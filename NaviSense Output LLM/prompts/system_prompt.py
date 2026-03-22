def build_system_prompt(node_registry: dict, world_model_filtered: dict, task: dict) -> str:
    valid_nodes = ", ".join(f'"{n}"' for n in node_registry.keys())

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
VALID NODE NAMES (copy exactly, case-sensitive): {valid_nodes}
Every step must have exactly these fields: "n", "i".
The "i" field MUST always be "ids": [...]. Never use x, y, or any other keys.
[detected] = confirmed by sensors. Use directly.
[estimated] = approximate position. You MUST run SearchPattern on every [estimated] object before using it in any other node.

TASK: {task['name']}
RULES: {task['rules']}

NODE REGISTRY:
{node_descriptions}

WORLD MODEL (relevant objects only):
{world_model_str}
"""