import os
import json
import datetime
import tempfile
import traceback
from io import BytesIO
from functools import wraps
from flask import Flask, request, jsonify, send_from_directory, send_file
from flask_cors import CORS
from dotenv import load_dotenv
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

try:
    import jwt
except ImportError:
    jwt = None

HAS_PYJWT = bool(jwt and hasattr(jwt, "encode") and hasattr(jwt, "decode"))

load_dotenv()

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["TRANSFORMERS_VERBOSITY"] = "error"

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'docr-secret-key-2024')
CORS(app, resources={r"/api/*": {"origins": "*"}})

USERS_FILE = "users.json"
JSON_FOLDER = "final_output_json"
CROPS_FOLDER = "detected_fields"

FIELD_ALIASES = {
    "cheque_number": ("cheque_number", "Cheque_Number", "chequenumber"),
    "account_number": ("account_number", "Account_Number", "accountnumber"),
    "ifsc_code": ("ifsc_code", "IFSC_Code", "ifsccode", "ifsc"),
    "amount": ("amount", "Amount"),
    "date": ("date", "Date"),
    "payee_name": ("payee_name", "Payee_Name", "payeename"),
}

# ─── Model cache (loaded once at startup) ────────────────────────────────────

_model = None
_trocr_model = None
_processor = None
_device = None
_model_load_error = None

def get_models():
    global _model, _trocr_model, _processor, _device, _model_load_error
    if _model is not None:
        return _model, _trocr_model, _processor, _device
    if _model_load_error is not None:
        raise RuntimeError(_model_load_error)
    try:
        import main as ocr_main
        _model, _trocr_model, _processor, _device = ocr_main.initialize_models()
        print("✅ Models loaded and cached.")
        return _model, _trocr_model, _processor, _device
    except Exception as e:
        _model_load_error = str(e)
        raise RuntimeError(f"Failed to load models: {e}")

# ─── Auth helpers ─────────────────────────────────────────────────────────────

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE) as f:
            return json.load(f)
    # Create default users file
    default = {"admin": "admin"}
    save_users(default)
    return default

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)

def get_field(record, field):
    for key in FIELD_ALIASES[field]:
        value = record.get(key)
        if value not in (None, ""):
            return value
    return ""

def amount_number(value):
    try:
        clean = "".join(c for c in str(value) if c.isdigit() or c == ".")
        return float(clean) if clean else 0
    except Exception:
        return 0

def parse_date(value):
    if not value:
        return None
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%d %b %Y", "%d %B %Y"):
        try:
            return datetime.datetime.strptime(str(value).strip(), fmt).date()
        except ValueError:
            pass
    return None

def load_records():
    records = []
    if os.path.exists(JSON_FOLDER):
        for fname in sorted(os.listdir(JSON_FOLDER), reverse=True):
            if fname.endswith(".json"):
                try:
                    with open(os.path.join(JSON_FOLDER, fname), encoding="utf-8") as f:
                        d = json.load(f)
                    d["file"] = fname.replace(".json", "")
                    records.append(d)
                except Exception:
                    pass
    return records

def make_token(username):
    if HAS_PYJWT:
        payload = {
            "sub": username,
            "iat": datetime.datetime.utcnow(),
            "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=24),
        }
        return jwt.encode(payload, app.config['SECRET_KEY'], algorithm="HS256")
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    return serializer.dumps({"sub": username}, salt="docr-auth")

def require_auth(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return jsonify({"error": "Unauthorized"}), 401
        token = auth.split(" ", 1)[1]
        try:
            if HAS_PYJWT:
                data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            else:
                serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
                data = serializer.loads(token, salt="docr-auth", max_age=24 * 60 * 60)
            request.username = data["sub"]
        except (SignatureExpired, getattr(jwt, "ExpiredSignatureError", SignatureExpired) if jwt else SignatureExpired):
            return jsonify({"error": "Token expired"}), 401
        except (BadSignature, Exception):
            return jsonify({"error": "Invalid token"}), 401
        return f(*args, **kwargs)
    return wrapper

# ─── Auth routes ──────────────────────────────────────────────────────────────

@app.route("/api/auth/login", methods=["POST"])
def login():
    body = request.get_json(force=True)
    username = (body.get("username") or "").strip()
    password = (body.get("password") or "").strip()
    users = load_users()
    if username in users and users[username] == password:
        token = make_token(username)
        return jsonify({"token": token, "user": {"username": username}})
    return jsonify({"error": "Invalid username or password"}), 401

@app.route("/api/auth/register", methods=["POST"])
def register():
    body = request.get_json(force=True)
    username = (body.get("username") or "").strip()
    password = (body.get("password") or "").strip()
    if not username or not password:
        return jsonify({"error": "All fields required"}), 400
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400
    users = load_users()
    if username in users:
        return jsonify({"error": "Username already exists"}), 409
    users[username] = password
    save_users(users)
    return jsonify({"message": "Account created. Please sign in."})

# ─── Process route ────────────────────────────────────────────────────────────

@app.route("/api/process", methods=["POST"])
@require_auth
def process_document():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    original_name = file.filename
    base_name = os.path.splitext(original_name)[0]
    suffix = os.path.splitext(original_name)[1] or ".jpg"

    # Save uploaded file to a temp path
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False, prefix="docr_") as tmp:
        file.save(tmp.name)
        tmp_path = tmp.name

    # Also save to dataset/cheques with original filename for records
    dest_dir = os.path.join("dataset", "cheques")
    os.makedirs(dest_dir, exist_ok=True)
    import shutil
    dest_path = os.path.join(dest_dir, original_name)
    shutil.copy(tmp_path, dest_path)

    # Ensure output folders exist
    os.makedirs(JSON_FOLDER, exist_ok=True)
    os.makedirs(CROPS_FOLDER, exist_ok=True)
    os.makedirs("ocr_results", exist_ok=True)

    try:
        # Get cached models (loaded once, reused on every request)
        model, trocr_model, processor, device = get_models()

        import main as ocr_main
        success = ocr_main.run_pipeline(dest_path, model, trocr_model, processor, device)

        json_path = os.path.join(JSON_FOLDER, f"{base_name}.json")

        if os.path.exists(json_path):
            with open(json_path) as f:
                result = json.load(f)
            result["filename"] = base_name
            return jsonify({"success": True, "data": result})
        elif success:
            return jsonify({
                "success": True,
                "data": {"filename": base_name, "message": "Processed — no fields detected"}
            })
        else:
            return jsonify({"error": "Pipeline ran but produced no output"}), 500

    except RuntimeError as e:
        # Model load failure — try simple OCR fallback
        print(f"Model error: {e}, trying fallback OCR...")
        traceback.print_exc()
        try:
            result = _simple_ocr_fallback(tmp_path, original_name)
            return jsonify({"success": True, "data": result})
        except Exception as e2:
            traceback.print_exc()
            return jsonify({"error": f"Processing failed: {str(e)}"}), 500
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"Processing error: {str(e)}"}), 500
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass

def _simple_ocr_fallback(image_path, filename):
    """Fallback using Tesseract-based OCR if YOLO/TrOCR models fail."""
    from ocr.preprocess import preprocess_image
    from ocr.extract import extract_fields_enhanced, extract_text
    import cv2

    base_name = os.path.splitext(os.path.basename(filename))[0]
    img = cv2.imread(image_path)
    if img is None:
        from PIL import Image
        import numpy as np
        pil_img = Image.open(image_path)
        img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

    preprocessed = preprocess_image(img, doc_type="cheque", text_type="mixed")
    text = extract_text(preprocessed)
    fields = extract_fields_enhanced(text)

    result = {"filename": base_name}
    for field, info in fields.items():
        result[field] = info.get("value", "")

    # Save to JSON for records
    os.makedirs(JSON_FOLDER, exist_ok=True)
    json_path = os.path.join(JSON_FOLDER, f"{base_name}.json")
    with open(json_path, "w") as f:
        json.dump(result, f, indent=4)

    return result

# ─── Records routes ───────────────────────────────────────────────────────────

@app.route("/api/records", methods=["GET"])
@require_auth
def get_records():
    records = load_records()
    return jsonify({"records": records, "total": len(records)})

@app.route("/api/records/export/excel", methods=["GET"])
@require_auth
def export_records_excel():
    records = load_records()
    rows = []
    for record in records:
        rows.append({
            "File": record.get("file", ""),
            "Cheque No.": get_field(record, "cheque_number"),
            "Account No.": get_field(record, "account_number"),
            "IFSC": get_field(record, "ifsc_code"),
            "Amount": get_field(record, "amount"),
            "Date": get_field(record, "date"),
            "Payee": get_field(record, "payee_name"),
        })

    output = BytesIO()
    try:
        import pandas as pd
        df = pd.DataFrame(rows)
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="DocOCR Records")
    except Exception:
        import csv
        text = BytesIO()
        content = ""
        if rows:
            string_rows = []
            headers = list(rows[0].keys())
            string_rows.append(",".join(headers))
            for row in rows:
                string_rows.append(",".join(str(row.get(h, "")).replace(",", " ") for h in headers))
            content = "\n".join(string_rows)
        text.write(content.encode("utf-8"))
        text.seek(0)
        return send_file(
            text,
            mimetype="text/csv",
            as_attachment=True,
            download_name="DocOCR_Records.csv",
        )

    output.seek(0)
    return send_file(
        output,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        as_attachment=True,
        download_name="DocOCR_Records.xlsx",
    )

