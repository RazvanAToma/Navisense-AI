import sqlite3

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

cursor.executescript("""
CREATE TABLE IF NOT EXISTS course_elements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id INTEGER,
    element_name VARCHAR,
    x REAL,
    y REAL,
    rotation REAL,
    FOREIGN KEY (course_id) REFERENCES courses(id)
); 
""")

conn.commit()
conn.close()