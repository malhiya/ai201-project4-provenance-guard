import sqlite3
import datetime

DATABASE_FILE = "provenance_guard.db"

def init_db():
    """Initializes schema and ensures all fine-grained logging columns are ready."""
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
            stylometric_score REAL NOT NULL,
            status TEXT NOT NULL,
            appeal_reasoning TEXT
        )
    """)
    conn.commit()
    conn.close()

def write_log_entry(content_id: str, creator_id: str, text_content: str, attribution: str, confidence: float, llm_score: float, stylometric_score: float, status: str = "completed"):
    current_time = datetime.datetime.utcnow().isoformat() + "Z"
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO audit_log (content_id, creator_id, timestamp, text_content, attribution, confidence, llm_score, stylometric_score, status, appeal_reasoning)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, NULL)
    """, (content_id, creator_id, current_time, text_content, attribution, confidence, llm_score, stylometric_score, status))
    conn.commit()
    conn.close()

def get_log_by_id(content_id: str):
    """Fetches a single tracking transaction to allow state machine validation check boundaries."""
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM audit_log WHERE content_id = ?", (content_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def update_to_under_review(content_id: str, reason: str):
    """Mutates lifecycle state cleanly without touching historically frozen metric evaluations."""
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE audit_log 
        SET status = 'under_review', appeal_reasoning = ? 
        WHERE content_id = ?
    """, (reason, content_id))
    conn.commit()
    conn.close()

def read_all_logs():
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row  
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM audit_log ORDER BY timestamp DESC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]