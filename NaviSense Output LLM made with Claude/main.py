"""
main.py
Navisense-AI mission planner.

Flow:
1. Load GUI output + node registry
2. Transform GUI coordinates to ROS2 frame
3. For each task in running_order:
   a. Poll detection register
   b. Match detections to task elements
   c. Prompt LLM with current state (detected/estimated)
   d. Execute steps one by one
   e. After each SearchPattern: poll until new elements matched
   f. Re-prompt LLM with updated state
   g. Never re-plan already-executed elements
4. Mark task elements as used when HoldPosition reached
"""
import json
import time
import subprocess
import sqlite3
from pathlib import Path
from ollama import chat
from db.register import poll, match, mark_used, ELEMENT_TYPE_MAP
from prompts.system_prompt import build_system_prompt, build_user_message

# ------------------------------------------------------------------ #
#  Config                                                              #
# ------------------------------------------------------------------ #
GUI_OUTPUT_PATH    = Path(__file__).parent / "config" / "navisense-output.json"
NODE_REGISTRY_PATH = Path(__file__).parent / "config" / "node_registry.json"
REGISTER_DB_PATH   = Path(__file__).parent / "db" / "register.db"
MATCH_RADIUS       = 3.0   # meters
POLL_INTERVAL      = 0.5   # seconds


# ------------------------------------------------------------------ #
#  Coordinate transformation                                           #
# ------------------------------------------------------------------ #

def get_boat_start_position() -> tuple:
    """
    TODO: Replace with ROS2 odometry fetch.
    Returns (x, y) in ROS2 frame.
    """
    return 0.0, 0.0


def transform_elements(course_elements: list, gui_start: tuple, ros2_start: tuple) -> dict:
    """
    Transform GUI coordinates to ROS2 frame.
    ros2_pos = element_gui - gui_start + ros2_start
    Returns {id: element_dict}
    """
    gx, gy = gui_start
    rx, ry = ros2_start
    result = {}
    for el in course_elements:
        result[el["id"]] = {
            **el,
            "x": round(el["x"] - gx + rx, 3),
            "y": round(el["y"] - gy + ry, 3),
        }
    return result


# ------------------------------------------------------------------ #
#  Task state                                                          #
# ------------------------------------------------------------------ #

class TaskState:
    """Tracks detection and execution state for a single task."""

    def __init__(self, task: dict, transformed_elements: dict):
        self.task     = task
        self.elements = transformed_elements  # all transformed course elements

        # All course element ids for this task (excluding infrastructure)
        self.element_ids = [
            el["course_element_id"]
            for el in task["elements"]
            if el["element_type"] >= 0
        ]

        self.matched  = {}   # {course_element_id: detection_dict}
        self.executed = set()  # course_element_ids already executed

    def update_matches(self, new_matches: dict):
        self.matched.update(new_matches)

    def get_available_elements(self) -> list:
        """Elements not yet executed."""
        return [
            self.elements[eid]
            for eid in self.element_ids
            if eid in self.elements and eid not in self.executed
        ]

    def build_world_model(self) -> dict:
        """Build world model for LLM — only available (non-executed) elements."""
        objects = {}
        for el in self.get_available_elements():
            el_type = ELEMENT_TYPE_MAP.get(el["element_type"], "unknown")
            obj_id  = f"{el_type}_{el['id']}"
            source  = "detected" if el["id"] in self.matched else "estimated"
            objects[obj_id] = {
                "type":   el_type,
                "x":      el["x"],
                "y":      el["y"],
                "source": source,
            }
        return {"objects": objects}

    def get_buoy_ids(self) -> list:
        return [
            f"{ELEMENT_TYPE_MAP.get(el['element_type'], 'unknown')}_{el['id']}"
            for el in self.get_available_elements()
        ]

    def mark_executed(self, obj_ids: list):
        """Mark course elements as executed based on obj_id strings."""
        for obj_id in obj_ids:
            # Extract course_element_id from obj_id string (e.g. "green_tower_166" → 166)
            try:
                eid = int(obj_id.split("_")[-1])
                if eid in self.element_ids:
                    self.executed.add(eid)
                    # Mark detection as used in register
                    if eid in self.matched:
                        mark_used(self.matched[eid]["id"], REGISTER_DB_PATH)
            except (ValueError, IndexError):
                pass

    def is_complete(self) -> bool:
        return len(self.executed) >= len(self.element_ids)


# ------------------------------------------------------------------ #
#  Main                                                                #
# ------------------------------------------------------------------ #

