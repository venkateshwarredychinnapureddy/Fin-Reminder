import streamlit as st
import pandas as pd
import smtplib
import os
from datetime import datetime, date
from email.mime.text import MIMEText

# --- CONFIGURATION ---
DB_FILE = "bills_data.csv"

def send_email_notification(to_email, app_password, bill_name, days_left):
    """Function to send email via Gmail SMTP"""
    sender_email = to_email  # Sending to yourself for reminders
    subject = f"⚠️ BILL ALERT: {bill_name} expires in {days_left} days!"
    body = f"Hello,\n\nThis is a reminder that your bill '{bill_name}' is due on {due_date}. Please clear it soon to avoid penalties."
    
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = to_email

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, app_password)
            server.sendmail(sender_email, to_email, msg.as_string())
        return True
    except Exception as e:
        st.error(f"Email failed: {e}")
        return False

# --- LOGIN LOGIC ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if not st.session_state['logged_in']:
    st.title("🔐 BillGuard Login")
    with st.form("login_form"):
        email = st.text_input("Gmail Address")
        password = st.text_input("Gmail App Password", type="password")
        if st.form_submit_button("Login"):
            if "@gmail.com" in email and len(password) >= 16:
                st.session_state['logged_in'] = True
                st.session_state['email'] = email
                st.session_state['password'] = password
                st.rerun()
            else:
                st.error("Please enter a valid Gmail and 16-digit App Password.")
    st.stop()

# --- MAIN APP (After Login) ---
st.title("📅 Proactive Bill Sentinel")
st.sidebar.write(f"Logged in as: {st.session_state['email']}")

# Load/Init Data
if os.path.exists(DB_FILE):
    df = pd.read_csv(DB_FILE)
    df['Due Date'] = pd.to_datetime(df['Due Date']).dt.date
else:
    df = pd.DataFrame(columns=["Bill Name", "Amount", "Due Date"])

# --- SIDEBAR: ADD BILL ---
with st.sidebar.form("add_bill"):
    name = st.text_input("Bill Name")
    amt = st.number_input("Amount", min_value=0)
    due = st.date_input("Due Date")
    if st.form_submit_button("Save"):
        new_row = pd.DataFrame([[name, amt, due]], columns=df.columns)
        df = pd.concat([df, new_row], ignore_index=True)
        df.to_csv(DB_FILE, index=False)
        st.success("Saved!")
        st.rerun()

# --- DASHBOARD & NOTIFICATIONS ---
if not df.empty:
    today = date.today()
    df['Days Left'] = df['Due Date'].apply(lambda x: (x - today).days)
    
    # Check for urgent bills to notify
    urgent = df[df['Days Left'] <= 3]
    
    if not urgent.empty:
        st.error(f"You have {len(urgent)} urgent bills!")
        if st.button("📧 Send Email Reminder to Myself"):
            for _, row in urgent.iterrows():
                success = send_email_notification(
                    st.session_state['email'], 
                    st.session_state['password'], 
                    row['Bill Name'], 
                    row['Days Left']
                )
                if success:
                    st.success(f"Notification sent for {row['Bill Name']}!")

    st.dataframe(df.sort_values("Days Left"), use_container_width=True)

if st.sidebar.button("Logout"):
    st.session_state['logged_in'] = False
    st.rerun()
