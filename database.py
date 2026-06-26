import sqlite3
import datetime

DATABASE_FILE = "provenance_guard.db"

def init_db():
    """
    Initializes the local SQLite database file and builds the structural
    audit log schema if it doesn't already exist.
    """
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            content_id TEXT PRIMARY KEY,
            creator_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            text_content TEXT NOT NULL,
            attribution TEXT NOT NULL,
            confidence REAL NOT NULL,
            llm_score REAL NOT NULL,
            status TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def write_log_entry(content_id: str, creator_id: str, text_content: str, attribution: str, confidence: float, llm_score: float, status: str = "classified"):
    """
    Writes a beautifully structured row into the database audit ledger.
    """
    # Generates a standard UTC ISO timestamp
    current_time = datetime.datetime.utcnow().isoformat() + "Z"
    
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO audit_log (content_id, creator_id, timestamp, text_content, attribution, confidence, llm_score, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (content_id, creator_id, current_time, text_content, attribution, confidence, llm_score, status)) # <-- Added current_time & text_content here
    conn.commit()
    conn.close()

def read_all_logs():
    """
    Reads all past audit entries, converting row objects into dictionaries 
    so they can be easily serialized into JSON by Flask.
    """
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row  # This allows accessing columns by name like a dictionary
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM audit_log ORDER BY timestamp DESC")
    rows = cursor.fetchall()
    conn.close()
    
    # Transform rows to an array of standard Python dictionaries
    return [dict(row) for row in rows]