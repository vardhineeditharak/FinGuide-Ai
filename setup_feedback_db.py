import os
import sqlite3

DB_DIR = os.path.join(os.path.dirname(__file__), "vectorstore")
SQLITE_DB_PATH = os.path.join(DB_DIR, "embeddings.db")

def init_feedback_db():
    if not os.path.exists(DB_DIR):
        os.makedirs(DB_DIR)
        
    print(f"Connecting to SQLite database: {SQLITE_DB_PATH}")
    conn = sqlite3.connect(SQLITE_DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            query TEXT NOT NULL,
            answer TEXT NOT NULL,
            rating TEXT NOT NULL, -- 'up' or 'down'
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    conn.commit()
    print("Feedback table initialized successfully.")
    conn.close()

if __name__ == "__main__":
    init_feedback_db()
