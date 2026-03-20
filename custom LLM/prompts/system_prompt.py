def build_system_prompt(node_registry: dict, world_model_filtered: dict, task_name: str) -> str:
    from config.task_config import TASK_RULES
    rules = TASK_RULES[task_name]["rules"]

    node_descriptions = "\n".join(
        f"- \"{name}\": {info['description']}"
        for name, info in node_registry.items()
    )

    objects = world_model_filtered.get("objects", {})
    world_model_str = "\n".join(
        f"- {obj_id}: type={s['type']}, position=({s['x']}, {s['y']}) [{s['source']}]"
        for obj_id, s in objects.items()
    ) or "- No relevant objects detected"

    return f"""Output raw JSON only. No explanation, no markdown, no code fences.
Node names are case-sensitive strings. Copy them EXACTLY as listed. Do not paraphrase, shorten, or invent node names.
Every step must have exactly these fields: "n", "i".

[detected] = confirmed by sensors. Use directly.
[estimated] = position is approximate. You MUST run SearchPattern on every [estimated] object before using it in any other node. No exceptions.

The final step of EVERY task MUST always be HoldPosition with empty ids. No exceptions.

TASK: {task_name}
RULES: {rules}

NODE REGISTRY:
{node_descriptions}

WORLD MODEL (relevant objects only):
{world_model_str}
"""


def build_user_message(task_name: str) -> str:
    return f"""Plan the "{task_name}" task. Output a single JSON object. No explanation.

{{
  "ts": [
    {{
      "t": "{task_name}",
      "s": [
        {{
          "n": "NodeName from registry",
          "i": {{
            "ids": ["object_id_from_world_model"]
          }}
        }}
      ]
    }}
  ]
}}"""