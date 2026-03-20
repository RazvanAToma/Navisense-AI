import json
import time
import subprocess
from pathlib import Path
from ollama import chat
import world_model as wm
from prompts.system_prompt import build_system_prompt, build_user_message
from db.db_functions import DBfunctions
from parse_course import parse_course_to_world_model


class Main:
    def __init__(self):
        # Initializing variables
        self.NODE_REGISTRY = {}
        self.world_model   = {}
        self.mission       = {}
        self.system_prompt = ""
        self.user_message  = ""
        self.response      = None
        self.spec          = {}

    # Loading node_registry & mission
    def load_config(self):
        base = Path(__file__).parent

        # Node Registry
        with open(base / "config" / "node_registry.json") as f:
            self.NODE_REGISTRY = json.load(f)

        # Mission
        with open(base / "config" / "mission.json") as f:
            self.mission = json.load(f)
        self.world_model = wm.load()


    # Generate system & user prompts for LLM
    def generate_prompts(self, task: dict):
        # Filtering world_model, only selecting buoys as per specified in the rules from NaviSense.
        filtered_wm        = wm.filter_for_task(self.world_model, task["buoys"])

        # Building prompts
        self.system_prompt = build_system_prompt(self.NODE_REGISTRY, filtered_wm, task)
        self.user_message  = build_user_message(task)


    # Prompting LLM
    def prompt_llm(self):
        self.response = chat(
            model="qwen2.5:7b",
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user",   "content": self.user_message},
            ],
        )


    # Prompting LLM, removing unnecessary chars, and checking json validity, retrying max 3 times.
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

    # Checking 
    def validate(self, task: dict):
        # For task in tasks from raw json output
        for t in self.spec["ts"]:
            # For step (node) in task steps (task nodes)
            for step in t["s"]:
                # If node doesn't exist
                if step["n"] not in self.NODE_REGISTRY:
                    print(f"Unknown node '{step['n']}' — rejected")
                    exit(1)

                # If input dict doesn't exist
                if "i" not in step:
                    print(f"Missing inputs for step '{step['n']}' — rejected")
                    exit(1)

                # If any object doesn't exist
                for obj_id in step["i"].get("ids", []):
                    # Not in world model
                    if obj_id not in self.world_model["objects"]:
                        print(f"Unknown object '{obj_id}' referenced — rejected")
                        exit(1)
                    
                    # Not relevant to task
                    if obj_id not in task["buoys"]:
                        print(f"Object '{obj_id}' not assigned to this task — rejected")
                        exit(1)

        print("Plan valid.")


    # Executing nodes
    def execute_step(self, step: dict):
        node_id = step["n"]
        inputs  = step.get("i", {})
        ids     = inputs.get("ids", [])
        script  = Path(__file__).parent.parent / self.NODE_REGISTRY[node_id]["script"]
        print(f">> Running: {node_id}")
        print(f"   Inputs:  {inputs}")
        subprocess.run(["python", str(script)] + ids, check=True)
        print(f">> {node_id} done\n")


    def run_task(self, task: dict):
        # Small header
        t = time.time
        print(f"\n{'='*40}")
        print(f"  TASK: {task['name'].upper()}")
        print(f"{'='*40}")

        while True:
            print(f"[{t():.3f}] Generating prompts...")
            self.generate_prompts(task)
            print(f"[{t():.3f}] Prompting LLM...")
            self.prompt_and_parse()
            print(f"[{t():.3f}] Validating...")
            self.validate(task)

            steps = self.spec["ts"][0]["s"]

            # Check if task is complete, if last task is HoldPosition
            if len(steps) == 1 and steps[0]["n"] == "HoldPosition":
                self.execute_step(steps[0])
                print(f"Task '{task['name']}' complete.")
                break

            # Execute steps until we hit a SearchPattern
            for step in steps:
                self.execute_step(step)
                if step["n"] == "SearchPattern":
                    print(f"[{t():.3f}] Re-loading world model after SearchPattern...")
                    self.world_model = wm.load()
                    break
            else:
                print(f"Task '{task['name']}' complete.")
                break

    # All together now
    def run(self):
        t = time.time
        print(f"[{t():.3f}] Loading config...")
        self.load_config()

        tasks = self.mission["tasks"]
        print(f"[{t():.3f}] Mission loaded — {len(tasks)} task(s): {[t_['name'] for t_ in tasks]}")

        for task in tasks:
            self.run_task(task)

        print("\nMission complete.")


if __name__ == "__main__":
    main = Main()
    
    parse_course_to_world_model()

    main.run()

    """
    db = DBfunctions()
    db.clear_db("course_elements")
    gate = db.add_gate(course_id=1, green_x=20, green_y=20, red_x=30, red_y=20)
    speedgate = db.add_speedgate(
        course_id=1,
        green_x=60,  green_y=20,
        red_x=70,    red_y=20,
        beacon_x=65, beacon_y=10, beacon_color="green_beacon",
        yellow_x=65, yellow_y=35,
    )

    tower_gate = db.add_towergate(course_id=1, green_x=100, green_y=20, red_x=110, red_y=20)
    tower_gate = db.add_towergate(course_id=1, green_x=100, green_y=40, red_x=110, red_y=40)
    """