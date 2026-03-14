import sqlite3
from pathlib import Path

class DBfunctions():
    def __init__(self):
        self.DB_PATH = Path(__file__).parent / "database.db"
        self.conn = sqlite3.connect(self.DB_PATH)
        
        self.cursor = self.conn.cursor()


    def read_db(self):
        query = f"SELECT * FROM course_elements"
        self.cursor.execute(query)
        db_contents = self.cursor.fetchall()

        return db_contents
    

    def add_element(self, course_id, element_name, x, y, rotation):
        query = "INSERT INTO course_elements (course_id, element_name, x, y, rotation) VALUES (?, ?, ?, ?, ?)"
        self.cursor.execute(query, (course_id, element_name, x, y, rotation))
        self.conn.commit()