class Main:
    def __init__(self):
        self.NODE_REGISTRY       = {}
        self.gui_data            = {}
        self.transformed_elements = {}

    def load_config(self):
        with open(NODE_REGISTRY_PATH) as f:
            self.NODE_REGISTRY = json.load(f)
        with open(GUI_OUTPUT_PATH) as f:
            self.gui_data = json.load(f)
        
        # Clear register on startup
        conn = sqlite3.connect(REGISTER_DB_PATH)
        conn.execute("DELETE FROM detections")
        conn.commit()
        conn.close()
        print("Register cleared.")

    def setup_coordinates(self):
        start_el = next(
            (el for el in self.gui_data["course_elements"]
             if el["element_type"] == -1 and "start" in el["name"].lower()),
            None
        )
        gui_start  = (start_el["x"], start_el["y"]) if start_el else (0.0, 0.0)
        ros2_start = get_boat_start_position()

        print(f"GUI start:  {gui_start}")
        print(f"ROS2 start: {ros2_start}")

        self.transformed_elements = transform_elements(
            self.gui_data["course_elements"], gui_start, ros2_start
        )

    def prompt_and_parse(self, state: TaskState, retries: int = 3) -> dict:
        world_model = state.build_world_model()
        buoys       = state.get_buoy_ids()
        task_llm    = {
            "name":  state.task["rule_title"],
            "rules": state.task["rule_content"],
        }
        system_prompt = build_system_prompt(self.NODE_REGISTRY, world_model, task_llm)
        user_message  = build_user_message(task_llm, buoys)

        for attempt in range(1, retries + 1):
            response = chat(
                model="qwen2.5:7b",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user",   "content": user_message},
                ],
            )
            raw = response.message.content.replace("```json", "").replace("```", "").strip()
            try:
                spec = json.loads(raw)
                out  = Path(__file__).parent / "output" / "raw.json"
                out.parent.mkdir(exist_ok=True)
                out.write_text(json.dumps(spec, indent=2))
                return spec
            except json.JSONDecodeError as e:
                print(f"Invalid JSON (attempt {attempt}/{retries}): {e}")

        print("Failed after max retries.")
        exit(1)

    def validate(self, spec: dict, state: TaskState) -> bool:
        buoys = state.get_buoy_ids()
        for t in spec["ts"]:
            for step in t["s"]:
                if step["n"] not in self.NODE_REGISTRY:
                    print(f"Unknown node '{step['n']}' — rejected")
                    return False
                if "i" not in step:
                    print(f"Missing inputs for '{step['n']}' — rejected")
                    return False
                for obj_id in step["i"].get("ids", []):
                    if obj_id not in buoys:
                        print(f"Object '{obj_id}' not valid for this task — rejected")
                        return False
        return True

    def execute_step(self, step: dict):
        node_id = step["n"]
        ids     = step.get("i", {}).get("ids", [])
        script  = Path(__file__).parent.parent / self.NODE_REGISTRY[node_id]["script"]
        print(f">> Running: {node_id}")
        print(f"   Inputs:  {ids}")
        subprocess.run(["python", str(script)] + ids, check=True)
        print(f">> {node_id} done\n")

    def poll_until_matched(self, state: TaskState, needed_obj_ids: set):
        print(f"   Waiting for: {needed_obj_ids}")
        already_matched = set(
            f"{ELEMENT_TYPE_MAP.get(self.transformed_elements[eid]['element_type'], 'unknown')}_{eid}"
            for eid in state.matched
        )
        while True:
            detections  = poll(REGISTER_DB_PATH)
            new_matches = match(detections, state.get_available_elements(), MATCH_RADIUS)
            state.update_matches(new_matches)

            now_matched = set(
                f"{ELEMENT_TYPE_MAP.get(self.transformed_elements[eid]['element_type'], 'unknown')}_{eid}"
                for eid in state.matched
            )

            newly_matched = now_matched - already_matched
            if newly_matched:
                print(f"   Matched: {newly_matched} — re-prompting LLM")
                return

            time.sleep(POLL_INTERVAL)

    def run_task(self, task: dict):
        t = time.time
        print(f"\n{'='*40}")
        print(f"  TASK: {task['rule_title'].upper()}")
        print(f"{'='*40}")

        state = TaskState(task, self.transformed_elements)

        while not state.is_complete():
            # Poll for new detections
            detections  = poll(REGISTER_DB_PATH)
            new_matches = match(detections, state.get_available_elements(), MATCH_RADIUS)
            state.update_matches(new_matches)

            print(f"[{t():.3f}] Prompting LLM...")
            spec = self.prompt_and_parse(state)

            if not self.validate(spec, state):
                print("Validation failed — re-prompting...")
                continue

            print("Plan valid.")
            steps = spec["ts"][0]["s"]

            for step in steps:
                self.execute_step(step)

                if step["n"] == "HoldPosition":
                    # Mark all executed elements from this plan
                    for s in steps:
                        state.mark_executed(s["i"].get("ids", []))
                    print(f"Task '{task['rule_title']}' complete.")
                    return

                if step["n"] == "SearchPattern":
                    # Mark searched elements as executed (they'll be re-added as detected)
                    ids_searched = set(step["i"].get("ids", []))
                    # Poll until all searched elements are matched as detected
                    self.poll_until_matched(state, ids_searched)
                    break  # Re-prompt with updated state

                # Mark executed elements after each non-search step
                state.mark_executed(step["i"].get("ids", []))

    def run(self):
        t = time.time
        print(f"[{t():.3f}] Loading config...")
        self.load_config()
        print(f"[{t():.3f}] Setting up coordinates...")
        self.setup_coordinates()

        tasks = sorted(self.gui_data["running_order"], key=lambda x: x["position"])
        print(f"[{t():.3f}] Mission loaded — {len(tasks)} task(s): {[t_['rule_title'] for t_ in tasks]}")

        for task in tasks:
            self.run_task(task)

        print("\nMission complete.")


if __name__ == "__main__":
    main = Main()
    main.run()
