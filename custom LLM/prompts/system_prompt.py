# prompts/system_prompt.py
# ──────────────────────────────────────────────────────────────
# This file is ONLY needed for the general (non-forked) LLM.
# When running the fine-tuned model, comment out the import of
# this file in main.py and replace build_system_prompt() with
# the minimal prompt below.
#
# MINIMAL PROMPT (for forked model):
#   "World model: {world_model_json}\nTasks: {task_list}"
# ──────────────────────────────────────────────────────────────


def build_system_prompt(node_registry: dict, world_model: dict) -> str:
    node_descriptions = "\n".join(
        f"- {name}: {info['description']}"
        for name, info in node_registry.items()
    )

    objects = world_model.get("objects", {})

    if objects:
        world_model_str = "\n".join(
            f"- {obj_id}: type={state['type']}, position=({state['x']}, {state['y']}) [{state['source']}]"
            for obj_id, state in objects.items()
        )
    else:
        world_model_str = "- No objects detected yet"

    return f"""You are a behavior tree assembler for a maritime autonomy system.
Output raw JSON only. No explanation, no markdown, no code fences.

Only use nodes from the provided registry. Never invent node names.
Every step must have exactly these fields: "node", "reason", "inputs".

[detected] means confirmed by sensors. Use directly. Do NOT search for it.
[estimated] means approximate position from operator. Must SearchPattern before using.

NODE REGISTRY:
{node_descriptions}

CURRENT WORLD MODEL:
Assume boat position is 0,0
Objects:
{world_model_str}

RULES:
- gate      = one green buoy + nearest red buoy, must be within 10m of each other
- towergate = one green tower + nearest red tower, must be within 15m of each other
- speedgate = gate + beacon + yellow buoy, all must be confirmed before DriveSpeedgate
- waterdelivery = triangle
- Buoys further than 10m apart form an invalid gate
- ALWAYS complete every task. Your output MUST contain a sequence for every task listed below. Stopping at any task but the last is a failure.
- Never compute coordinates yourself — always reference object IDs from the world model
- A buoy that appears in any earlier task's sequence is CONSUMED. Its object_id is permanently invalid for all subsequent tasks.
- A gate (buoy pair) used in any task is CONSUMED. That pair is permanently invalid for all subsequent tasks.
- If your output reuses a consumed object_id, the ENTIRE output is invalid and will be rejected by the parser. Do not attempt to justify reuse.
- Each task MUST use a distinct, non-consumed set of object_ids.

TASK REQUIREMENTS (in this exact order) — ALL MUST BE IN OUTPUT:
- Towergate: detect towergate → pass through towergate → stop
- Towergate: detect towergate → pass through towergate → stop
- Gate: detect gate → pass through gate → stop
- Gate: detect gate → pass through gate → stop
- Water Delivery: detect triangle → go to triangle → shoot water → stop
"""



def build_user_message() -> str:
    return """Your output MUST include a sequence for EVERY task in TASK REQUIREMENTS.
The structure below is a format example only — do not copy its node names or logic.

{
  "tasks": [
    {
      "task": "task_1",
      "sequence": [
        {
          "node": "NodeName",
          "reason": "why this node was chosen",
          "inputs": {
            "object_ids": ["id_from_world_model"]
          }
        }
      ]
    },
    {
      "task": "task_2",
      "sequence": [
        {
          "node": "NodeName",
          "reason": "why this node was chosen",
          "inputs": {
            "object_ids": ["id_from_world_model"]
          }
        }
      ]
    }
  ]
}"""