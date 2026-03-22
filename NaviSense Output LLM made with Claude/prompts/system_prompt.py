def build_system_prompt(node_registry: dict, world_model: dict, task: dict) -> str:
    valid_nodes = ", ".join(f'"{n}"' for n in node_registry.keys())

    node_descriptions = "\n".join(
        f"- \"{name}\": {info['description']}"
        for name, info in node_registry.items()
    )

    objects = world_model.get("objects", {})
    world_model_str = "\n".join(
        f"- {obj_id}: type={s['type']}, position=({s['x']:.2f}, {s['y']:.2f}) [{s['source']}]"
        for obj_id, s in objects.items()
    ) or "- No relevant objects detected"

    return f"""Output raw JSON only. No explanation, no markdown, no code fences.
VALID NODE NAMES (copy exactly, case-sensitive): {valid_nodes}
Every step must have exactly these fields: "n", "i".
The "i" field MUST always be {{"ids": [...]}}. Never use x, y, or any other keys.
The final step of EVERY task MUST always be HoldPosition with empty ids. No exceptions.
[detected] = confirmed by sensors. Use directly.
[estimated] = approximate position. You MUST run SearchPattern on every [estimated] object before using it in any other node.
VALID OBJECT IDS (copy exactly): {", ".join(f'"{k}"' for k in objects.keys())}

TASK: {task['name']}
RULES:
{task['rules']}

NODE REGISTRY:
{node_descriptions}

WORLD MODEL (available objects only):
{world_model_str}
"""


def build_user_message(task: dict, buoy_list: list) -> str:
    ids_str = ", ".join(f'"{b}"' for b in buoy_list)
    return f"""Plan the next steps for the "{task['name']}" task using only available objects.
You MUST only use these exact object ids: {ids_str}. Copy them character by character.
If multiple objects are [estimated], group them ALL into one single SearchPattern step.
IMPORTANT: If the task contains multiple gate pairs, plan and execute ONE gate pair at a time.
A gate pair is one green + one red object. SearchPattern only the objects needed for the NEXT single gate pair, not all gates at once.
After completing one gate pair with HoldPosition, the next prompt will handle the remaining pairs.

The following is a FORMAT EXAMPLE ONLY. Do not copy node names or ids from it.
{{
  "ts": [
    {{
      "t": "task_name",
      "s": [
        {{
          "n": "NodeName",
          "i": {{"ids": ["object_id"]}}
        }}
      ]
    }}
  ]
}}"""
