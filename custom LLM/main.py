import json
import time
import subprocess
from pathlib import Path
from ollama import chat
import world_model as wm
from prompts.system_prompt import build_system_prompt, build_user_message


class Main:
    def __init__(self):
        self.NODE_REGISTRY = {}
        self.world_model   = {}
        self.system_prompt = ""
        self.user_message  = ""
        self.response      = None
        self.spec          = {}

    def load_config(self):
        NODE_REGISTRY_PATH = Path(__file__).parent / "config" / "node_registry.json"
        with open(NODE_REGISTRY_PATH, "r") as f:
            self.NODE_REGISTRY = json.load(f)
        self.world_model = wm.load()

    def generate_prompts(self, task_name: str):
        filtered_wm        = wm.filter_for_task(self.world_model, task_name)
        self.system_prompt = build_system_prompt(self.NODE_REGISTRY, filtered_wm, task_name)
        self.user_message  = build_user_message(task_name)

    def prompt_llm(self):
        self.response = chat(
            model="qwen2.5:7b",
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user",   "content": self.user_message},
            ],
        )

    def prompt_and_parse(self, retries: int = 3):
        for attempt in range(1, retries + 1):
            self.prompt_llm()
            raw = self.response.message.content.replace("```json", "").replace("```", "").strip()
            try:
                self.spec = json.loads(raw)
                out_path = Path(__file__).parent / "output" / "raw.json"
                out_path.parent.mkdir(exist_ok=True)
                out_path.write_text(json.dumps(self.spec, indent=2))
                return
            except json.JSONDecodeError as e:
                print(f"Invalid JSON (attempt {attempt}/{retries}): {e}")
        print("Failed after max retries.")
        exit(1)

    def validate(self):
        for task in self.spec["ts"]:
            for step in task["s"]:
                if step["n"] not in self.NODE_REGISTRY:
                    print(f"Unknown node '{step['n']}' — rejected")
                    exit(1)
                if "i" not in step:
                    print(f"Missing inputs for step '{step['n']}' — rejected")
                    exit(1)
                for obj_id in step["i"].get("ids", []):
                    if obj_id not in self.world_model["objects"]:
                        print(f"Unknown object '{obj_id}' referenced — rejected")
                        exit(1)
        print("Plan valid.")

    def execute_step(self, step: dict):
        node_id = step["n"]
        inputs  = step.get("i", {})
        ids     = inputs.get("ids", [])
        script  = Path(__file__).parent.parent / self.NODE_REGISTRY[node_id]["script"]
        print(f">> Running: {node_id}")
        print(f"   Inputs:  {inputs}")
        subprocess.run(["python", str(script)] + ids, check=True)
        print(f">> {node_id} done\n")

    def run(self, task_name: str):
        t = time.time
        print(f"[{t():.3f}] Loading config...")
        self.load_config()

        while True:
            print(f"[{t():.3f}] Generating prompts...")
            self.generate_prompts(task_name)
            print(f"[{t():.3f}] Prompting LLM...")
            self.prompt_and_parse()
            print(f"[{t():.3f}] Validating...")
            self.validate()

            steps = self.spec["ts"][0]["s"]

            # Check if task is complete
            if len(steps) == 1 and steps[0]["n"] == "HoldPosition":
                self.execute_step(steps[0])
                print("Task complete.")
                break

            # Execute steps until we hit a SearchPattern
            for step in steps:
                self.execute_step(step)
                if step["n"] == "SearchPattern":
                    print(f"[{t():.3f}] Re-loading world model after SearchPattern...")
                    self.world_model = wm.load()
                    break
            else:
                # Completed all steps without hitting SearchPattern — task done
                print("Task complete.")
                break


if __name__ == "__main__":
    main = Main()
    main.run("speedgate")