import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from pdf_reader import extract_text_from_pdf
from analyzer import analyze_report
import pytesseract
from PIL import Image
import base64
import os
st.set_page_config(
    page_title="AI BASED MEDICAL REPORT ANALYZER",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ---------------- USER DATABASE ----------------
USER_DB = "users.csv"

if not os.path.exists(USER_DB):
    pd.DataFrame(columns=["username","password"]).to_csv(USER_DB,index=False)

def signup_user(username,password):

    df = pd.read_csv(USER_DB)

    if username in df["username"].values:
        return False

    new_user = pd.DataFrame([[username,password]],columns=["username","password"])
    df = pd.concat([df,new_user],ignore_index=True)
    df.to_csv(USER_DB,index=False)

    return True


def login_user(username,password):

    df = pd.read_csv(USER_DB)

    user = df[(df["username"]==username) & (df["password"]==password)]

    return len(user) > 0


# ---------------- BACKGROUND ----------------
def set_background(image_file):

    with open(image_file,"rb") as img:
        encoded = base64.b64encode(img.read()).decode()

    st.markdown(f"""
    <style>

    .stApp {{
        background: linear-gradient(rgba(0,0,0,0.40), rgba(0,0,0,0.40)),
        url("data:image/png;base64,{encoded}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}

    .block-container {{
        background: rgba(0,0,0,0.35);
        padding: 2rem;
        border-radius: 15px;
    }}

    h1,h2,h3,h4 {{
        color:white !important;
    }}

    label {{
        color:white !important;
        font-weight:bold;
    }}

    /* -------- LOGIN SIGNUP BORDER STYLE -------- */

    div[role="radiogroup"] {{
        background:white;
        border-radius:12px;
        padding:15px;
        border:2px solid #e0e0e0;
        display:flex;
        justify-content:center;
        gap:40px;
        width:350px;
        margin:auto;
    }}

    div[role="radiogroup"] label {{
        color:white !important;
        font-size:20px !important;
        font-weight:bold !important;
    }}

    div[role="radiogroup"] label:hover {{
        border:2px solid white;
        border-radius:8px;
        padding:5px;
        background:rgba(255,255,255,0.2);
    }}

    .stTextInput input,
    .stNumberInput input,
    .stSelectbox div {{
        background:rgba(255,255,255,0.95) !important;
        color:black !important;
        border-radius:8px;
    }}

    section[data-testid="stFileUploader"]{{
        background: rgba(255,255,255,0.15);
        border:2px dashed rgba(255,255,255,0.6);
        border-radius:18px;
        padding:35px;
        backdrop-filter: blur(10px);
    }}

    div[data-testid="stFileUploaderDropzone"]{{
        background: rgba(255,255,255,0.92);
        border-radius:12px;
        padding:30px;
    }}

    .stAlert {{
        background: rgba(255,255,255,0.85) !important;
        color:black !important;
    }}

    div[data-testid="stMetricValue"] {{
        color:white !important;
        font-size:30px;
        font-weight:bold;
    }}

    div[data-testid="stMetricLabel"] {{
        color:#e0e0e0 !important;
    }}

    </style>
    """,unsafe_allow_html=True)


set_background("background.png")


# ---------------- SESSION ----------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in=False


# ---------------- AUTH PAGE ----------------
def auth_page():

    st.markdown("""
    <h1 style='text-align:center;
    background:rgba(0,0,0,0.45);
    padding:15px;
    border-radius:10px;'>
    🩺 AI BASED MEDICAL REPORT ANALYZER
    </h1>
    """,unsafe_allow_html=True)

    st.markdown("### ")

    page = st.radio(
        "Select Page",
        ["Login","Signup"],
        horizontal=True
    )
    username = st.text_input("Username")
    password = st.text_input("Password",type="password")

    if page=="Signup":

        if st.button("Create Account"):

            if signup_user(username,password):

                st.success("Account created successfully! Please login.")

            else:

                st.error("Username already exists")


    if page=="Login":

        if st.button("Login"):

            if login_user(username,password):

                st.session_state.logged_in=True
                st.success("Login Successful")
                st.rerun()

            else:

                st.error("Invalid credentials")


# ---------------- LOGIN CHECK ----------------
if not st.session_state.logged_in:

    auth_page()
    st.stop()


# ---------------- SIDEBAR ----------------
st.sidebar.title("Navigation")

if st.sidebar.button("Logout"):
    st.session_state.logged_in=False
    st.rerun()


# ---------------- TITLE ----------------
st.title("🩺 AI BASED MEDICAL REPORT ANALYZER")
st.markdown("### Upload a clinical report to detect abnormalities and health insights")
st.divider()


# ---------------- FILE UPLOAD ----------------
uploaded_file = st.file_uploader(
    "Upload Medical Report",
    type=["pdf","txt","png","jpg","jpeg"]
)

text=""

if uploaded_file:

    if uploaded_file.type=="application/pdf":

        text = extract_text_from_pdf(uploaded_file)

    elif uploaded_file.type=="text/plain":

        text = uploaded_file.read().decode()

    else:

        image = Image.open(uploaded_file)

        st.subheader("Uploaded Clinical Report")

        col1,col2,col3 = st.columns([1,2,1])

        with col2:
            st.image(image,width=450)

        text = pytesseract.image_to_string(image)


# ---------------- ANALYSIS ----------------
if text:

    results = analyze_report(text)

    if results:

        df = pd.DataFrame(results)

        abnormal = len(df[df["Status"]!="Normal"])
        risk_score = df["Severity_Score"].mean()

        st.subheader("Health Summary Dashboard")

        m1,m2,m3 = st.columns(3)

        m1.metric("Parameters Scanned",len(df))
        m2.metric("Abnormal Findings",abnormal)
        m3.metric("Overall Risk Score",f"{risk_score:.1f}%")

        st.divider()

        col1,col2 = st.columns(2)

        with col1:

            st.subheader("Clinical Findings")

            def color_status(val):

                if val=="High":
                    return "background-color:#ffcccc;color:#cc0000;font-weight:bold"

                if val=="Low":
                    return "background-color:#ffe6cc;color:#cc6600;font-weight:bold"

                return "background-color:#e6fffa;color:#008080"

            st.dataframe(
                df.style.applymap(color_status,subset=["Status"]),
                use_container_width=True
            )

        with col2:

            st.subheader("Severity Zone Analysis")

            fig,ax = plt.subplots(figsize=(8,5))

            colors=[
                "#e74c3c" if s!="Normal" else "#2ecc71"
                for s in df["Status"]
            ]

            ax.barh(df["Parameter"],df["Severity_Score"],color=colors)

            ax.set_xlabel("Deviation from Optimal (%)")
            ax.set_title("Risk Proximity Scale")

            st.pyplot(fig)

        st.divider()

        st.markdown("## 💡 AI Health Recommendations")

        recommendations=[]

        for _,row in df.iterrows():

            p=row["Parameter"]
            s=row["Status"]

            if p=="Hemoglobin" and s=="Low":
                recommendations.append("Increase iron-rich foods like spinach, lentils, dates.")

            if p=="WBC" and s=="High":
                recommendations.append("Elevated WBC may indicate infection. Ensure rest and hydration.")

            if p=="Glucose" and s=="High":
                recommendations.append("High glucose detected. Reduce sugar intake and exercise.")

            if p=="Cholesterol" and s=="High":
                recommendations.append("High cholesterol detected. Reduce fatty foods.")

        if recommendations:

            for r in recommendations:
                st.warning(r)

        else:
            st.success("All parameters are within normal clinical range.")

        st.divider()

        if abnormal>0:

            st.error(
            f"⚠ {abnormal} parameters are outside normal range. Please consult a healthcare professional."
            )

        else:

            st.success(
            "Perfect Health Summary: All scanned parameters are within range."
            )

    else:

        st.warning(
        "No medical parameters detected. Upload a valid lab report."
        )