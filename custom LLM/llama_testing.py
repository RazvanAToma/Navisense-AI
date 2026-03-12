import subprocess
import json
from ollama import chat

# ── 1. NODE REGISTRY ───────────────────────────────────────────
NODE_REGISTRY = {
    "MoveToPoint": {
        "script":      "LLM/nodes/moving_to_point.py",
        "description": (
            "Drives the boat in a straight line to a single (x, y) coordinate. "
            "Use this when the target position is already known and confirmed. "
            "Do NOT use this to search — use SearchPattern instead. "
            "Do NOT use this to pass through a gate — use PassThroughGate instead. "
            "Always precedes PassThroughGate or DriveSpeedgate when the boat needs "
            "to reposition before executing a task."
        )
    },
    "PassThroughGate": {
        "script":      "LLM/nodes/pass_through_gates.py",
        "description": (
            "Aligns the boat perpendicular to the gate centerline and drives through the midpoint between the green and red buoy pair. "
            "REQUIRES: both green and red buoy of this gate to be confirmed. "
            "Used for the standard gate task only. "
            "Do NOT use this for speedgate entry/exit — use DriveSpeedgate instead."
        )
    },
    "SearchPattern": {
        "script":      "LLM/nodes/search_pattern.py",
        "description": (
            "Executes a spiral or lawnmower search pattern centered on the given (x, y) coordinate. "
            "Use this when a required object is marked [estimated] from the world model. "
            "After SearchPattern completes, assume the object has been found and confirmed. "
            "Do NOT use this if the object is already marked [detected]."
        )
    },
    "HoldPosition": {
        "script":      "LLM/nodes/hold_position.py",
        "description": (
            "Stops the boat and holds its current position. "
            "Use this after completing a task as a hard stop before the next task begins, or to hold position during a task if something unexpected happens. "
            "Target should be the last known boat position or the position just after gate passage. "
        )
    },
    "DriveSpeedgate": {
        "script":      "LLM/nodes/drive_speedgate.py",
        "description": (
            "Executes the full speedgate sequence as a single compound action: "
            "(1) enters through the gate (green+red buoy pair), "
            "(2) keeps the beacon on its left side while passing, "
            "(3) circles clockwise around the yellow buoy, "
            "(4) keeps the beacon on its left side again while returning, "
            "(5) exits back through the same gate. "
            "REQUIRES: gate (green+red buoy pair), beacon, and yellow buoy all confirmed. "
            "Do NOT split this into separate steps — it is one atomic action."
        )
    },
}

# ── 2. WORLD MODEL ─────────────────────────────────────────────
# source: "estimated" = placed in GUI, approximate position
# source: "detected"  = confirmed by YOLO/LiDAR, reliable position
WORLD_MODEL = {
    # Gate
    "green_buoy_1": {"x": 10, "y": 20, "source": "estimated"},
    "red_buoy_1":   {"x": 10, "y": 24, "source": "estimated"},

    # Speedgate
    "green_buoy_2": {"x": 20, "y": 20, "source": "estimated"},
    "red_buoy_2":   {"x": 20, "y": 24, "source": "estimated"},
    "beacon_1":     {"x": 25, "y": 22, "source": "estimated"},
    "yellow_buoy_1":{"x": 35, "y": 22, "source": "estimated"},
}

# ── 3. BUILD PROMPT PARTS ──────────────────────────────────────
node_descriptions = "\n".join(
    f"- {name}: {info['description']}"
    for name, info in NODE_REGISTRY.items()
)

world_model_str = "\n".join(
    f"- {obj}: position=({state['x']}, {state['y']}) [{state['source']}]"
    for obj, state in WORLD_MODEL.items()
) if WORLD_MODEL else "- No objects detected yet"

custom_instructions = f"""
You are a behavior tree assembler for a maritime autonomy system.
Output raw JSON only. No explanation, no markdown, no code fences.

Only use nodes from the provided registry. Never invent node names.
Every step must have exactly three fields: "node", "reason", "target".

[detected] means confirmed by sensors. Use directly. Do NOT search for it.
[estimated] means approximate position from operator. Must SearchPattern before using.

NODE REGISTRY:
{node_descriptions}

CURRENT WORLD MODEL:
{world_model_str}

gate      = green buoy + nearest red buoy
speedgate = gate + beacon + yellow buoy
one unit in x or y equals one meter in the real world
buoys further than 10m apart form an invalid gate, check this before putting together two buoys
once a buoy is used it cannot be reused
once a gate is used it cannot be reused for another task
only look for one gate at a time
Complete one task fully before starting the next.


TASK REQUIREMENTS (in this exact order):
- task_1: detect gate → pass through gate → stop.
- task_2: detect speedgate → run speedgate → stop.


Based on what is detected, estimated, or missing, assemble a sequence to complete both tasks.
Output JSON now.
"""

example_output = f"""
EXAMPLE FORMAT (structure only, do not copy the logic):
{{
  "task": "ExampleTask",
  "sequence": [
    {{"node": "NodeA", "reason": "why NodeA was chosen here"}},
    {{"node": "NodeB", "reason": "why NodeB was chosen here"}},
    {{"node": "NodeA", "reason": "why NodeA is used again"}}
  ]
}}
"""

# ── 4. ASK LLM ─────────────────────────────────────────────────
response = chat(
    model='qwen2.5:14b',
    messages=[
        {'role': 'system', 'content': custom_instructions},
        {'role': 'user',   'content': example_output}
    ],
)

# ── 5. CLEAN + VALIDATE ────────────────────────────────────────
raw = response.message.content
raw = raw.replace("```json", "").replace("```", "").strip()

print("=== LLM OUTPUT ===")
print(raw)
print("==================\n")

try:
    spec = json.loads(raw)
except json.JSONDecodeError as e:
    print(f"Invalid JSON from LLM: {e}")
    exit(1)

# Validate all nodes exist and targets are present
for step in spec["sequence"]:
    if step["node"] not in NODE_REGISTRY:
        print(f"Unknown node '{step['node']}' — rejected")
        exit(1)
    if "target" not in step:
        print(f"Missing target for step '{step['node']}' — rejected")
        exit(1)

print(f"Task:     {spec['task']}")
print(f"Sequence: {[step['node'] for step in spec['sequence']]}")
print("Tree valid. Executing...\n")

# ── 6. EXECUTE ─────────────────────────────────────────────────
for step in spec["sequence"]:
    node_id = step["node"]
    reason  = step.get("reason", "")
    target  = step.get("target", {})
    print(f">> Running: {node_id}")
    print(f"   Reason:  {reason}")
    print(f"   Target:  x={target.get('x')}, y={target.get('y')}")
    subprocess.run(["python", NODE_REGISTRY[node_id]["script"]], check=True)
    print(f">> {node_id} done\n")

print("Mission complete.")