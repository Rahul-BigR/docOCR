import warnings
warnings.filterwarnings("ignore")

import logging
logging.getLogger("transformers").setLevel(logging.ERROR)
logging.getLogger("ultralytics").setLevel(logging.ERROR)

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import time
import main
from streamlit_option_menu import option_menu
from io import BytesIO
import os
import tempfile
import json
import cv2
from PIL import Image
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
os.environ["TRANSFORMERS_VERBOSITY"] = "error"

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    st.error("API key missing. Add GROQ_API_KEY in .env")
    st.stop()

client = Groq(api_key=api_key)

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="DocOCR – Financial Document Analyzer",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
# GLOBAL CSS  –  bigger text, roomier layout
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap');

/* ── Root reset ── */
html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 16px !important;
}

/* ── Hide Streamlit chrome ── */
#MainMenu, footer { visibility: hidden; }
header { visibility: visible !important; }
.block-container {
    padding-top: 2rem !important;
    padding-bottom: 2.5rem !important;
    max-width: 1400px !important;
}

/* ── Sidebar ── */
/* ── Sidebar (FIXED FINAL) ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0a0f1e 0%, #111827 100%) !important;
    border-right: 1px solid #1e2d45;
}

/* Sidebar text */
[data-testid="stSidebar"] * {
    color: #e2e8f0 !important;
}

/* Ensure toggle button is visible */
[data-testid="collapsedControl"] {
    display: block !important;
    color: #818cf8 !important;
}


[data-testid="collapsedControl"] {
    display: block !important;
    color: #818cf8 !important;
}


/* ── Cards ── */
.docr-card {
    background: #111827;
    border: 1px solid #1e2d45;
    border-radius: 16px;
    padding: 1.75rem;
    margin-bottom: 1.25rem;
}

