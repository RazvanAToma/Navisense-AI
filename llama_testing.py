import subprocess
import json
from ollama import chat

# ── 1. NODE REGISTRY ───────────────────────────────────────────
NODE_REGISTRY = {
    "MoveToPoint": {
        "script":      "nodes/moving_to_point.py",
        "description": "Drives the boat to a target coordinate"
    },
    "PassThroughGate": {
        "script":      "nodes/pass_through_gates.py",
        "description": "Aligns to and transits a detected gate"
    },
    "SearchPattern": {
        "script":      "nodes/search_pattern.py",
        "description": "Executes a search pattern to find a missing object"
    },
    "OrbitTarget": {
        "script":      "nodes/orbit_target.py",
        "description": "Orbits a detected object while scanning for a second object"
    },
    "HoldPosition": {
        "script":      "nodes/hold_position.py",
        "description": "Holds current position and waits"
    },
}

# ── 2. WORLD MODEL ─────────────────────────────────────────────
# source: "estimated" = placed in GUI, approximate position
# source: "detected"  = confirmed by YOLO/LiDAR, reliable position
WORLD_MODEL = {
    "green_buoy_1":    {"x": 10, "y": 20, "source": "detected"},
    "red_buoy_1":      {"x": 12, "y": 24, "source": "estimated"},
    "green_buoy_2":    {"x": 20, "y": 20, "source": "detected"},
    "red_buoy_2":      {"x": 22, "y": 24, "source": "estimated"},
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

custom_instructions = """
You are a behavior tree assembler for a maritime autonomy system.
Output raw JSON only. No explanation, no markdown, no code fences.
Only use nodes from the provided registry. Never invent node names.
Use the world model to make smart decisions — if a required object is missing, search for it first.
Always include a reasoning field explaining why each node was chosen.
The example below shows FORMAT ONLY. Base all logic solely on the actual world model and task requirements provided.
World model entries marked [estimated] are approximate GUI placements — navigate toward that area but search locally to confirm.
World model entries marked [detected] are confirmed by sensors — trust and use them directly."""

example_output = f"""
EXAMPLE FORMAT (structure only, do not copy the logic):
{{
  "task": "ExampleTask",
  "sequence": ["NodeA", "NodeB"],
  "reasoning": {{
    "NodeA": "why NodeA was chosen",
    "NodeB": "why NodeB was chosen"
  }}
}}

NODE REGISTRY:
{node_descriptions}

CURRENT WORLD MODEL (only detected objects are listed):
{world_model_str}

LOGIC:
gate = green buoy + nearest red buoy
one unit in x or y equals one meter in the real world.
check if buoys are further than 10m apart (if they are, gate is invalid)
once a buoy is used, it cannot be reused.
only look for one gate at a time, other gates are not relevant until the previous gate is passed.

TASK REQUIREMENTS:
detect gate, pass through gate, stop after passing gate.
then
detect gate, pass through gate, stop after passing gate.
end mission.

Based on what is detected, estimated, or missing, assemble a sequence to complete the task.

Output JSON now.
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

for node_id in spec["sequence"]:
    if node_id not in NODE_REGISTRY:
        print(f"Unknown node '{node_id}' — rejected")
        exit(1)

print(f"Task:     {spec['task']}")
print(f"Sequence: {spec['sequence']}")
print("Tree valid. Executing...\n")

# ── 6. EXECUTE ─────────────────────────────────────────────────
for node_id in spec["sequence"]:
    reason = spec.get("reasoning", {}).get(node_id, "")
    print(f">> Running: {node_id} — {reason}")
    subprocess.run(["python", NODE_REGISTRY[node_id]["script"]], check=True)
    print(f">> {node_id} done\n")

print("Mission complete.")