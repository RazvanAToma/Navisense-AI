import json
import math
from pathlib import Path

WORLD_MODEL_PATH = Path(__file__).parent / "config" / "world_model.json"


def load() -> dict:
    with open(WORLD_MODEL_PATH, "r") as f:
        return json.load(f)


def save(world_model: dict):
    with open(WORLD_MODEL_PATH, "w") as f:
        json.dump(world_model, f, indent=2)


def filter_for_task(world_model: dict, task_name: str) -> dict:
    from config.task_config import TASK_RULES
    required_types = TASK_RULES[task_name]["required_types"]
    filtered = {
        obj_id: state
        for obj_id, state in world_model["objects"].items()
        if state["type"] in required_types
    }
    return {"objects": filtered}


def update_object(world_model: dict, obj_id: str, x: float, y: float,
                  source: str = "detected", save_to_disk: bool = True):
    if obj_id not in world_model["objects"]:
        raise KeyError(f"Object '{obj_id}' not found in world model.")
    world_model["objects"][obj_id]["x"]      = x
    world_model["objects"][obj_id]["y"]      = y
    world_model["objects"][obj_id]["source"] = source
    if save_to_disk:
        save(world_model)


def update_boat(world_model: dict, x: float, y: float,
                heading: float, save_to_disk: bool = True):
    world_model["boat"]["x"]       = x
    world_model["boat"]["y"]       = y
    world_model["boat"]["heading"] = heading
    if save_to_disk:
        save(world_model)


def distance(world_model: dict, obj_a: str, obj_b: str) -> float:
    a = world_model["objects"][obj_a]
    b = world_model["objects"][obj_b]
    return math.sqrt((a["x"] - b["x"]) ** 2 + (a["y"] - b["y"]) ** 2)