import json
import subprocess
from pathlib import Path
from ollama import chat
from db.db_functions import DBfunctions

import world_model as wm
from prompts.system_prompt import build_system_prompt, build_user_message

class Main():
    def __init__(self):
        self.db_functions = DBfunctions()

    def load_config(self):
        NODE_REGISTRY_PATH = Path("custom LLM/config/node_registry.json")

        with open(NODE_REGISTRY_PATH, "r") as f:
            self.NODE_REGISTRY = json.load(f)

        self.world_model = wm.load()

    def generate_prompts(self):
        self.system_prompt = build_system_prompt(self.NODE_REGISTRY, self.world_model)
        self.user_message  = build_user_message() 

    def prompt_llm(self):
        self.response = chat(
            model="qwen2.5:14b",
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user",   "content": self.user_message},
            ],
        )

    def parse_prompt(self):
        raw = self.response.message.content
        raw = raw.replace("```json", "").replace("```", "").strip()

        try:
            self.spec = json.loads(raw)
        except json.JSONDecodeError as e:
            print(f"Invalid JSON from LLM: {e}")
            exit(1)

        with open("custom LLM/output/raw.json", "w") as f:
            json.dump(self.spec, f, indent=2)

    def validate(self):
        for task in self.spec["tasks"]:
            for step in task["sequence"]:
                if step["node"] not in self.NODE_REGISTRY:
                    print(f"Unknown node '{step['node']}' — rejected")
                    exit(1)
                if "inputs" not in step:
                    print(f"Missing inputs for step '{step['node']}' — rejected")
                    exit(1)
                for obj_id in step["inputs"].get("object_ids", []):
                    if obj_id not in self.world_model["objects"]:
                        print(f"Unknown object '{obj_id}' referenced — rejected")
                        exit(1)

        print("Plan valid.")

    def execute(self):
        for task in self.spec["tasks"]:
            print(f"=== {task['task'].upper()} ===")
            for step in task["sequence"]:
                node_id = step["node"]
                reason  = step.get("reason", "")
                inputs  = step.get("inputs", {})

                print(f">> Running: {node_id}")
                print(f"   Reason:  {reason}")
                print(f"   Inputs:  {inputs}")

                subprocess.run(["python", self.NODE_REGISTRY[node_id]["script"]], check=True)

                # Mark referenced objects as used
                for obj_id in inputs.get("object_ids", []):
                    wm.mark_used(self.world_model, obj_id, save_to_disk=True)

                print(f">> {node_id} done\n")

        print("Mission complete.")

    def run(self):
        self.load_config()
        self.generate_prompts()
        self.prompt_llm()
        self.parse_prompt()
        self.validate()



if __name__ == "__main__":
    main = Main()

    #main.run()

    db_functions = DBfunctions()

    