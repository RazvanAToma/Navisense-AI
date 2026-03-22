"""
create_db.py
Creates register.db with the detections table.
Run once to initialize the database.
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "register.db"


def create():
    conn = sqlite3.connect(DB_PATH)
    conn.executescript("""
        PRAGMA foreign_keys = ON;

        CREATE TABLE IF NOT EXISTS detections (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            element_type INTEGER NOT NULL,
            x            REAL NOT NULL,
            y            REAL NOT NULL,
            confidence   REAL,
            used         INTEGER DEFAULT 0,
            timestamp    DATETIME DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.close()
    print(f"Created {DB_PATH}")


if __name__ == "__main__":
    create()
