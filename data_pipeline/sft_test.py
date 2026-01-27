from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    TrainingArguments
)
from trl import SFTTrainer
from datasets import load_from_disk
import torch
#use absolute path to model for serverside
#model path should include safe_tensors
model_path = "/home/elias/.cache/modelscope/hub/models/Qwen/Qwen3-4B-Thinking-2507"
dataset_path = "/home/elias/TEST_DATA"

# tokenizer
tokenizer = AutoTokenizer.from_pretrained(
    model_path,
    trust_remote_code=True
)
tokenizer.padding_side = "left"
tokenizer.pad_token = tokenizer.eos_token

# model (FULL fine-tuning)
model = AutoModelForCausalLM.from_pretrained(
    model_path,
    trust_remote_code=True,
    torch_dtype=torch.bfloat16,   # IMPORTANT on H20
    device_map="cuda"
)

# dataset
dataset = load_from_disk(dataset_path)

# training args
training_args = TrainingArguments(
    #use absolute path
    output_dir="./qwen3-full-sft",
    per_device_train_batch_size=1,
    gradient_accumulation_steps=4,
    num_train_epochs=1,           # start low
    learning_rate=1e-5,           # LOWER than LoRA
    lr_scheduler_type="cosine",
    warmup_ratio=0.03,
    bf16=True,
    logging_steps=10,
    save_steps=500, #change this parameter to increase number of checkpoints
    save_total_limit=2,
    report_to="none",
    remove_unused_columns=False,
    gradient_checkpointing=False, # H20 does not need it
)

trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=dataset
    # these two parameters are buggy
    # dataset_text_field="messages",
    # max_seq_length=8192
)

trainer.train()