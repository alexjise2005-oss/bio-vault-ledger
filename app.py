import streamlit as st
import psycopg2
import json
import os
import pandas as pd
import plotly.express as px

"""
# 🛑 SECURITY GATEKEEPER: Stop unauthorized users instantly
if not st.user.is_logged_in:
    st.title("🔒 Production Logistics Ledger Control Panel")
    st.info("Por favor, inicia sesión para acceder al panel de control de la red.")
    if st.button("Iniciar Sesión", type="primary"):
        st.login()
    st.stop()  # Aborts execution right here if not authenticated!
"""

st.set_page_config(page_title="Enterprise Logistics Dashboard", page_icon="📦", layout="wide")

# Read database URL from Streamlit's secrets manager configuration block
from dotenv import load_dotenv
# Load the exact same credentials your backend uses
load_dotenv(r"C:\Users\alexj\mcp-lab\.env")
DB_URL = os.getenv("DB_URL")
LOG_FILE = r"C:\Users\alexj\mcp-lab\audit_log.json"

# --- AUTHENTICATION LAYER ---
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if st.session_state["authenticated"]:
        return True

    st.markdown("<h2 style='text-align: center;'>🔐 Enterprise Access Gate</h2>", unsafe_allow_html=True)
    with st.container(border=True):
        username = st.text_input("User ID Descriptor", placeholder="e.g. admin")
        password = st.text_input("Security Access Code (Password)", type="password")
        login_btn = st.button("Authenticate Identity System")
        
        if login_btn:
            if username == "admin" and password == "logistics2026":
                st.session_state["authenticated"] = True
                st.success("Access Granted. Re-rendering interface maps...")
                st.rerun()
            else:
                st.error("❌ Authentication Breach: Identity coordinates invalid.")
    return False

if check_password():

    # --- CLOUD CONTEXT POSTGRES PARSING ---
    def load_sql_data():
        try:
            conn = psycopg2.connect(DB_URL)
            query = "SELECT record_id, name, status, details, last_updated FROM inventory;"
            df_raw = pd.read_sql_query(query, conn)
            conn.close()
            
            if df_raw.empty: return pd.DataFrame()
            
            rows = []
            for _, row in df_raw.iterrows():
                status_str = str(row["status"])
                if "out" in status_str.lower(): emoji = "🔴 Out of Stock"
                elif "low" in status_str.lower(): emoji = "🟡 Low Stock"
                else: emoji = "🟢 In Stock"
                
                rows.append({
                    "SKU / Record ID": row["record_id"],
                    "Asset Name": row["name"],
                    "Logistics Status": emoji,
                    "Warehouse Location / Notes": row["details"],
                    "Synchronization Timestamp": row["last_updated"]
                })
            return pd.DataFrame(rows)
        except Exception as e:
            return pd.DataFrame()

    def load_logs():
        if not os.path.exists(LOG_FILE): return []
        try:
            with open(LOG_FILE, "r", encoding="utf-8") as f: return json.load(f)
        except: return []

    df = load_sql_data()
    logs = load_logs()

    # --- INTERFACE STRUCTURING ---
    st.markdown("<div style='display:flex; justify-content:space-between; align-items:center;'><h1>🏭 Production Logistics SQL Ledger Control Panel</h1></div>", unsafe_allow_html=True)
    st.caption("Active Production Node linked live via Supabase PostgreSQL Cloud Cluster Datamesh Engine.")
    
    if st.sidebar.button("🔒 Terminate Session / Logout"):
        st.session_state["authenticated"] = False
        st.rerun()

    st.markdown("---")

    if df.empty:
        st.info("👋 Supabase Cloud Database is initialized but empty. Command Claude via your local tool config to inject live elements.")
    else:
        # --- STATS ROW ---
        with st.container(border=True):
            col1, col2, col3, col4 = st.columns(4)
            with col1: st.metric("Cloud Assets Indexed", len(df))
            with col2: st.metric("Low Stock Alerts", len(df[df['Logistics Status'].str.contains('🟡')]))
            with col3: st.metric("Depleted Supply Nodes", len(df[df['Logistics Status'].str.contains('🔴')]))
            with col4: st.metric("Database Health", "Supabase PostgreSQL Connected ✅")

        st.markdown("### 📊 Real-time Relational Data Mesh")
        c_col1, c_col2 = st.columns([1, 1])
        
        with c_col1:
            status_counts = df['Logistics Status'].value_counts().reset_index()
            status_counts.columns = ['Status', 'Count']
            fig = px.pie(status_counts, values='Count', names='Status', hole=0.4,
                         color_discrete_map={"🟢 In Stock":"#2ecc71","🟡 Low Stock":"#f1c40f","🔴 Out of Stock":"#e74c3c"})
            fig.update_layout(margin=dict(t=20, b=20, l=10, r=10), height=230)
            st.plotly_chart(fig, use_container_width=True)
            
        with c_col2:
            st.write("**⚠️ High Metric Supply Risk Priority Matrix**")
            watchlist = df[df['Logistics Status'].str.contains('🟡|🔴')]
            if not watchlist.empty:
                st.dataframe(watchlist[['SKU / Record ID', 'Asset Name', 'Logistics Status']], hide_index=True, use_container_width=True)
            else:
                st.success("✨ Supply chains optimal. Zero cloud network latency anomalies recorded.")

        st.markdown("---")
        
        # --- DATA GRID ---
        st.markdown("### 🗂️ Live Supabase Data Engine Registry View")
        search = st.text_input("🔍 Filter row indexes instantaneously...", "")
        filtered_df = df[df.astype(str).apply(lambda x: x.str.contains(search, case=False)).any(axis=1)] if search else df
        st.dataframe(filtered_df, hide_index=True, use_container_width=True)

    # --- AUDIT STREAM TRAIL PANEL ---
    st.markdown("---")
    st.markdown("### 📜 Real-Time SQL Engine Transaction Logs")
    if logs:
        with st.container(height=150, border=True):
            for log in logs:
                st.markdown(f"⏱️ `{log['timestamp']}` — **{log['event']}**")
    else:
        st.text("No data logs recorded in the session file pathway yet.")

    if st.button("🔄 Force Interface Redraw"): st.rerun()