@app.route("/api/records/<name>", methods=["DELETE"])
@require_auth
def delete_record(name):
    path = os.path.join(JSON_FOLDER, f"{name}.json")
    if os.path.exists(path):
        os.remove(path)
        return jsonify({"message": "Deleted"})
    return jsonify({"error": "Not found"}), 404

@app.route("/api/records/<name>/image")
@require_auth
def get_record_image(name):
    for ext in [".jpg", ".jpeg", ".png", ".tif", ".tiff"]:
        p = os.path.join("dataset", "cheques", name + ext)
        if os.path.exists(p):
            return send_from_directory(os.path.dirname(p), os.path.basename(p))
    return jsonify({"error": "Image not found"}), 404

# ─── Analytics route ──────────────────────────────────────────────────────────

@app.route("/api/analytics", methods=["GET"])
@require_auth
def get_analytics():
    records = load_records()
    total = len(records)
    normalized = []
    amounts = [amount_number(get_field(r, "amount")) for r in records]
    nonzero_amounts = [a for a in amounts if a > 0]

    for record in records:
        amount = amount_number(get_field(record, "amount"))
        date_value = parse_date(get_field(record, "date"))
        normalized.append({
            "file": record.get("file", ""),
            "cheque_number": get_field(record, "cheque_number"),
            "account_number": get_field(record, "account_number"),
            "ifsc_code": get_field(record, "ifsc_code"),
            "amount": get_field(record, "amount"),
            "amount_num": amount,
            "date": get_field(record, "date"),
            "date_iso": date_value.isoformat() if date_value else "",
            "payee_name": get_field(record, "payee_name"),
        })

    fields_found = {
        field: sum(1 for r in records if get_field(r, field))
        for field in FIELD_ALIASES
    }

    distribution_bins = [
        ("0-1k", 0, 1000),
        ("1k-5k", 1000, 5000),
        ("5k-10k", 5000, 10000),
        ("10k-50k", 10000, 50000),
        ("50k+", 50000, None),
    ]
    amount_distribution = []
    for label, low, high in distribution_bins:
        count = sum(1 for amount in nonzero_amounts if amount >= low and (high is None or amount < high))
        amount_distribution.append({"range": label, "count": count})

    by_date = {}
    for row in normalized:
        if row["date_iso"]:
            by_date[row["date_iso"]] = by_date.get(row["date_iso"], 0) + row["amount_num"]
    trend = [{"date": key, "amount": value} for key, value in sorted(by_date.items())]

    by_payee = {}
    for row in normalized:
        payee = row["payee_name"] or "Unknown"
        by_payee[payee] = by_payee.get(payee, 0) + row["amount_num"]
    payee_breakdown = [
        {"payee": payee, "amount": amount}
        for payee, amount in sorted(by_payee.items(), key=lambda item: item[1], reverse=True)[:10]
    ]

    return jsonify({
        "total_documents": total,
        "total_amount": sum(nonzero_amounts),
        "avg_amount": sum(nonzero_amounts) / len(nonzero_amounts) if nonzero_amounts else 0,
        "max_amount": max(nonzero_amounts) if nonzero_amounts else 0,
        "fields_found": fields_found,
        "amount_distribution": amount_distribution,
        "trend": trend,
        "payee_breakdown": payee_breakdown,
        "records": normalized,
    })

# ─── Chatbot route ────────────────────────────────────────────────────────────

