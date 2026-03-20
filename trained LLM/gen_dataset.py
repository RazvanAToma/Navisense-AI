"""
generate_dataset.py
Generates randomized (system_prompt, user_message, expected_output) training pairs.
Run this to produce dataset/raw_dataset.jsonl
"""
import json
import random
import copy
from pathlib import Path
from prompts.system_prompt import build_system_prompt, build_user_message

# ------------------------------------------------------------------ #
#  Config                                                              #
# ------------------------------------------------------------------ #
SAMPLES_PER_TASK = 500
OUTPUT_PATH      = Path(__file__).parent / "dataset" / "raw_dataset.jsonl"

NODE_REGISTRY = {
    "PassThroughGate": {
        "script": "custom LLM/nodes/pass_through_gates.py",
        "description": "Aligns the boat perpendicular to the gate centerline and drives through the midpoint between the two buoys or towers. REQUIRES: both objects confirmed. Used for gate and towergate tasks. Do NOT use this for speedgate — use DriveSpeedgate instead."
    },
    "SearchPattern": {
        "script": "custom LLM/nodes/search_pattern.py",
        "description": "Executes a spiral or lawnmower search pattern centered on the given (x, y) coordinate. Use this when a required object is marked [estimated] from the world model. After SearchPattern completes, assume the object has been found and confirmed. Do NOT use this if the object is already marked [detected]."
    },
    "DriveSpeedgate": {
        "script": "custom LLM/nodes/drive_speedgate.py",
        "description": "Executes the full speedgate sequence as a single compound action: (1) enters through the gate (green+red buoy pair), (2) keeps the beacon on its left side while passing, (3) circles clockwise around the yellow buoy, (4) keeps the beacon on its left side again while returning, (5) exits back through the same gate. REQUIRES: gate (green+red buoy pair), beacon, and yellow buoy all confirmed. Do NOT split this into separate steps — it is one atomic action."
    },
    "ShootWater": {
        "script": "custom LLM/nodes/shoot_water.py",
        "description": "Shoots a stream of water for 10 seconds"
    },
    "HoldPosition": {
        "script": "custom LLM/nodes/hold_position.py",
        "description": "Stops the boat and holds its current position. Always the final step of any task."
    },
}

# Rule variants per task
GATE_RULES = [
    "a gate consists of one green and one red buoy no further apart than 10m. Pass between them.",
    "gate = green buoy + red buoy within 10m. The boat must pass through the midpoint.",
    "find a gate (one green, one red buoy) and pass through it. Max gate width: 10m.",
    "navigate through the gate formed by the green and red buoy pair.",
]

TOWERGATE_RULES = [
    "a towergate consists of one green tower and one red tower no further apart than 15m. Pass between them.",
    "towergate = green tower + red tower within 15m. The boat must pass through the midpoint.",
    "find a towergate (one green tower, one red tower) and pass through it. Max width: 15m.",
    "navigate through the towergate formed by the green and red tower pair.",
]

SPEEDGATE_RULES = [
    "find gate, beacon and yellow buoy. green_beacon = CCW around yellow buoy, red_beacon = CW around yellow buoy.",
    "speedgate: pass through gate (green+red buoy), then circle yellow buoy. beacon color sets direction: green=CCW, red=CW.",
    "gate + beacon + yellow buoy. Beacon color determines orbit direction around yellow buoy (green=CCW, red=CW).",
    "navigate speedgate: enter gate, read beacon color, orbit yellow buoy accordingly (green_beacon→CCW, red_beacon→CW).",
]

WATERDELIVERY_RULES = [
    "find the triangle boat and shoot water at it.",
    "locate the triangle marker and activate the water cannon.",
    "waterdelivery: move to the triangle target and shoot water for 10 seconds.",
]


# ------------------------------------------------------------------ #
#  World model generators                                              #
# ------------------------------------------------------------------ #

def rand_pos(min_val=5.0, max_val=100.0):
    return round(random.uniform(min_val, max_val), 1)

def rand_source():
    return random.choice(["estimated", "estimated", "detected"])  # bias toward estimated


def make_gate_world(id_offset=0):
    gid = id_offset + 1
    rid = id_offset + 2
    return {
        "objects": {
            f"green_buoy_{gid}": {"type": "green_buoy", "x": rand_pos(), "y": rand_pos(), "source": rand_source()},
            f"red_buoy_{rid}":   {"type": "red_buoy",   "x": rand_pos(), "y": rand_pos(), "source": rand_source()},
        }
    }, [f"green_buoy_{gid}", f"red_buoy_{rid}"]


def make_towergate_world(id_offset=0):
    gid = id_offset + 1
    rid = id_offset + 2
    return {
        "objects": {
            f"green_tower_{gid}": {"type": "green_tower", "x": rand_pos(), "y": rand_pos(), "source": rand_source()},
            f"red_tower_{rid}":   {"type": "red_tower",   "x": rand_pos(), "y": rand_pos(), "source": rand_source()},
        }
    }, [f"green_tower_{gid}", f"red_tower_{rid}"]


def make_speedgate_world(id_offset=0):
    gid  = id_offset + 1
    rid  = id_offset + 2
    bcol = random.choice(["green_beacon", "red_beacon"])
    bid  = id_offset + 3
    yid  = id_offset + 4
    return {
        "objects": {
            f"green_buoy_{gid}":  {"type": "green_buoy", "x": rand_pos(), "y": rand_pos(), "source": rand_source()},
            f"red_buoy_{rid}":    {"type": "red_buoy",   "x": rand_pos(), "y": rand_pos(), "source": rand_source()},
            f"{bcol}_{bid}":      {"type": bcol,         "x": rand_pos(), "y": rand_pos(), "source": rand_source()},
            f"yellow_buoy_{yid}": {"type": "yellow_buoy","x": rand_pos(), "y": rand_pos(), "source": rand_source()},
        }
    }, [f"green_buoy_{gid}", f"red_buoy_{rid}", f"{bcol}_{bid}", f"yellow_buoy_{yid}"], bcol


