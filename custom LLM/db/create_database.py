import sqlite3

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

cursor.executescript("""
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS competition_elements (
    id          INTEGER PRIMARY KEY,
    comp_id     INTEGER NOT NULL,
    element_id  INTEGER NOT NULL,
    name        TEXT NOT NULL,
    size        TEXT NOT NULL,
    icon_path   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS course_elements (
    id          INTEGER PRIMARY KEY,
    course_id   INTEGER NOT NULL,
    element_id  INTEGER NOT NULL REFERENCES competition_elements(id),
    x           REAL NOT NULL,
    y           REAL NOT NULL,
    rotation    REAL NOT NULL DEFAULT 0
);
""")

conn.close()