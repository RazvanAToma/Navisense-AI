import time
import json
import statistics
from pathlib import Path
from ollama import chat
import world_model as wm
from prompts.system_prompt import build_system_prompt, build_user_message

TASK_NAME = "gate"
RUNS      = 10


def single_run() -> float:
    NODE_REGISTRY_PATH = Path(__file__).parent / "config" / "node_registry.json"
    with open(NODE_REGISTRY_PATH, "r") as f:
        node_registry = json.load(f)

    world_model     = wm.load()
    filtered_wm     = wm.filter_for_task(world_model, TASK_NAME)
    system_prompt   = build_system_prompt(node_registry, filtered_wm, TASK_NAME)
    user_message    = build_user_message(TASK_NAME)

    t_start = time.perf_counter()
    chat(
        model="qwen2.5:7b",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_message},
        ],
        options={"num_ctx": 1024, "num_predict": 256}
    )
    return time.perf_counter() - t_start


def main():
    print(f"Benchmarking LLM response time — {RUNS} runs, task: {TASK_NAME}\n")

    NODE_REGISTRY_PATH = Path(__file__).parent / "config" / "node_registry.json"
    with open(NODE_REGISTRY_PATH, "r") as f:
        node_registry = json.load(f)
    world_model   = wm.load()
    filtered_wm   = wm.filter_for_task(world_model, TASK_NAME)
    system_prompt = build_system_prompt(node_registry, filtered_wm, TASK_NAME)
    user_message  = build_user_message(TASK_NAME)

    # Warm-up — laster modellen inn i VRAM, telles ikke
    print("  Warming up...", end=" ", flush=True)
    chat(model="qwen2.5:7b", messages=[{"role": "user", "content": "hi"}],
         options={"num_ctx": 1024, "num_predict": 1})
    print("done\n")

    times = []
    for i in range(1, RUNS + 1):
        print(f"  Run {i:2}/{RUNS}...", end=" ", flush=True)
        t_start = time.perf_counter()
        chat(
            model="qwen2.5:7b",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_message},
            ],
        )
        t = time.perf_counter() - t_start
        times.append(t)
        print(f"{t:.2f}s")


if __name__ == "__main__":
    main()