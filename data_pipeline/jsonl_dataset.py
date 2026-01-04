import pandas as pd
from datasets import Dataset

# 1. Load your JSONL file
df = pd.read_json("all_dialogues_assistant_thinking.jsonl", lines=True)

# 2. Extract and format the dialogue
# If 'dialogue_history' already contains the full conversation (user + assistant):
def format_conversation(row):
    return {"messages": row["dialogue_history"]}

# If you want to include 'background_story' as a system prompt:
def format_with_context(row):
    messages = []
    # Add background info as a system message if relevant
    messages.append({"role": "system", "content": str(row["background_story"])})
    # Extend with the existing dialogue history
    messages.extend(row["dialogue_history"])
    return {"messages": messages}

# Apply the transformation
processed_data = df.apply(format_with_context, axis=1).tolist()

# 3. Create Hugging Face Dataset
dataset = Dataset.from_list(processed_data)
# check with print(dataset[0]) if you aren't sure it has worked
# 4. Save for training
# use absolute path on serverside
dataset.save_to_disk("./processed_medical_dataset")