import json
from ollama import chat
from pathlib import Path
from prompts.system_prompt import build_system_prompt
from prompts.user_prompt import build_user_prompt


class LLM():
    def __init__(self):
        # Root path
        self.base = Path(__file__).parent

        # Variable defs
        self.node_reg = {}
        self.navisense_output = {}
        self.running_order = {}


    def load_config(self):
        # Node Registry
        with open(self.base / "config" / "node_registry.json") as f:
            self.node_reg = json.load(f)

        # Navisense Output
        with open(self.base / "config" / "navisense_output.json") as f:
            self.navisense_output = json.load(f)

            for task in self.navisense_output['running_order']:
                self.task = task['rule_title']
                self.task_rules = task['rule_content']
                self.task_elements = task["elements"]

                print(f"{self.task}\n{self.task_rules}\n{self.task_elements}")


    def generate_prompts(self):
        self.system_prompt = build_system_prompt()
        self.user_prompt = build_user_prompt()


    # Prompting LLM
    def prompt_llm(self):
        self.response = chat(
            model="qwen2.5:7b",
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user",   "content": self.user_prompt},
            ],
        )





if __name__ == "__main__":
    llm = LLM()

    llm.load_config()