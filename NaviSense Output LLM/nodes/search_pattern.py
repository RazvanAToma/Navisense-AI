import sys
import json
from pathlib import Path

print("Executing search pattern...")

# IDs passed as CLI args: python search_pattern.py id1 id2 ...
ids = sys.argv[1:]

wm_path = Path(__file__).parent.parent / "config" / "world_model.json"
with open(wm_path) as f:
    wm = json.load(f)

for obj_id in ids:
    if obj_id in wm["objects"]:
        wm["objects"][obj_id]["source"] = "detected"
        print(f"  Marked {obj_id} as detected")
    else:
        print(f"  Warning: {obj_id} not found in world model")

with open(wm_path, "w") as f:
    json.dump(wm, f, indent=2)