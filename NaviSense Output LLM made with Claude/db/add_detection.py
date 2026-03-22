import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "register.db"

def add(element_type: int, x: float, y: float, confidence: float = 0.95):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO detections (element_type, x, y, confidence) VALUES (?, ?, ?, ?)",
        (element_type, x, y, confidence)
    )
    conn.commit()
    conn.close()
    print(f"Added detection: type={element_type}, x={x}, y={y}")

if __name__ == "__main__":
    # Element types: 0=green_buoy, 1=red_buoy, 2=yellow_buoy,
    #                3=green_tower, 4=red_tower, 5=black_buoy,
    #                6=plus_boat, 7=triangle_boat, 8=green_beacon, 9=red_beacon

    add(element_type=3, x=10.42, y=-6.28)   # green_tower_166 transformert
    add(element_type=4, x=10.47, y=4.69)    # red_tower_167 transformert
    #add(element_type=3, x=24.46, y=-5.99)   # green_tower_169 transformert
    #add(element_type=4, x=24.30, y=4.66)    # red_tower_168 transformert