import json
import subprocess
from pathlib import Path
from ollama import chat

import world_model as wm
from prompts.system_prompt import build_system_prompt, build_user_message


# ── 1. LOAD CONFIG ─────────────────────────────────────────────
NODE_REGISTRY_PATH = Path("custom LLM/config/node_registry.json")

with open(NODE_REGISTRY_PATH, "r") as f:
    NODE_REGISTRY = json.load(f)

world_model = wm.load()


# ── 3. BUILD PROMPT ────────────────────────────────────────────
system_prompt = build_system_prompt(NODE_REGISTRY, world_model)
user_message  = build_user_message()


# ── 4. ASK LLM ─────────────────────────────────────────────────
response = chat(
    model="qwen2.5:14b",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user",   "content": user_message},
    ],
)


# ── 5. CLEAN + PARSE ───────────────────────────────────────────
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


# ── 6. VALIDATE ────────────────────────────────────────────────
for task in spec["tasks"]:
    for step in task["sequence"]:
        if step["node"] not in NODE_REGISTRY:
            print(f"Unknown node '{step['node']}' — rejected")
            exit(1)
        if "inputs" not in step:
            print(f"Missing inputs for step '{step['node']}' — rejected")
            exit(1)
        for obj_id in step["inputs"].get("object_ids", []):
            if obj_id not in world_model["objects"]:
                print(f"Unknown object '{obj_id}' referenced — rejected")
                exit(1)

print("Plan valid. Executing...\n")


'''
# ── 7. EXECUTE ─────────────────────────────────────────────────
for task in spec["tasks"]:
    print(f"=== {task['task'].upper()} ===")
    for step in task["sequence"]:
        node_id = step["node"]
        reason  = step.get("reason", "")
        inputs  = step.get("inputs", {})

        print(f">> Running: {node_id}")
        print(f"   Reason:  {reason}")
        print(f"   Inputs:  {inputs}")

        subprocess.run(["python", NODE_REGISTRY[node_id]["script"]], check=True)

        # Mark referenced objects as used
        for obj_id in inputs.get("object_ids", []):
            wm.mark_used(world_model, obj_id, save_to_disk=True)

        print(f">> {node_id} done\n")

print("Mission complete.")
'''