def make_waterdelivery_world(id_offset=0):
    tid = id_offset + 1
    return {
        "objects": {
            f"triangle_{tid}": {"type": "triangle", "x": rand_pos(), "y": rand_pos(), "source": rand_source()},
        }
    }, [f"triangle_{tid}"]


# ------------------------------------------------------------------ #
#  Expected output builders                                            #
# ------------------------------------------------------------------ #

def has_estimated(world_model, buoys):
    return any(
        world_model["objects"][b]["source"] == "estimated"
        for b in buoys if b in world_model["objects"]
    )


def build_passthrough_output(task_name, world_model, buoys):
    """Used for both gate and towergate — same node, different buoy types."""
    steps = []
    if has_estimated(world_model, buoys):
        estimated_ids = [b for b in buoys if world_model["objects"][b]["source"] == "estimated"]
        steps.append({"n": "SearchPattern", "i": {"ids": estimated_ids}})
        for b in buoys:
            world_model["objects"][b]["source"] = "detected"
    steps.append({"n": "PassThroughGate", "i": {"ids": buoys}})
    steps.append({"n": "HoldPosition",    "i": {"ids": []}})
    return {"ts": [{"t": task_name, "s": steps}]}


def build_speedgate_output(task_name, world_model, buoys):
    steps = []
    if has_estimated(world_model, buoys):
        estimated_ids = [b for b in buoys if world_model["objects"][b]["source"] == "estimated"]
        steps.append({"n": "SearchPattern", "i": {"ids": estimated_ids}})
        for b in buoys:
            world_model["objects"][b]["source"] = "detected"
    steps.append({"n": "DriveSpeedgate", "i": {"ids": buoys}})
    steps.append({"n": "HoldPosition",   "i": {"ids": []}})
    return {"ts": [{"t": task_name, "s": steps}]}


def build_waterdelivery_output(task_name, world_model, buoys):
    steps = []
    if has_estimated(world_model, buoys):
        estimated_ids = [b for b in buoys if world_model["objects"][b]["source"] == "estimated"]
        steps.append({"n": "SearchPattern", "i": {"ids": estimated_ids}})
        for b in buoys:
            world_model["objects"][b]["source"] = "detected"
    steps.append({"n": "ShootWater",   "i": {"ids": buoys}})
    steps.append({"n": "HoldPosition", "i": {"ids": []}})
    return {"ts": [{"t": task_name, "s": steps}]}


# ------------------------------------------------------------------ #
#  Main generation loop                                                #
# ------------------------------------------------------------------ #

def generate():
    OUTPUT_PATH.parent.mkdir(exist_ok=True)
    samples = []

    # --- Gate ---
    for _ in range(SAMPLES_PER_TASK):
        wm, buoys = make_gate_world(id_offset=random.randint(0, 50))
        wm_copy   = copy.deepcopy(wm)
        task = {"name": "gate", "rules": random.choice(GATE_RULES), "buoys": buoys}
        samples.append({
            "system": build_system_prompt(NODE_REGISTRY, wm, task),
            "input":  build_user_message(task),
            "output": json.dumps(build_passthrough_output("gate", wm_copy, buoys)),
        })

    # --- Towergate ---
    for _ in range(SAMPLES_PER_TASK):
        wm, buoys = make_towergate_world(id_offset=random.randint(0, 50))
        wm_copy   = copy.deepcopy(wm)
        task = {"name": "towergate", "rules": random.choice(TOWERGATE_RULES), "buoys": buoys}
        samples.append({
            "system": build_system_prompt(NODE_REGISTRY, wm, task),
            "input":  build_user_message(task),
            "output": json.dumps(build_passthrough_output("towergate", wm_copy, buoys)),
        })

    # --- Speedgate ---
    for _ in range(SAMPLES_PER_TASK):
        wm, buoys, _ = make_speedgate_world(id_offset=random.randint(0, 50))
        wm_copy      = copy.deepcopy(wm)
        task = {"name": "speedgate", "rules": random.choice(SPEEDGATE_RULES), "buoys": buoys}
        samples.append({
            "system": build_system_prompt(NODE_REGISTRY, wm, task),
            "input":  build_user_message(task),
            "output": json.dumps(build_speedgate_output("speedgate", wm_copy, buoys)),
        })

    # --- Waterdelivery ---
    for _ in range(SAMPLES_PER_TASK):
        wm, buoys = make_waterdelivery_world(id_offset=random.randint(0, 50))
        wm_copy   = copy.deepcopy(wm)
        task = {"name": "waterdelivery", "rules": random.choice(WATERDELIVERY_RULES), "buoys": buoys}
        samples.append({
            "system": build_system_prompt(NODE_REGISTRY, wm, task),
            "input":  build_user_message(task),
            "output": json.dumps(build_waterdelivery_output("waterdelivery", wm_copy, buoys)),
        })

    random.shuffle(samples)

    with open(OUTPUT_PATH, "w") as f:
        for s in samples:
            f.write(json.dumps(s) + "\n")

    print(f"Generated {len(samples)} samples → {OUTPUT_PATH}")


if __name__ == "__main__":
    generate()