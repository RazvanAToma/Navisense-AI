import sqlite3
from pathlib import Path

class DBfunctions():
    def __init__(self):
        self.DB_PATH = Path(__file__).parent / "database.db"
        self.conn = sqlite3.connect(self.DB_PATH)
        
        self.cursor = self.conn.cursor()


    def read_course_elements(self):
        query = f"SELECT * FROM course_elements"
        self.cursor.execute(query)
        db_contents = self.cursor.fetchall()

        return db_contents
    
    def read_course_elements(self):
        query = f"SELECT * FROM competition_elements"
        self.cursor.execute(query)
        db_contents = self.cursor.fetchall()

        return db_contents
    
    def add_comp_element(self, comp_id, element_id, name, size, icon_path):
        query = f"INSERT INTO competition_elements (comp_id, element_id, name, size, icon_path) VALUES (?, ?, ?, ?, ?)"
        self.cursor.execute(query, (comp_id, element_id, name, size, icon_path))
        self.conn.commit()

    def add_course_element(self, course_id, element_id, x, y, rotation):
        query = f"INSERT INTO course_elements (course_id, element_id, x, y, rotation) VALUES (?, ?, ?, ?, ?)"
        self.cursor.execute(query, (course_id, element_id, x, y, rotation))
        self.conn.commit()

    def clear_db(self, table):
        if table == "course_elements":
            query = f"DELETE FROM course_elements"
            self.cursor.execute(query)
            self.conn.commit()
        elif table == "competition_elements":
            query = f"DELETE FROM competition_elements"
            self.cursor.execute(query)
            self.conn.commit()