/* ── Metric cards ── */
.metric-row { display: flex; gap: 1.25rem; margin-bottom: 2rem; flex-wrap: wrap; }
.metric-card {
    flex: 1; min-width: 170px;
    background: #111827;
    border: 1px solid #1e2d45;
    border-radius: 16px;
    padding: 1.5rem 1.75rem;
    position: relative; overflow: hidden;
}
.metric-card::before {
    content: '';
    position: absolute; top: 0; left: 0;
    width: 5px; height: 100%;
    border-radius: 16px 0 0 16px;
}
.metric-card.indigo::before { background: linear-gradient(180deg,#6366f1,#4f46e5); }
.metric-card.green::before  { background: linear-gradient(180deg,#22c55e,#16a34a); }
.metric-card.amber::before  { background: linear-gradient(180deg,#f59e0b,#d97706); }
.metric-card.rose::before   { background: linear-gradient(180deg,#f43f5e,#e11d48); }
.metric-label {
    font-size: 0.8rem; font-weight: 600; color: #64748b;
    letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 0.5rem;
}
.metric-value {
    font-size: 2.1rem; font-weight: 800; color: #f1f5f9;
    line-height: 1.1; font-family: 'DM Sans', sans-serif;
}
.metric-sub { font-size: 0.82rem; color: #4b5563; margin-top: 0.3rem; }

/* ── Page / hero ── */
.hero-bar {
    background: linear-gradient(135deg, #111827 0%, #1a1040 100%);
    border: 1px solid #1e2d45; border-radius: 18px;
    padding: 1.75rem 2.25rem; margin-bottom: 2rem;
    display: flex; align-items: center; justify-content: space-between;
}
.hero-text h1 {
    font-size: 1.75rem; font-weight: 800; color: #f1f5f9;
    margin: 0; letter-spacing: -0.03em;
}
.hero-text p { font-size: 0.95rem; color: #6b7280; margin: 0.3rem 0 0 0; }

/* ── Divider ── */
.divider { border: none; border-top: 1px solid #1e2d45; margin: 1.25rem 0; }

/* ── Badge ── */
.badge {
    display: inline-block; padding: 0.3rem 0.8rem;
    border-radius: 999px; font-size: 0.78rem; font-weight: 700;
    letter-spacing: 0.04em;
}
.badge-green  { background: rgba(34,197,94,0.12);  color: #4ade80; border: 1px solid rgba(34,197,94,0.2); }
.badge-indigo { background: rgba(99,102,241,0.12); color: #818cf8; border: 1px solid rgba(99,102,241,0.2); }
.badge-amber  { background: rgba(245,158,11,0.12); color: #fbbf24; border: 1px solid rgba(245,158,11,0.2); }

/* ── Result grid ── */
.result-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
.result-item {
    background: #0d1520; border: 1px solid #1e2d45;
    border-radius: 12px; padding: 1rem 1.25rem;
}
.result-field {
    font-size: 0.75rem; font-weight: 700; color: #4b5563;
    text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 0.3rem;
}
.result-val {
    font-size: 1.15rem; font-weight: 700; color: #e2e8f0;
    font-family: 'JetBrains Mono', monospace;
}

/* ── Upload zone ── */
[data-testid="stFileUploader"] {
    background: #111827 !important;
    border: 2px dashed #1e2d45 !important;
    border-radius: 16px !important;
    padding: 1.25rem !important;
}
[data-testid="stFileUploader"]:hover { border-color: #4f46e5 !important; }
[data-testid="stFileUploader"] label { font-size: 1rem !important; }

/* ── Buttons ── */
.stButton > button {
    background: linear-gradient(135deg, #4f46e5, #7c3aed) !important;
    color: white !important;
    border: none !important; border-radius: 10px !important;
    font-weight: 700 !important; font-size: 1rem !important;
    letter-spacing: 0.02em !important;
    padding: 0.7rem 1.5rem !important;
    transition: all 0.2s !important;
    box-shadow: 0 4px 15px rgba(79,70,229,0.3) !important;
}
.stButton > button:hover {
    opacity: 0.9 !important;
    box-shadow: 0 6px 20px rgba(79,70,229,0.45) !important;
    transform: translateY(-1px) !important;
}

/* ── Inputs ── */
.stTextInput > div > div > input {
    background: #111827 !important; color: #e2e8f0 !important;
    border-color: #1e2d45 !important; border-radius: 10px !important;
    font-size: 1rem !important; padding: 0.6rem 0.9rem !important;
}
.stTextInput > label {
    color: #94a3b8 !important; font-size: 0.9rem !important;
    font-weight: 600 !important;
}

/* ── Dataframe ── */
[data-testid="stDataFrame"] { border-radius: 14px !important; overflow: hidden; }
[data-testid="stDataFrame"] * { font-size: 0.95rem !important; }

/* ── Tabs ── */
[data-baseweb="tab-list"] {
    gap: 0.5rem; background: transparent !important;
    border-bottom: 1px solid #1e2d45 !important;
}
[data-baseweb="tab"] {
    background: transparent !important; border-radius: 10px 10px 0 0 !important;
    color: #6b7280 !important; font-weight: 600 !important;
    font-size: 0.95rem !important; padding: 0.7rem 1.25rem !important;
}
[aria-selected="true"][data-baseweb="tab"] {
    background: #111827 !important; color: #818cf8 !important;
    border-bottom: 3px solid #4f46e5 !important;
}

/* ── Alerts ── */
[data-testid="stAlert"] { border-radius: 12px !important; font-size: 0.95rem !important; }

/* ── Sidebar brand ── */
.sidebar-brand {
    padding: 1.75rem 1rem 1.25rem 1rem;
    border-bottom: 1px solid #1e2d45;
    margin-bottom: 1rem;
}
.sidebar-logo {
    font-size: 1.7rem; font-weight: 900; color: #818cf8 !important;
    letter-spacing: -0.05em;
}
.sidebar-tagline { font-size: 0.8rem; color: #374151 !important; margin-top: 0.15rem; }

/* ── Table ── */
thead tr th {
    background: #111827 !important; color: #94a3b8 !important;
    font-size: 0.9rem !important; font-weight: 700 !important;
}

/* ── Spinner ── */
[data-testid="stSpinner"] p { color: #94a3b8 !important; font-size: 1rem !important; }

/* ── Form labels ── */
label { color: #94a3b8 !important; font-size: 0.9rem !important; font-weight: 600 !important; }

/* ── Auth cards ── */
.auth-card {
    max-width: 460px; margin: 2.5rem auto;
    background: #111827; border: 1px solid #1e2d45;
    border-radius: 20px; padding: 2.75rem;
}
.auth-title { font-size: 1.6rem; font-weight: 800; color: #f1f5f9; margin-bottom: 0.4rem; }
.auth-sub   { font-size: 0.9rem; color: #6b7280; margin-bottom: 2rem; }

/* ── Section labels ── */
.section-label {
    font-size: 0.82rem; font-weight: 700; color: #6b7280;
    text-transform: uppercase; letter-spacing: 0.09em; margin-bottom: 0.75rem;
}

/* ── Download btn ── */
[data-testid="stDownloadButton"] > button {
    background: #111827 !important;
    border: 1px solid #1e2d45 !important;
    color: #94a3b8 !important;
    font-size: 0.95rem !important;
    box-shadow: none !important;
}
[data-testid="stDownloadButton"] > button:hover {
    border-color: #4f46e5 !important;
    color: #818cf8 !important;
    transform: none !important;
    box-shadow: none !important;
}

/* ── Info banner for current session record ── */
.session-banner {
    background: rgba(99,102,241,0.08);
    border: 1px solid rgba(99,102,241,0.25);
    border-radius: 12px;
    padding: 0.85rem 1.25rem;
    margin-bottom: 1rem;
    font-size: 0.9rem;
    color: #a5b4fc;
    display: flex; align-items: center; gap: 0.6rem;
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# MODELS (cached)
# ─────────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def load_models():
    model, trocr_model, processor, DEVICE = main.initialize_models()
    return model, trocr_model, processor, DEVICE


# ─────────────────────────────────────────────
# AUTH HELPERS
# ─────────────────────────────────────────────
USERS_FILE = "users.json"

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    return {"admin": "admin"}

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)


# ─────────────────────────────────────────────
# HELPER: load all JSON records from disk
# ALSO merges the current session result so the
# just-processed cheque always appears in lists.
# ─────────────────────────────────────────────
def load_all_records():
    """
    Reads every .json from final_output_json/ and returns them as a list of dicts.
    The current session's last_result is guaranteed to be included (de-duplicated
    by the 'file' key derived from the json filename).
    """
    folder = "final_output_json"
    records = []
    seen_files = set()

    if os.path.exists(folder):
        for fname in sorted(os.listdir(folder)):
            if fname.endswith(".json"):
                fpath = os.path.join(folder, fname)
                try:
                    with open(fpath, encoding="utf-8") as fh:
                        d = json.load(fh)
                    d["file"] = fname.replace(".json", "")
                    records.append(d)
                    seen_files.add(d["file"])
                except Exception:
                    pass

    # If the current session has a result that somehow didn't make it to disk yet,
    # inject it at the top so it always appears.
    last = st.session_state.get("last_result")
    last_filename = st.session_state.get("last_result_filename")
    if last and last_filename and last_filename not in seen_files:
        injected = dict(last)
        injected["file"] = last_filename
        records.insert(0, injected)

    return records

def chatbot_response(query, df):
    import json

    data = df.to_dict(orient="records")

    prompt = f"""
    You are a smart financial assistant.

    You have cheque data:
    {json.dumps(data)}

    Answer user questions clearly.
    If user makes spelling mistakes, still understand.
    Give short and accurate answers.

    User question: {query}
    """

    completion = client.chat.completions.create(
        model="openai/gpt-oss-120b",   # ✅ latest working model
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.5
    )

    return completion.choices[0].message.content



# ─────────────────────────────────────────────
# SESSION STATE INIT
# ─────────────────────────────────────────────
for key, default in [
    ("users", None),
    ("logged_in", False),
    ("username", None),
    ("last_result", None),
    ("last_result_filename", None),
    ("processing", False),
    ("chat_history", []),
]:
    if key not in st.session_state:
        st.session_state[key] = default

if st.session_state.users is None:
    st.session_state.users = load_users()


# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div class="sidebar-brand">
        <div class="sidebar-logo">⬡ DocOCR</div>
        <div class="sidebar-tagline">Financial Document Intelligence</div>
    </div>
    """, unsafe_allow_html=True)

    NAV_STYLES = {
        "container": {"background-color": "transparent", "padding": "0"},
        "icon": {"color": "#818cf8", "font-size": "17px"},
        "nav-link": {
            "font-size": "15px", "color": "#94a3b8",
            "border-radius": "10px", "margin": "3px 0",
            "padding": "0.65rem 1rem",
            "--hover-color": "rgba(99,102,241,0.12)",
        },
        "nav-link-selected": {"background-color": "#4f46e5", "color": "white"},
    }

    if not st.session_state.logged_in:
        selected = option_menu(
            menu_title=None,
            options=["Login", "Register"],
            icons=["box-arrow-in-right", "person-plus"],
            default_index=0,
            styles=NAV_STYLES,
        )
    else:
        selected = option_menu(
            menu_title=None,
            options=["Analyzer", "All Records", "Analytics" , "Chatbot"],
            icons=["file-earmark-text", "table", "bar-chart-line"],
            default_index=0,
            styles=NAV_STYLES,
        )

        st.markdown("<hr class='divider'>", unsafe_allow_html=True)
        st.markdown(f"""
        <div style='padding: 0 0.5rem;'>
            <div style='font-size:0.75rem; color:#374151; text-transform:uppercase;
                        letter-spacing:0.08em; margin-bottom:0.4rem;'>Signed in as</div>
            <div style='font-size:1rem; font-weight:700; color:#c7d2fe;'>
                👤 {st.session_state.username}
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
        if st.button("Sign out", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.username = None
            st.session_state.last_result = None
            st.session_state.last_result_filename = None
            st.rerun()

    st.markdown("""
    <div style='position:absolute; bottom:1.5rem; left:1rem; right:1rem;
                font-size:0.75rem; color:#1e2d45; text-align:center;'>
        DocOCR &nbsp;·&nbsp; AI-Powered OCR Platform
    </div>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# HELPER: formatted result card
# ─────────────────────────────────────────────
FIELD_META = {
    "cheque_number":  ("Cheque Number",  "🔢"),
    "account_number": ("Account Number", "🏦"),
    "ifsc_code":      ("IFSC Code",      "🔤"),
    "amount":         ("Amount (₹)",     "💰"),
    "date":           ("Date",           "📅"),
    "payee_name":     ("Payee Name",     "👤"),
}

def render_result_card(data: dict):
    items_html = ""
    for key, (label, icon) in FIELD_META.items():
        val = data.get(key, data.get(key.replace("_", ""), "—")) or "—"
        items_html += f"""
        <div class="result-item">
            <div class="result-field">{icon} {label}</div>
            <div class="result-val">{val}</div>
        </div>"""

    st.markdown(f"""
    <div class="docr-card">
        <div style="display:flex; align-items:center; justify-content:space-between;
                    margin-bottom:1.25rem;">
            <span style="font-size:1.15rem; font-weight:800; color:#e2e8f0;">
                Extracted Fields
            </span>
            <span class="badge badge-green">✓ OCR Complete</span>
        </div>
        <div class="result-grid">{items_html}</div>
    </div>
    """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════
# PAGE — LOGIN
# ═══════════════════════════════════════════════
if not st.session_state.logged_in and selected == "Login":

    col_c = st.columns([1, 2, 1])[1]
    with col_c:
        st.markdown("""
        <div style="text-align:center; margin-bottom:2.5rem; margin-top:2rem;">
            <div style="font-size:3rem; font-weight:900; color:#818cf8;
                        letter-spacing:-0.05em;">⬡ DocOCR</div>
            <div style="font-size:1rem; color:#6b7280; margin-top:0.45rem;">
                AI-Powered Financial Document Analyzer
            </div>
        </div>
        """, unsafe_allow_html=True)

        with st.form("login_form"):
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            st.markdown("<div style='height:0.75rem'></div>", unsafe_allow_html=True)
            login_btn = st.form_submit_button("Sign In →", use_container_width=True)

            if login_btn:
                if username in st.session_state.users and \
                   st.session_state.users[username] == password:
                    st.session_state.logged_in = True
                    st.session_state.username = username
                    st.rerun()
                else:
                    st.error("❌  Invalid username or password.")

        st.markdown("""
        <div style="text-align:center; font-size:0.9rem; color:#4b5563; margin-top:1.25rem;">
            No account? Select <b style='color:#818cf8'>Register</b> in the sidebar.
        </div>
        """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════
# PAGE — REGISTER
# ═══════════════════════════════════════════════
elif not st.session_state.logged_in and selected == "Register":

    col_c = st.columns([1, 2, 1])[1]
    with col_c:
        st.markdown("""
        <div style="text-align:center; margin-bottom:2.5rem; margin-top:2rem;">
            <div style="font-size:3rem; font-weight:900; color:#818cf8;
                        letter-spacing:-0.05em;">⬡ DocOCR</div>
            <div style="font-size:1rem; color:#6b7280; margin-top:0.35rem;">
                Create your account
            </div>
        </div>
        """, unsafe_allow_html=True)

        with st.form("register_form", clear_on_submit=True):
            username = st.text_input("Choose a username", placeholder="e.g. john.doe")
            password = st.text_input("Choose a password", type="password",
                                     placeholder="Min. 6 characters")
            st.markdown("<div style='height:0.75rem'></div>", unsafe_allow_html=True)
            reg_btn = st.form_submit_button("Create Account →", use_container_width=True)

            if reg_btn:
                if not username or not password:
                    st.error("Please fill in all fields.")
                elif len(password) < 6:
                    st.warning("Password must be at least 6 characters.")
                elif username in st.session_state.users:
                    st.warning("Username already exists. Try another.")
                else:
                    st.session_state.users[username] = password
                    save_users(st.session_state.users)
                    st.success("✅  Account created! Please sign in.")
                    time.sleep(1)
                    st.rerun()


# ═══════════════════════════════════════════════
# PAGE — ANALYZER
# ═══════════════════════════════════════════════
elif st.session_state.logged_in and selected == "Analyzer":

    st.markdown("""
    <div class="hero-bar">
        <div class="hero-text">
            <h1>Cheque Analyzer</h1>
            <p>Upload a cheque image and extract all key fields instantly using AI.</p>
        </div>
        <span class="badge badge-indigo">YOLO + TrOCR Engine</span>
    </div>
    """, unsafe_allow_html=True)

    col_left, col_right = st.columns([1, 1], gap="large")

    # ── Left: upload ──
    with col_left:
        st.markdown('<div class="section-label">📤 Upload Document</div>',
                    unsafe_allow_html=True)

        uploaded_file = st.file_uploader(
            "Upload cheque", 
            type=["jpg", "jpeg", "png"],
            label_visibility="collapsed",
        )

        if uploaded_file:
            st.image(uploaded_file, use_container_width=True,
                     caption=f"📎 {uploaded_file.name}")
            st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
            process_btn = st.button("⚡ Run OCR Analysis", use_container_width=True)

            if process_btn:
                with st.spinner("Analyzing document with YOLO + TrOCR…"):
                    temp_dir = tempfile.mkdtemp()
                    image_path = os.path.join(temp_dir, uploaded_file.name)
                    img = Image.open(uploaded_file)
                    img.save(image_path)

                    try:
                        model, trocr_model, processor, DEVICE = load_models()
                        success = main.run_pipeline(
                            image_path, model, trocr_model, processor, DEVICE
                        )
                        if success:
                            stem = os.path.splitext(os.path.basename(image_path))[0]
                            json_path = os.path.join("final_output_json", stem + ".json")
                            if os.path.exists(json_path):
                                with open(json_path, encoding="utf-8") as fh:
                                    result = json.load(fh)
                                st.session_state.last_result = result
                                # Store the filename so All Records can find it
                                st.session_state.last_result_filename = stem
                            else:
                                st.warning("⚠️ Processing done but output file not found.")
                        else:
                            st.error("❌ OCR pipeline returned an error.")
                    except Exception as e:
                        st.error(f"❌ Error: {e}")

    # ── Right: results ──
    with col_right:
        st.markdown('<div class="section-label">📋 Extracted Data</div>',
                    unsafe_allow_html=True)

        if st.session_state.last_result:
            render_result_card(st.session_state.last_result)

            # JSON download
            json_bytes = json.dumps(st.session_state.last_result, indent=4).encode()
            st.download_button(
                "⬇ Download JSON",
                data=json_bytes,
                file_name="cheque_data.json",
                mime="application/json",
                use_container_width=True,
            )

            st.markdown("""
            <div style="font-size:0.85rem; color:#4b5563; margin-top:0.75rem; text-align:center;">
                This result is also saved and visible in <b style='color:#818cf8'>All Records</b>.
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="docr-card" style="text-align:center; padding:3.5rem 1.5rem;">
                <div style="font-size:3rem; margin-bottom:1rem;">📄</div>
                <div style="color:#4b5563; font-size:1rem; line-height:1.6;">
                    Upload a cheque image on the left<br>and click
                    <b style="color:#818cf8">Run OCR Analysis</b><br>to see results here.
                </div>
            </div>
            """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════
# PAGE — ALL RECORDS
# ═══════════════════════════════════════════════
elif st.session_state.logged_in and selected == "All Records":

    st.markdown("""
    <div class="hero-bar">
        <div class="hero-text">
            <h1>All Processed Records</h1>
            <p>Browse, search, and export every cheque that has been analyzed.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Show a banner if the current session has a freshly processed cheque
    if st.session_state.last_result and st.session_state.last_result_filename:
        st.markdown(f"""
        <div class="session-banner">
            ✅ &nbsp; Current session result —
            <b>{st.session_state.last_result_filename}</b> — is included below.
        </div>
        """, unsafe_allow_html=True)

    records = load_all_records()

    if not records:
        st.markdown("""
        <div class="docr-card" style="text-align:center; padding:3.5rem;">
            <div style="font-size:3rem; margin-bottom:1rem;">📂</div>
            <div style="color:#4b5563; font-size:1rem;">
                No records yet. Analyze a cheque in the
                <b style="color:#818cf8">Analyzer</b> tab.
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        df = pd.DataFrame(records)
        df["amount_num"] = pd.to_numeric(
            df.get("amount", pd.Series()), errors="coerce"
        ).fillna(0)

        total     = len(df)
        total_amt = df["amount_num"].sum()
        avg_amt   = df["amount_num"].mean()

        # ── Metrics ──
        m1, m2, m3 = st.columns(3)
        with m1:
            st.markdown(f"""
            <div class="metric-card indigo">
                <div class="metric-label">Total Records</div>
                <div class="metric-value">{total}</div>
                <div class="metric-sub">cheques processed</div>
            </div>""", unsafe_allow_html=True)
        with m2:
            st.markdown(f"""
            <div class="metric-card green">
                <div class="metric-label">Total Amount</div>
                <div class="metric-value">₹{total_amt:,.0f}</div>
                <div class="metric-sub">across all cheques</div>
            </div>""", unsafe_allow_html=True)
        with m3:
            st.markdown(f"""
            <div class="metric-card amber">
                <div class="metric-label">Average Amount</div>
                <div class="metric-value">₹{avg_amt:,.0f}</div>
                <div class="metric-sub">per cheque</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

        # ── Search + table ──
        search = st.text_input(
            "🔍 Search records",
            placeholder="Filter by payee, IFSC, cheque number, account number…"
        )
        display_df = df.copy()
        if search:
            mask = display_df.astype(str).apply(
                lambda col: col.str.contains(search, case=False, na=False)
            ).any(axis=1)
            display_df = display_df[mask]

        COLS_ORDER = [
            c for c in
            ["file", "cheque_number", "account_number", "ifsc_code",
             "amount", "date", "payee_name"]
            if c in display_df.columns
        ]
        COL_LABELS = {
            "file": "File",
            "cheque_number": "Cheque No.",
            "account_number": "Account No.",
            "ifsc_code": "IFSC",
            "amount": "Amount (₹)",
            "date": "Date",
            "payee_name": "Payee",
        }

        st.dataframe(
            display_df[COLS_ORDER].rename(columns=COL_LABELS),
            use_container_width=True,
            hide_index=True,
        )

        # ── Export ──
        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
        output = BytesIO()
        df[COLS_ORDER].rename(columns=COL_LABELS).to_excel(output, index=False)
        st.download_button(
            "⬇ Export All Records to Excel",
            data=output.getvalue(),
            file_name="DocOCR_Records.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )


# ═══════════════════════════════════════════════
# PAGE — ANALYTICS
# ═══════════════════════════════════════════════
elif st.session_state.logged_in and selected == "Analytics":

    st.markdown("""
    <div class="hero-bar">
        <div class="hero-text">
            <h1>Analytics Overview</h1>
            <p>Visualize trends, distributions, and insights from all processed cheques.</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    records = load_all_records()

    if not records:
        st.markdown("""
        <div class="docr-card" style="text-align:center; padding:3.5rem;">
            <div style="font-size:3rem; margin-bottom:1rem;">📊</div>
            <div style="color:#4b5563; font-size:1rem;">
                No data yet. Analyze some cheques first.
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        df = pd.DataFrame(records)
        df["amount_num"] = pd.to_numeric(
            df.get("amount", pd.Series()), errors="coerce"
        ).fillna(0)
        df["date_parsed"] = pd.to_datetime(
            df.get("date", pd.Series()), dayfirst=True, errors="coerce"
        )

        total     = len(df)
        total_amt = df["amount_num"].sum()
        avg_amt   = df["amount_num"].mean()
        max_amt   = df["amount_num"].max()
        latest    = df["date_parsed"].max()

        # ── Metrics ──
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(f"""<div class="metric-card indigo">
                <div class="metric-label">Cheques</div>
                <div class="metric-value">{total}</div>
                <div class="metric-sub">total processed</div>
            </div>""", unsafe_allow_html=True)
        with c2:
            st.markdown(f"""<div class="metric-card green">
                <div class="metric-label">Total Value</div>
                <div class="metric-value">₹{total_amt:,.0f}</div>
                <div class="metric-sub">combined amount</div>
            </div>""", unsafe_allow_html=True)
        with c3:
            st.markdown(f"""<div class="metric-card amber">
                <div class="metric-label">Average</div>
                <div class="metric-value">₹{avg_amt:,.0f}</div>
                <div class="metric-sub">per cheque</div>
            </div>""", unsafe_allow_html=True)
        with c4:
            latest_str = latest.strftime("%d %b %Y") if pd.notna(latest) else "N/A"
            st.markdown(f"""<div class="metric-card rose">
                <div class="metric-label">Latest Date</div>
                <div class="metric-value" style="font-size:1.4rem;">{latest_str}</div>
                <div class="metric-sub">most recent cheque</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<div style='height:1.25rem'></div>", unsafe_allow_html=True)

        PLOTLY_THEME = dict(
            paper_bgcolor="#111827",
            plot_bgcolor="#0d1520",
            font_color="#94a3b8",
            font_family="DM Sans",
            font_size=14,
            title_font_color="#e2e8f0",
            title_font_size=16,
            xaxis=dict(gridcolor="#1e2d45", zerolinecolor="#1e2d45"),
            yaxis=dict(gridcolor="#1e2d45", zerolinecolor="#1e2d45"),
            margin=dict(l=20, r=20, t=50, b=20),
        )

        tab1, tab2, tab3 = st.tabs([
            "📊 Amount Distribution",
            "📈 Temporal Trend",
            "👥 Payee Breakdown",
        ])

        # ─ Tab 1 ─
        with tab1:
            c_a, c_b = st.columns(2, gap="large")
            with c_a:
                fig = px.histogram(
                    df, x="amount_num", nbins=12,
                    title="Amount Distribution",
                    labels={"amount_num": "Amount (₹)"},
                    color_discrete_sequence=["#6366f1"],
                )
                fig.update_layout(**PLOTLY_THEME)
                st.plotly_chart(fig, use_container_width=True)
            with c_b:
                fig2 = px.box(
                    df, y="amount_num", points="all",
                    title="Amount Box Plot",
                    labels={"amount_num": "Amount (₹)"},
                    color_discrete_sequence=["#818cf8"],
                )
                fig2.update_layout(**PLOTLY_THEME)
                st.plotly_chart(fig2, use_container_width=True)

        # ─ Tab 2 ─
        with tab2:
            if df["date_parsed"].notna().any():
                df_sorted = df.dropna(subset=["date_parsed"]).sort_values("date_parsed")
                fig3 = px.area(
                    df_sorted, x="date_parsed", y="amount_num",
                    title="Amount Over Time",
                    labels={"date_parsed": "Date", "amount_num": "Amount (₹)"},
                    color_discrete_sequence=["#6366f1"],
                )
                fig3.update_traces(
                    fill="tozeroy", line_color="#818cf8",
                    fillcolor="rgba(99,102,241,0.12)"
                )
                fig3.update_layout(**PLOTLY_THEME)
                st.plotly_chart(fig3, use_container_width=True)
            else:
                st.info("No valid date data available for trend analysis.")

        # ─ Tab 3 ─
        with tab3:
            if "payee_name" in df.columns and df["payee_name"].notna().any():
                payee_df = (
                    df.groupby("payee_name", as_index=False)["amount_num"].sum()
                      .sort_values("amount_num", ascending=False)
                      .head(15)
                )
                fig4 = px.bar(
                    payee_df, x="amount_num", y="payee_name",
                    orientation="h",
                    title="Top Payees by Total Amount",
                    labels={"amount_num": "Amount (₹)", "payee_name": "Payee"},
                    color_discrete_sequence=["#6366f1"],
                )
                fig4.update_layout(**PLOTLY_THEME)
                st.plotly_chart(fig4, use_container_width=True)
            else:
                st.info("No payee data available.")

elif st.session_state.logged_in and selected == "Chatbot":

    st.markdown("## 🤖 AI Cheque Assistant")

    records = load_all_records()
    df = pd.DataFrame(records)
    if df.empty:
        st.warning("No cheque data available. Please analyze some cheques first.")
        st.stop()

    # ---- Suggested questions ----
    st.markdown("### 💡 Try asking:")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Show all cheques from Rakesh"):
            st.session_state.chat_input = "show all cheques from rakesh"

        if st.button("Highest amount cheque"):
            st.session_state.chat_input = "highest amount cheque"

    with col2:
        if st.button("Total amount of all cheques"):
            st.session_state.chat_input = "total amount"

        if st.button("Find cheque by number"):
            st.session_state.chat_input = "cheque number 12345"

    st.markdown("---")
    st.markdown("""
        <style>
        input::placeholder {
            color: #9ca3af !important;  /* light grey */
            opacity: 1;
        }
        </style>
        """, unsafe_allow_html=True)
    
    # ---- Input + Send button ----
    
    
    
    col_input, col_btn = st.columns([5,1])

    with col_input:
        user_input = st.text_input(
            "Ask your question",
            value=st.session_state.get("chat_input", ""),
            placeholder="e.g. show cheques from rakesh"
        )

    with col_btn:
        st.markdown("<div style='margin-top:8px'></div>", unsafe_allow_html=True)  
        send = st.button("➤", use_container_width=True)

    # ---- Response ----
    if send and user_input:
        with st.spinner("Thinking..."):
            answer = chatbot_response(user_input, df)

    # 👉 store history
        st.session_state.chat_history.append(("user", user_input))
        st.session_state.chat_history.append(("bot", answer))

        st.session_state.chat_input = ""
        
    
    # ---- Chat History ----
    for role, msg in st.session_state.chat_history:
        if role == "user":
            st.markdown(f"**🧑 You:** {msg}")
        else:
            st.markdown(f"**🤖 Bot:** {msg}")
