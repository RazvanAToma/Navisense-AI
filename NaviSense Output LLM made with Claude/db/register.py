"""
register.py
Interface to register.db — polls detections and matches to GUI elements.
"""
import math
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "register.db"

ELEMENT_TYPE_MAP = {
    0:  "green_buoy",
    1:  "red_buoy",
    2:  "yellow_buoy",
    3:  "green_tower",
    4:  "red_tower",
    5:  "black_buoy",
    6:  "plus_boat",
    7:  "triangle_boat",
    8:  "green_beacon",
    9:  "red_beacon",
}


def poll(db_path: Path = DB_PATH) -> list:
    """Return all unused detections from register."""
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT id, element_type, x, y, confidence FROM detections WHERE used = 0"
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception:
        return []


def mark_used(detection_id: int, db_path: Path = DB_PATH):
    """Mark a detection as used."""
    try:
        conn = sqlite3.connect(db_path)
        conn.execute("UPDATE detections SET used = 1 WHERE id = ?", (detection_id,))
        conn.commit()
        conn.close()
    except Exception:
        pass


def _distance(x1, y1, x2, y2) -> float:
    return math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)


def match(detections: list, gui_elements: list, radius: float) -> dict:
    """
    Match detections to GUI elements by type + proximity.
    Only matches elements not already matched.
    Returns {course_element_id: detection_dict}
    """
    matched          = {}
    used_detections  = set()

    for el in gui_elements:
        if el["element_type"] < 0:
            continue
        el_type = ELEMENT_TYPE_MAP.get(el["element_type"])
        if not el_type:
            continue

        best   = None
        best_d = radius

        for det in detections:
            if det["id"] in used_detections:
                continue
            det_type = ELEMENT_TYPE_MAP.get(det["element_type"])
            if det_type != el_type:
                continue
            d = _distance(det["x"], det["y"], el["x"], el["y"])
            if d < best_d:
                best   = det
                best_d = d

        if best:
            matched[el["id"]] = best
            used_detections.add(best["id"])

    return matched
