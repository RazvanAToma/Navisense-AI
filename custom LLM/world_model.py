# world_model.py
# Handles loading, updating, and saving the world model at runtime.
# Called by main.py whenever new detections come in.

import json
import math
from pathlib import Path

WORLD_MODEL_PATH = Path("custom LLM/config/world_model.json")


def load() -> dict:
    with open(WORLD_MODEL_PATH, "r") as f:
        return json.load(f)


def save(world_model: dict):
    with open(WORLD_MODEL_PATH, "w") as f:
        json.dump(world_model, f, indent=2)


def update_object(world_model: dict, obj_id: str, x: float, y: float,
                  source: str = "detected", save_to_disk: bool = True):
    """
    Update or insert an object in the world model.
    Called when YOLO/LiDAR confirms or refines a detection.
    source should be 'detected' for sensor confirmations.
    """
    if obj_id not in world_model["objects"]:
        raise KeyError(f"Object '{obj_id}' not found in world model. Add it first.")

    world_model["objects"][obj_id]["x"]      = x
    world_model["objects"][obj_id]["y"]      = y
    world_model["objects"][obj_id]["source"] = source

    if save_to_disk:
        save(world_model)


def mark_used(world_model: dict, obj_id: str, save_to_disk: bool = True):
    """Mark an object as used so it cannot be reused in another task."""
    world_model["objects"][obj_id]["used"] = True
    if save_to_disk:
        save(world_model)


def update_boat(world_model: dict, x: float, y: float,
                heading: float, save_to_disk: bool = True):
    """Update boat position, called continuously from nav stack."""
    world_model["boat"]["x"]       = x
    world_model["boat"]["y"]       = y
    world_model["boat"]["heading"] = heading
    if save_to_disk:
        save(world_model)


def distance(world_model: dict, obj_a: str, obj_b: str) -> float:
    """Euclidean distance in meters between two objects."""
    a = world_model["objects"][obj_a]
    b = world_model["objects"][obj_b]
    return math.sqrt((a["x"] - b["x"]) ** 2 + (a["y"] - b["y"]) ** 2)