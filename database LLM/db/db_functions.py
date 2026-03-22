import sqlite3
from pathlib import Path


# Maps competition_elements.id to element type
ELEMENT_IDS = {
    "green_buoy":   0,
    "red_buoy":     1,
    "yellow_buoy":  2,
    "black_buoy":   3,
    "green_beacon": 4,
    "red_beacon":   5,
    "red_tower":    6,
    "green_tower":  7,
    "triangle":     8,
    "plus":         9,
}


class DBfunctions:
    def __init__(self):
        self.DB_PATH = Path(__file__).parent / "database.db"
        self.conn    = sqlite3.connect(self.DB_PATH)
        self.cursor  = self.conn.cursor()

    # ------------------------------------------------------------------ #
    #  Generic                                                             #
    # ------------------------------------------------------------------ #

    def read_competition_elements(self):
        self.cursor.execute("SELECT * FROM competition_elements")
        return self.cursor.fetchall()

    def read_course_elements(self):
        self.cursor.execute("SELECT * FROM course_elements")
        return self.cursor.fetchall()

    def add_comp_element(self, comp_id, element_id, name, size, icon_path):
        self.cursor.execute(
            "INSERT INTO competition_elements (comp_id, element_id, name, size, icon_path) VALUES (?, ?, ?, ?, ?)",
            (comp_id, element_id, name, size, icon_path)
        )
        self.conn.commit()

    def add_course_element(self, course_id, element_id, x, y, rotation=0):
        self.cursor.execute(
            "INSERT INTO course_elements (course_id, element_id, x, y, rotation) VALUES (?, ?, ?, ?, ?)",
            (course_id, element_id, x, y, rotation)
        )
        self.conn.commit()

    def clear_db(self, table: str):
        if table in ("course_elements", "competition_elements"):
            self.cursor.execute(f"DELETE FROM {table}")
            self.conn.commit()

    # ------------------------------------------------------------------ #
    #  Task convenience functions                                          #
    #  Each returns the course element ids inserted so the caller can     #
    #  build mission.json buoy lists directly.                            #
    # ------------------------------------------------------------------ #

    def add_gate(self, course_id: int,
                 green_x: float, green_y: float,
                 red_x: float,   red_y: float,
                 rotation: float = 0) -> dict:
        """Insert a green + red buoy pair for a gate task."""
        self.add_course_element(course_id, ELEMENT_IDS["green_buoy"], green_x, green_y, rotation)
        green_id = self.cursor.lastrowid

        self.add_course_element(course_id, ELEMENT_IDS["red_buoy"], red_x, red_y, rotation)
        red_id = self.cursor.lastrowid

        return {
            "green_buoy": f"green_buoy_{green_id}",
            "red_buoy":   f"red_buoy_{red_id}",
        }

    def add_towergate(self, course_id: int,
                      green_x: float, green_y: float,
                      red_x: float,   red_y: float,
                      rotation: float = 0) -> dict:
        """Insert a green + red tower pair for a towergate task."""
        self.add_course_element(course_id, ELEMENT_IDS["green_tower"], green_x, green_y, rotation)
        green_id = self.cursor.lastrowid

        self.add_course_element(course_id, ELEMENT_IDS["red_tower"], red_x, red_y, rotation)
        red_id = self.cursor.lastrowid

        return {
            "green_tower": f"green_tower_{green_id}",
            "red_tower":   f"red_tower_{red_id}",
        }

    def add_speedgate(self, course_id: int,
                      green_x: float,  green_y: float,
                      red_x: float,    red_y: float,
                      beacon_x: float, beacon_y: float, beacon_color: str,
                      yellow_x: float, yellow_y: float,
                      rotation: float = 0) -> dict:
        """
        Insert all elements for a speedgate task.
        beacon_color: 'green_beacon' or 'red_beacon'
        """
        if beacon_color not in ("green_beacon", "red_beacon"):
            raise ValueError(f"beacon_color must be 'green_beacon' or 'red_beacon', got '{beacon_color}'")

        self.add_course_element(course_id, ELEMENT_IDS["green_buoy"], green_x, green_y, rotation)
        green_id = self.cursor.lastrowid

        self.add_course_element(course_id, ELEMENT_IDS["red_buoy"], red_x, red_y, rotation)
        red_id = self.cursor.lastrowid

        self.add_course_element(course_id, ELEMENT_IDS[beacon_color], beacon_x, beacon_y, rotation)
        beacon_id = self.cursor.lastrowid

        self.add_course_element(course_id, ELEMENT_IDS["yellow_buoy"], yellow_x, yellow_y, rotation)
        yellow_id = self.cursor.lastrowid

        return {
            "green_buoy":  f"green_buoy_{green_id}",
            "red_buoy":    f"red_buoy_{red_id}",
            beacon_color:  f"{beacon_color}_{beacon_id}",
            "yellow_buoy": f"yellow_buoy_{yellow_id}",
        }

    def add_waterdelivery(self, course_id: int,
                          triangle_x: float, triangle_y: float,
                          rotation: float = 0) -> dict:
        """Insert a triangle element for a waterdelivery task."""
        self.add_course_element(course_id, ELEMENT_IDS["triangle"], triangle_x, triangle_y, rotation)
        triangle_id = self.cursor.lastrowid

        return {
            "triangle": f"triangle_{triangle_id}",
        }