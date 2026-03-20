"""
finetune.py
Finetunes Qwen2.5-7B on the Navisense-AI Alpaca dataset using Unsloth.

Requirements:
    pip install unsloth datasets trl

Run:
    python finetune.py

Output:
    model/navisense-qwen2.5-7b  (merged model, ready for Ollama)
"""

from unsloth import FastLanguageModel
from datasets import load_dataset
from trl import SFTTrainer
from transformers import TrainingArguments
import torch

# ------------------------------------------------------------------ #
#  Config                                                              #
# ------------------------------------------------------------------ #
BASE_MODEL    = "unsloth/Qwen2.5-7B-Instruct-bnb-4bit"
DATASET_PATH  = "dataset/alpaca_dataset.jsonl"
OUTPUT_DIR    = "model/navisense-qwen2.5-7b"
MAX_SEQ_LEN   = 1024   # covers largest prompt comfortably
BATCH_SIZE    = 2
GRAD_ACCUM    = 4      # effective batch = 8
EPOCHS        = 3
LR            = 2e-4
LORA_RANK     = 16

# ------------------------------------------------------------------ #
#  Load model                                                          #
# ------------------------------------------------------------------ #
print("Loading model...")
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name     = BASE_MODEL,
    max_seq_length = MAX_SEQ_LEN,
    dtype          = None,   # auto-detect
    load_in_4bit   = True,
)

# ------------------------------------------------------------------ #
#  Apply LoRA                                                          #
# ------------------------------------------------------------------ #
model = FastLanguageModel.get_peft_model(
    model,
    r                   = LORA_RANK,
    target_modules      = ["q_proj", "k_proj", "v_proj", "o_proj",
                           "gate_proj", "up_proj", "down_proj"],
    lora_alpha          = LORA_RANK * 2,
    lora_dropout        = 0,
    bias                = "none",
    use_gradient_checkpointing = "unsloth",
    random_state        = 42,
)

# ------------------------------------------------------------------ #
#  Format dataset                                                      #
# ------------------------------------------------------------------ #
ALPACA_TEMPLATE = """Below is an instruction that describes a task, paired with an input that provides further context. Write a response that appropriately completes the request.

### Instruction:
{}

### Input:
{}

### Response:
{}"""

EOS = tokenizer.eos_token

def format_sample(sample):
    return {
        "text": ALPACA_TEMPLATE.format(
            sample["instruction"],
            sample["input"],
            sample["output"],
        ) + EOS
    }

print("Loading dataset...")
dataset = load_dataset("json", data_files=DATASET_PATH, split="train")
dataset = dataset.map(format_sample)
print(f"Dataset size: {len(dataset)} samples")

# ------------------------------------------------------------------ #
#  Train                                                               #
# ------------------------------------------------------------------ #
trainer = SFTTrainer(
    model        = model,
    tokenizer    = tokenizer,
    train_dataset = dataset,
    dataset_text_field = "text",
    max_seq_length = MAX_SEQ_LEN,
    args = TrainingArguments(
        per_device_train_batch_size  = BATCH_SIZE,
        gradient_accumulation_steps  = GRAD_ACCUM,
        num_train_epochs             = EPOCHS,
        learning_rate                = LR,
        fp16                         = not torch.cuda.is_bf16_supported(),
        bf16                         = torch.cuda.is_bf16_supported(),
        logging_steps                = 10,
        save_strategy                = "epoch",
        output_dir                   = OUTPUT_DIR,
        optim                        = "adamw_8bit",
        warmup_ratio                 = 0.05,
        lr_scheduler_type            = "cosine",
        report_to                    = "none",
    ),
)

print("Training...")
trainer.train()

# ------------------------------------------------------------------ #
#  Save merged model for Ollama                                        #
# ------------------------------------------------------------------ #
print("Saving merged model...")
model.save_pretrained_merged(
    OUTPUT_DIR,
    tokenizer,
    save_method = "merged_16bit",
)
print(f"Done. Model saved to {OUTPUT_DIR}")
print()
print("To use with Ollama:")
print(f"  ollama create navisense -f Modelfile")
print(f"  # Modelfile: FROM ./{OUTPUT_DIR}")