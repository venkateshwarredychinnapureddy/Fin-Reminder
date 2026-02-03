import streamlit as st
import pandas as pd
import smtplib
import os
from datetime import datetime, date
from email.mime.text import MIMEText

# ---------------- CONFIG ----------------
DB_FILE = "bills_ledger.csv"
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465

# ---------------- EMAIL FUNCTION ----------------
def send_email(user_email, app_password, subject, body):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = user_email
    msg["To"] = user_email

    try:
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(user_email, app_password)
            server.send_message(msg)
        return True
    except Exception as e:
        st.error(f"Email failed: {e}")
        return False

# ---------------- SESSION STATE ----------------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# ---------------- LOGIN SCREEN ----------------
if not st.session_state.authenticated:

    st.title("🔐 Secure BillGuard Login")

    with st.form("login_form"):
        email = st.text_input("Gmail Address")
        pwd = st.text_input("Gmail App Password", type="password")
        login_btn = st.form_submit_button("Login")

        if login_btn:
            if "@gmail.com" in email and len(pwd.replace(" ", "")) >= 16:
                st.session_state.authenticated = True
                st.session_state.email = email
                st.session_state.app_pwd = pwd.replace(" ", "")

                # -------- LOGIN EMAIL NOTIFICATION --------
                send_email(
                    email,
                    st.session_state.app_pwd,
                    "Login Alert - Bill Expiry Sentinel",
                    "You have successfully logged into Bill Expiry Sentinel."
                )

                st.success("Login Successful!")
                st.toast("🔔 Login notification sent!")
                st.rerun()
            else:
                st.error("Use a valid Gmail & 16-digit App Password")

    st.stop()

# ---------------- MAIN DASHBOARD ----------------
st.title("📊 Bill Expiry Sentinel")
st.sidebar.success(f"Logged in as:\n{st.session_state.email}")

# ---------------- LOAD DATA ----------------
if os.path.exists(DB_FILE):
    df = pd.read_csv(DB_FILE)
    df["Due Date"] = pd.to_datetime(df["Due Date"]).dt.date
else:
    df = pd.DataFrame(columns=["Bill Name", "Amount", "Due Date"])

# ---------------- ADD BILL ----------------
with st.sidebar.form("add_bill"):
    st.subheader("➕ Add Bill")
    name = st.text_input("Bill Name")
    amount = st.number_input("Amount ₹", min_value=0)
    due = st.date_input("Due Date", min_value=date.today())
    save_btn = st.form_submit_button("Save")

    if save_btn:
        if name.strip() == "":
            st.error("Bill name cannot be empty")
        else:
            new_row = pd.DataFrame([[name, amount, due]],
                                   columns=df.columns)
            df = pd.concat([df, new_row], ignore_index=True)
            df.to_csv(DB_FILE, index=False)

            # ---------- ITEM ADDED EMAIL ----------
            send_email(
                st.session_state.email,
                st.session_state.app_pwd,
                "New Bill Added",
                f"{name} bill of ₹{amount} added. Due on {due}"
            )

            st.toast("✅ Bill added successfully!")
            st.success("Bill saved & email sent")
            st.rerun()

# ---------------- ALERT SYSTEM ----------------
if not df.empty:

    today = date.today()
    df["Days Remaining"] = df["Due Date"].apply(lambda x: (x - today).days)

    urgent = df[df["Days Remaining"] <= 3].sort_values("Days Remaining")

    if not urgent.empty:
        st.warning(f"🚨 {len(urgent)} bills due soon!")

        if st.button("📧 Send Due Alerts"):
            for _, row in urgent.iterrows():
                send_email(
                    st.session_state.email,
                    st.session_state.app_pwd,
                    f"URGENT: {row['Bill Name']} Due",
                    f"{row['Bill Name']} is due on {row['Due Date']} "
                    f"({row['Days Remaining']} days left)"
                )

            st.toast("📨 Alert emails sent!")

    st.subheader("📅 All Bills")
    st.dataframe(df.sort_values("Days Remaining"),
                 use_container_width=True)

# ---------------- LOGOUT ----------------
if st.sidebar.button("Logout"):
    st.session_state.authenticated = False
    st.toast("Logged out!")
    st.rerun()
