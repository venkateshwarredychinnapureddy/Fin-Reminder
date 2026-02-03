import streamlit as st
import pandas as pd
from datetime import datetime, date
import os

# --- CONFIGURATION & SETUP ---
st.set_page_config(page_title="BillGuard Sentinel", page_icon="📅")
DB_FILE = "bills_data.csv"

# Load existing data or create a new one
if os.path.exists(DB_FILE):
    df = pd.read_csv(DB_FILE)
    df['Due Date'] = pd.to_datetime(df['Due Date']).dt.date
else:
    df = pd.DataFrame(columns=["Bill Name", "Amount", "Due Date", "Category"])

# --- SIDEBAR: INPUT FORM ---
st.sidebar.header("➕ Add New Bill")
with st.sidebar.form("bill_form", clear_on_submit=True):
    name = st.text_input("Bill Name (e.g. Electricity)")
    amount = st.number_input("Amount (₹)", min_value=0.0, step=100.0)
    due_date = st.date_input("Due Date", min_value=date.today())
    category = st.selectbox("Category", ["Utility", "EMI", "Subscription", "Other"])
    submit = st.form_submit_button("Save Bill")

    if submit and name:
        new_entry = pd.DataFrame([[name, amount, due_date, category]], columns=df.columns)
        df = pd.concat([df, new_entry], ignore_index=True)
        df.to_csv(DB_FILE, index=False)
        st.sidebar.success("Bill Saved!")
        st.rerun()

# --- MAIN DASHBOARD ---
st.title("📅 Proactive Bill Expiry Sentinel")
st.subheader("Keep track of your financial obligations")

if not df.empty:
    today = date.today()
    
    # 1. LOGIC: Calculate Days Left & Status
    df['Days Left'] = df['Due Date'].apply(lambda x: (x - today).days)
    
    # 2. PROACTIVE NOTIFICATIONS (Top of screen)
    urgent_bills = df[df['Days Left'] <= 3]
    if not urgent_bills.empty:
        st.error(f"🚨 ACTION REQUIRED: You have {len(urgent_bills)} bill(s) expiring within 72 hours!")
        for _, row in urgent_bills.iterrows():
            st.toast(f"Pay {row['Bill Name']} soon!", icon="⚠️")

    # 3. DISPLAY DASHBOARD
    # Color-coding logic for the table
    def color_status(val):
        if val <= 3: return 'background-color: #ff4b4b; color: white' # Red
        if val <= 7: return 'background-color: #ffa500; color: white' # Orange
        return ''

    styled_df = df.sort_values(by="Days Left").style.applymap(color_status, subset=['Days Left'])
    
    st.write("### Upcoming Bills")
    st.dataframe(styled_df, use_container_width=True)

    # 4. ACTION: CLEAR BILLS
    st.write("### Mark as Paid")
    bill_to_delete = st.selectbox("Select a bill to clear:", df['Bill Name'].unique())
    if st.button("✅ Confirm Payment"):
        df = df[df['Bill Name'] != bill_to_delete]
        df.to_csv(DB_FILE, index=False)
        st.success(f"Successfully cleared {bill_to_delete}!")
        st.rerun()
    else:
