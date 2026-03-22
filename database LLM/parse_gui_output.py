"""
parse_gui_output.py
Parses the GUI output JSON into:
  - config/world_model.json  (all course elements, all estimated)
  - config/mission.json      (tasks in running order with rules and buoy ids)

Usage:
    python parse_gui_output.py
    python parse_gui_output.py path/to/custom_output.json
"""
import json
import sys
from pathlib import Path

GUI_OUTPUT_PATH  = Path(__file__).parent / "config" / "navisense-output.json"
WORLD_MODEL_PATH = Path(__file__).parent / "config" / "world_model.json"
MISSION_PATH     = Path(__file__).parent / "config" / "mission.json"

# element_type to snake_case type name
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
    -1: "infrastructure",
}


def parse(input_path: Path = GUI_OUTPUT_PATH):
    with open(input_path) as f:
        data = json.load(f)

    # ------------------------------------------------------------------ #
    #  World model — all course elements, all estimated                   #
    # ------------------------------------------------------------------ #
    objects = {}
    for ce in data["course_elements"]:
        element_type = ce["element_type"]

        # Use descriptive name for infrastructure (-1) types
        if element_type == -1:
            type_name = ce["name"].lower().replace(" ", "_").replace("(", "").replace(")", "")
        else:
            type_name = ELEMENT_TYPE_MAP.get(element_type, f"unknown_{element_type}")

        obj_key = f"{type_name}_{ce['id']}"
        objects[obj_key] = {
            "type":   type_name,
            "x":      ce["x"],
            "y":      ce["y"],
            "source": "estimated",
        }

    world_model = {"objects": objects}
    WORLD_MODEL_PATH.parent.mkdir(exist_ok=True)
    WORLD_MODEL_PATH.write_text(json.dumps(world_model, indent=2))
    print(f"Wrote {len(objects)} objects to {WORLD_MODEL_PATH}")

    # ------------------------------------------------------------------ #
    #  Mission — running order tasks                                       #
    # ------------------------------------------------------------------ #
    tasks = []
    for part in sorted(data["running_order"], key=lambda p: p["position"]):
        # Filter out infrastructure elements (-1) from buoy list
        buoys = [
            f"{ELEMENT_TYPE_MAP.get(el['element_type'], 'unknown')}_{el['course_element_id']}"
            for el in part["elements"]
            if el["element_type"] != -1
        ]

        tasks.append({
            "name":  part["rule_title"],
            "rules": part["rule_content"],
            "buoys": buoys,
        })

    mission = {"tasks": tasks}
    MISSION_PATH.write_text(json.dumps(mission, indent=2))
    print(f"Wrote {len(tasks)} tasks to {MISSION_PATH}")

    return world_model, mission


if __name__ == "__main__":
    input_path = Path(sys.argv[1]) if len(sys.argv) > 1 else GUI_OUTPUT_PATH
    parse(input_path)