@app.route("/api/chat", methods=["POST"])
@require_auth
def chat():
    body = request.get_json(force=True)
    query = (body.get("message") or "").strip()
    if not query:
        return jsonify({"error": "No message provided"}), 400
    records = load_records()

    if not records:
        return jsonify({
            "reply": "No cheque records available yet."
        })
        
        
    # ✅ NEW — DIRECT PYTHON ANALYTICS
    # Much faster + more stable than asking LLM everything

    try:

        # ---- Total cheque count ----
        if "how many" in query and "cheque" in query:
            return jsonify({
                "reply": f"A total of {len(records)} cheques have been processed."
            })

        # ---- Total amount ----
        elif "total amount" in query:

            total_amount = sum(
                amount_number(get_field(r, "amount"))
                for r in records
            )

            return jsonify({
                "reply": f"Total amount across all cheques: ₹{total_amount:,.0f}"
            })

        # ---- Average amount ----
        elif "average" in query and "amount" in query:

            amounts = [
                amount_number(get_field(r, "amount"))
                for r in records
                if amount_number(get_field(r, "amount")) > 0
            ]

            avg_amount = sum(amounts) / len(amounts) if amounts else 0

            return jsonify({
                "reply": f"Average cheque amount: ₹{avg_amount:,.2f}"
            })

        # ---- Highest amount cheque ----
        elif "highest" in query or "largest" in query:

            valid_records = [
                r for r in records
                if amount_number(get_field(r, "amount")) > 0
            ]

            if valid_records:

                highest = max(
                    valid_records,
                    key=lambda r: amount_number(get_field(r, "amount"))
                )

                payee = get_field(highest, "payee_name")
                amount = amount_number(get_field(highest, "amount"))
                cheque = get_field(highest, "cheque_number")
                date = get_field(highest, "date")

                return jsonify({
                    "reply":
                        f"Highest cheque amount:\n\n"
                        f"Payee: {payee}\n"
                        f"Amount: ₹{amount:,.0f}\n"
                        f"Cheque Number: {cheque}\n"
                        f"Date: {date}"
                })

        # ---- IFSC Codes ----
        elif "ifsc" in query:

            ifsc_codes = set()

            for r in records:

                code = str(get_field(r, "ifsc_code")).strip()

                # ✅ NEW — CLEANUP
                code = code.replace(".", "")
                code = code.upper()

                if len(code) >= 11:
                    code = code[:11]

                if code:
                    ifsc_codes.add(code)

            if not ifsc_codes:
                return jsonify({
                    "reply": "No IFSC codes found."
                })

            formatted = "\n".join(
                [f"{i+1}. {code}" for i, code in enumerate(sorted(ifsc_codes))]
            )

            return jsonify({
                "reply": f"IFSC codes found:\n\n{formatted}"
            })

    except Exception as e:
        traceback.print_exc()
        
    api_key = os.getenv("GROQ_API_KEY")
    
    if not api_key:
        return jsonify({
            "reply": "The chatbot is not configured yet. Please add a GROQ_API_KEY to enable AI chat."
        })

    records = []
    if os.path.exists(JSON_FOLDER):
        for fname in sorted(os.listdir(JSON_FOLDER)):
            if fname.endswith(".json"):
                try:
                    with open(os.path.join(JSON_FOLDER, fname)) as f:
                        d = json.load(f)
                    d["file"] = fname.replace(".json", "")
                    records.append(d)
                except Exception:
                    pass

    try:
        from groq import Groq
        client = Groq(api_key=api_key)
        
        summary = []

        for r in records[:20]:

            summary.append(
                f"""
Cheque:
- Cheque Number: {get_field(r, "cheque_number")}
- Account Number: {get_field(r, "account_number")}
- IFSC Code: {get_field(r, "ifsc_code")}
- Amount: {get_field(r, "amount")}
- Date: {get_field(r, "date")}
- Payee Name: {get_field(r, "payee_name")}
"""
            )

        context = "\n".join(summary)
        
        prompt = f"""You are a smart financial assistant for DocOCR, an AI-powered cheque processing system.

You have access to the following extracted cheque data:
{context}

Answer the user's question clearly and concisely. If they make spelling mistakes, still understand their intent.
Be helpful and precise about financial data. Format numbers and amounts nicely.

User: {query}"""

        completion = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=700,
        )
        reply = completion.choices[0].message.content
        # fallback handling
        if not reply or not str(reply).strip():
            reply = "I couldn't generate a response. Please try again."
        return jsonify({"reply": reply})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"Chat failed: {str(e)}"}), 500

# ─── Health ───────────────────────────────────────────────────────────────────

@app.route("/api/health")
def health():
    model_status = "loaded" if _model is not None else ("error" if _model_load_error else "not_loaded")
    return jsonify({
        "status": "ok",
        "service": "DocOCR API",
        "model": model_status
    })

# ─── Startup ──────────────────────────────────────────────────────────────────

def startup():
    """Initialize resources on startup."""
    # Ensure users.json exists with default admin account
    load_users()
    print("✅ Users file ready.")

    # Pre-load models in background so first request is fast
    import threading
    def _load():
        try:
            get_models()
        except Exception as e:
            print(f"⚠️  Model preload failed: {e}")
    threading.Thread(target=_load, daemon=True).start()
    print("🔄 Model preload started in background...")

if __name__ == "__main__":
    startup()
    app.run(host="0.0.0.0", port=8000, debug=False)

