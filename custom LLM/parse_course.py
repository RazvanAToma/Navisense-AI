import sqlite3
import json
from pathlib import Path


DB_PATH = Path(__file__).parent / "db" / "database.db"
OUT_PATH = Path(__file__).parent / "config" / "world_model.json"


def parse_course_to_world_model(db_path: Path = DB_PATH, out_path: Path = OUT_PATH) -> dict:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
    SELECT
        ce.element_id,
        ce.x,
        ce.y,
        ce.rotation,
        comp.name
    FROM course_elements ce
    JOIN competition_elements comp ON ce.element_id = comp.element_id
    """)

    rows = cursor.fetchall()    
    conn.close()

    objects = {}
    for row in rows:
        element_id = row["element_id"]
        name = row["name"]
        x = row["x"]
        y = row["y"]

        # Derive type: lowercase, spaces to underscores
        obj_type = name.lower().replace(" ", "_")

        # Key: type + element_id (e.g. "green_buoy_5")
        obj_key = f"{obj_type}_{element_id}"

        objects[obj_key] = {
            "type": obj_type,
            "x": x,
            "y": y,
            "source": "estimated",
        }

    world_model = {"objects": objects}

    out_path.write_text(json.dumps(world_model, indent=2))
    print(f"Wrote {len(objects)} objects to {out_path}")

    return world_model


if __name__ == "__main__":
    parse_course_to_world_model()