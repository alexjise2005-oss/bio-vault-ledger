# /// script
# dependencies = ["mcp[cli]", "psycopg[binary]", "python-dotenv"]
# ///

import os
import json
import psycopg
from datetime import datetime
from mcp.server.fastmcp import FastMCP

# Load your local environment credentials matching your user folder
from dotenv import load_dotenv
load_dotenv(r"C:\Users\alexj\mcp-lab\.env")

DB_URL = os.getenv("DB_URL")
LOG_FILE = r"C:\Users\alexj\mcp-lab\audit_log.json"

mcp = FastMCP("Bio_Vault_Enterprise")

def get_db_connection():
    """Passes the connection string directly to psycopg, stripping out pgbouncer url parameters."""
    clean_url = DB_URL.split("?")[0] if "?" in DB_URL else DB_URL
    return psycopg.connect(clean_url)

def init_db():
    """Initializes the database structure if it doesn't exist."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            record_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            status TEXT NOT NULL,
            details TEXT,
            last_updated TEXT
        );
    """)
    conn.commit()
    conn.close()

# Initialize tables
init_db()

def log_audit_event(summary: str):
    logs = []
    if os.path.exists(LOG_FILE):
        try:
            with open(LOG_FILE, "r", encoding="utf-8") as f: logs = json.load(f)
        except: logs = []
    logs.insert(0, {"timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "event": summary})
    with open(LOG_FILE, "w", encoding="utf-8") as f: json.dump(logs[:50], f, indent=4, ensure_ascii=False)

# --- CLOUD CONTEXT TOOLS ---
@mcp.tool()
def view_lab_inventory() -> str:
    """Retrieves the data registry from a local sandbox text structure."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT record_id, name, status FROM inventory;")
    rows = cursor.fetchall()
    conn.close()
    
    if not rows: return "🔬 REGISTRY IS CURRENTLY EMPTY."
    output = "🔬 CURRENT LAB MATRIX INVENTORY:\n"
    for row in rows:
        output += f"- [{row[0]}] Name: {row[1]} | Status: {row[2]}\n"
    return output

@mcp.tool()
def save_record(record_id: str, item_name: str, status: str, details: str) -> str:
    """Inserts or updates a record inside the live cloud database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    cursor.execute("""
        INSERT INTO inventory (record_id, name, status, details, last_updated)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (record_id) 
        DO UPDATE SET name = EXCLUDED.name, status = EXCLUDED.status, details = EXCLUDED.details, last_updated = EXCLUDED.last_updated;
    """, (record_id, item_name, status, details, timestamp))
        
    conn.commit()
    conn.close()
    log_audit_event(f"Synced Cloud Record {record_id}")
    return f" SUCCESS: Data element {record_id} cleanly processed into cloud cluster matrix."

@mcp.tool()
def remove_record(record_id: str) -> str:
    """Removes a specific database record using its unique ID identifier."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM inventory WHERE record_id = %s;", (record_id,))
    conn.commit()
    conn.close()
    log_audit_event(f"Dropped Cloud Record {record_id}")
    return f" SUCCESS: Matrix index item {record_id} truncated securely."

@mcp.tool()
def save_records_bulk(records_json: str) -> str:
    """Accepts multiple records and executes a batch data dump into the database."""
    try:
        new_records = json.loads(records_json)
        conn = get_db_connection()
        cursor = conn.cursor()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        for r_id, r_info in new_records.items():
            cursor.execute("""
                INSERT INTO inventory (record_id, name, status, details, last_updated)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (record_id) 
                DO UPDATE SET name = EXCLUDED.name, status = EXCLUDED.status, details = EXCLUDED.details, last_updated = EXCLUDED.last_updated;
            """, (r_id, r_info.get("name", "Unknown"), r_info.get("status", "In Stock"), r_info.get("details", "N/A"), timestamp))
            
        conn.commit()
        conn.close()
        log_audit_event(f"Processed multi-cluster write batch: {len(new_records)} nodes updated.")
        return f" SUCCESS: Array simulation matrix parsed for {len(new_records)} coordinates."
    except Exception as e:
        return f" Transaction abort error: {str(e)}"

@mcp.tool()
def reset_database() -> str:
    """Wipes the database tables completely clear."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("TRUNCATE TABLE inventory;")
    conn.commit()
    conn.close()
    log_audit_event("Global Cloud Database Flush Triggered")
    return " SUCCESS: All remote matrix data rows reset to zero state fields."

if __name__ == "__main__":
    mcp.run()