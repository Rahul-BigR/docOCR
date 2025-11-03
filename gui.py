# gui.py
import streamlit as st
import pandas as pd
import time
import main
from streamlit_option_menu import option_menu
from io import BytesIO
import os
import tempfile
import json
import cv2
from PIL import Image

os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

# --- Page Config ---
st.set_page_config(
    page_title="DocOCR – Financial Document Analyzer",
    layout="wide",
)

# --- Load Models Once (YOLO + TrOCR) ---
@st.cache_resource
def load_models():
    with st.spinner("🚀 Initializing OCR models..."):
        model, trocr_model, processor, DEVICE = main.initialize_models()
    return model, trocr_model, processor, DEVICE

model, trocr_model, processor, DEVICE = load_models()
st.success("✅ Models loaded successfully!")

USERS_FILE = "users.json"

# --- Load or Create Users ---
def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    else:
        return {"admin": "admin"}

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)
        
# --- Session State Initialization ---
if "users" not in st.session_state:
    st.session_state.users = load_users()

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "username" not in st.session_state:
    st.session_state.username = None


# --- Sidebar Navigation ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/1041/1041916.png", width=80)
    st.markdown("<h2 style='color:black;'>DocOCR</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color:gray;'>AI-Powered Financial Document Analyzer</p>", unsafe_allow_html=True)
    st.markdown("---")

    if not st.session_state.logged_in:
        selected = option_menu(
            menu_title=None,
            options=["Login", "Register"],
            icons=["box-arrow-in-right", "pencil-square"],
            default_index=0,
            styles={
                "container": {"background-color": "#064E3B", "padding": "5px"},
                "icon": {"color": "white"},
                "nav-link": {
                    "font-size": "15px",
                    "color": "white",
                    "--hover-color": "#0D9488",
                },
                "nav-link-selected": {"background-color": "#0D9488"},
            },
        )
    else:
        selected = option_menu(
            menu_title=None,
            options=["","Dashboard"],
            icons=["","bar-chart-line"],
            default_index=0,
            styles={
                "container": {"background-color": "#064E3B", "padding": "5px"},
                "icon": {"color": "white"},
                "nav-link": {
                    "font-size": "15px",
                    "color": "white",
                    "--hover-color": "#0D9488",
                },
                "nav-link-selected": {"background-color": "#0D9488"},
            },
        )
        st.markdown(f"<p style='color:lightgray;'>🧑‍💻 Logged in as: <b>{st.session_state.username}</b></p>", unsafe_allow_html=True)
        if st.button("Logout", use_container_width=True, type="primary"):
            st.session_state.logged_in = False
            st.rerun()

# --- Registration Page ---
if not st.session_state.logged_in and selected == "Register":
    st.title("📝 Create Your DocOCR Account")
    st.write("---")

    with st.form("register_form", clear_on_submit=True):
        username = st.text_input("Choose a username")
        password = st.text_input("Choose a password", type="password")
        submitted = st.form_submit_button("Register ➜")

        if submitted:
            if not username or not password:
                st.error("Please fill in all fields before registering.")
            elif username in st.session_state.users:
                st.warning("⚠️ Username already exists. Please choose another.")
            else:
                # Save new user
                st.session_state.users[username] = password
                save_users(st.session_state.users)
                st.success(f"✅ User '{username}' registered successfully!")
                time.sleep(1)
                st.rerun()

# --- Login Page ---
elif not st.session_state.logged_in and selected == "Login":
    st.title("🔐 DocOCR Login Portal")
    st.write("---")

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        login = st.form_submit_button("Login ➜")

        if login:
            if username in st.session_state.users and st.session_state.users[username] == password:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.success("✅ Login successful! Redirecting to dashboard...")
                time.sleep(1)
                st.rerun()
            else:
                st.error("❌ Invalid username or password.")

    st.markdown(
        "<center>Don't have an account?<br><b>Select 'Register' from the sidebar.</b></center>",
        unsafe_allow_html=True,
    )
