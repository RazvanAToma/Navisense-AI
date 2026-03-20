import sqlite3
import json
from pathlib import Path

# Transforming DB to JSON
DB_PATH  = Path(__file__).parent / "db" / "database.db"
OUT_PATH = Path(__file__).parent / "config" / "world_model.json"


def parse_course_to_world_model(db_path: Path = DB_PATH, out_path: Path = OUT_PATH) -> dict:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            ce.id,
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
        obj_type = row["name"].lower().replace(" ", "_")
        obj_key  = f"{obj_type}_{row['id']}"
        objects[obj_key] = {
            "type":   obj_type,
            "x":      row["x"],
            "y":      row["y"],
            "source": "estimated",
        }

    world_model = {"objects": objects}
    out_path.parent.mkdir(exist_ok=True)
    out_path.write_text(json.dumps(world_model, indent=2))
    print(f"Wrote {len(objects)} objects to {out_path}")
    return world_model


if __name__ == "__main__":
    parse_course_to_world_model()