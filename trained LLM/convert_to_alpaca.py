"""
convert_to_alpaca.py
Converts dataset/raw_dataset.jsonl to Alpaca format for finetuning.
Output: dataset/alpaca_dataset.jsonl

Alpaca format:
{
  "instruction": <system prompt>,
  "input": <user message>,
  "output": <expected JSON output>
}
"""
import json
from pathlib import Path

INPUT_PATH  = Path(__file__).parent / "dataset" / "raw_dataset.jsonl"
OUTPUT_PATH = Path(__file__).parent / "dataset" / "alpaca_dataset.jsonl"


def convert():
    if not INPUT_PATH.exists():
        print(f"Input not found: {INPUT_PATH}")
        print("Run generate_dataset.py first.")
        return

    samples = []
    with open(INPUT_PATH) as f:
        for line in f:
            raw = json.loads(line.strip())
            samples.append({
                "instruction": raw["system"],
                "input":       raw["input"],
                "output":      raw["output"],
            })

    OUTPUT_PATH.parent.mkdir(exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        for s in samples:
            f.write(json.dumps(s) + "\n")

    print(f"Converted {len(samples)} samples → {OUTPUT_PATH}")


if __name__ == "__main__":
    convert()