# --- Processing Page ---
elif st.session_state.logged_in and selected == "":
    st.title("📊 DocOCR Document Analytics Dashboard")
    st.write("---")

    # --- Upload Section (Image Upload + Processing) ---
    with st.expander("📤 Upload Cheque Image for OCR", expanded=True):
        uploaded_file = st.file_uploader(
            "Upload cheque image (JPG, JPEG, or PNG)",
            type=["jpg", "jpeg", "png"]
        )

        if uploaded_file:
            st.image(uploaded_file, caption=f"Uploaded: {uploaded_file.name}", width=600)

            temp_dir = tempfile.mkdtemp()
            image_path = os.path.join(temp_dir, uploaded_file.name)
            image = Image.open(uploaded_file)
            image.save(image_path)

            st.success("✅ Image uploaded successfully!")

            if st.button("🔍 Process Image Using OCR"):
                with st.spinner("⏳ Running cheque OCR pipeline... Please wait..."):
                    try:
                        success = main.run_pipeline(image_path, model, trocr_model, processor, DEVICE)

                        if success:
                            st.success("✅ OCR Processing Completed!")

                            json_folder = "final_output_json"
                            json_name = os.path.splitext(os.path.basename(image_path))[0] + ".json"
                            json_path = os.path.join(json_folder, json_name)

                            if os.path.exists(json_path):
                                with open(json_path, "r", encoding="utf-8") as f:
                                    extracted_data = json.load(f)
                                st.subheader("📑 Extracted Cheque Details")
                                st.json(extracted_data)
                            else:
                                st.warning("⚠️ No output JSON found. Please verify processing.")
                        else:
                            st.error("❌ Failed to process image.")
                    except Exception as e:
                        st.error(f"🚨 Error: {e}")


    # --- Extracted Data Table (From JSON Folder) ---
    with st.expander("📑 View All Processed Cheques", expanded=False):
        json_folder = "final_output_json"

        if os.path.exists(json_folder) and os.listdir(json_folder):
            all_data = []
            for file in os.listdir(json_folder):
                if file.endswith(".json"):
                    with open(os.path.join(json_folder, file), "r", encoding="utf-8") as f:
                        data = json.load(f)
                    data["File"] = file
                    all_data.append(data)

            df = pd.DataFrame(all_data)
            st.dataframe(df, use_container_width=True)

            output = BytesIO()
            df.to_excel(output, index=False)
            st.download_button(
                "⬇️ Download All Extracted Data (Excel)",
                data=output.getvalue(),
                file_name="All_Cheques_Data.xlsx",
            )
        else:
            st.info("📂 No processed cheques found yet. Upload and process one above.")

# --- Dashboard Section ---
elif st.session_state.logged_in and selected == "Dashboard":
    st.title("📊 Analytics Overview")
    st.write("---")

    json_folder = "final_output_json"
    all_data = []

    # Load all JSONs
    if os.path.exists(json_folder) and os.listdir(json_folder):
        for file in os.listdir(json_folder):
            if file.endswith(".json"):
                with open(os.path.join(json_folder, file), "r", encoding="utf-8") as f:
                    data = json.load(f)
                data["File"] = file
                all_data.append(data)

    if all_data:
        df = pd.DataFrame(all_data)

        # Convert numeric + date columns safely
        if "amount" in df.columns:
            df["amount_numeric"] = pd.to_numeric(df["amount"], errors="coerce")
        else:
            df["amount_numeric"] = 0

        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
        else:
            df["date"] = pd.NaT

        # --- Metrics Overview ---
        col1, col2, col3, col4 = st.columns(4)
        total_docs = len(df)
        total_amount = df["amount_numeric"].sum()
        avg_amount = df["amount_numeric"].mean()
        latest_date = df["date"].max()

        col1.metric("Total Checks", total_docs)
        col2.metric("Total Amount", f"₹{total_amount:,.2f}")
        col3.metric("Average Amount", f"₹{avg_amount:,.2f}")
        col4.metric("Latest Check Date", latest_date.strftime("%Y-%m-%d") if pd.notna(latest_date) else "N/A")

        # --- Tabs for Detailed Charts ---
        tab1, tab2, tab3, tab4 = st.tabs([
            "Amount Distribution", "Temporal Trends", "Bank Analysis", "Payee Breakdown"
        ])

        # --- Tab 1: Amount Distribution ---
        with tab1:
            st.subheader("📊 Amount Distribution")
            c1, c2 = st.columns(2)
            with c1:
                st.bar_chart(df["amount_numeric"])
            with c2:
                import plotly.express as px
                st.subheader("Box Plot of Cheque Amounts")
                fig = px.box(df, y="amount_numeric", points="all", title="Cheque Amount Distribution")
                st.plotly_chart(fig, use_container_width=True)


        # --- Tab 2: Temporal Trends ---
        with tab2:
            st.subheader("📈 Amount Trend Over Time")
            if "date" in df.columns and df["date"].notna().any():
                df_sorted = df.sort_values("date")
                st.line_chart(df_sorted.set_index("date")["amount_numeric"])
            else:
                st.info("No valid date data available for trend analysis.")

        # --- Tab 3: Bank Analysis ---
        with tab3:
            st.subheader("🏦 Amount Distribution by Bank")
            if "bank_name" in df.columns:
                bank_summary = (
                    df.groupby("bank_name", as_index=False)["amount_numeric"].sum()
                )
                st.write(
                    "#### 💹 Bank-wise Cheque Amounts"
                )
                st.dataframe(bank_summary, use_container_width=True)
                st.plotly_chart(
                    px.pie(
                        bank_summary,
                        names="bank_name",
                        values="amount_numeric",
                        hole=0.4,
                        color_discrete_sequence=px.colors.sequential.Greens,
                    ),
                    use_container_width=True,
                )
            else:
                st.info("No bank information found in processed cheques.")

        # --- Tab 4: Payee Breakdown ---
        with tab4:
            st.subheader("🧾 Top Payees by Amount")
            if "payee_name" in df.columns:
                payee_summary = (
                    df.groupby("payee_name", as_index=False)["amount_numeric"].sum()
                )
                st.bar_chart(
                    payee_summary.set_index("payee_name")["amount_numeric"]
                )
            else:
                st.info("No payee names available to display.")
    else:
        st.info("📂 No processed cheque data found yet. Upload and process documents first.")
