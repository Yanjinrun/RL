import json
import os
from tqdm import tqdm

INPUT_PATH = "output_with_class.jsonl"
OUTPUT_DIR = "by_topic_and_risk"

os.makedirs(OUTPUT_DIR, exist_ok=True)
print(OUTPUT_DIR)
with open(INPUT_PATH, "r", encoding="utf-8") as fin:
    for line in tqdm(fin, desc="Splitting by topic and risk"):
        if not line.strip():
            continue

        data = json.loads(line)
        ann = data.get("class_annotation")
        if not ann:
            continue

        topic = ann["primary_class"]
        risk = ann["risk_level"]

        topic_dir = os.path.join(OUTPUT_DIR, topic)
        os.makedirs(topic_dir, exist_ok=True)

        out_path = os.path.join(topic_dir, f"{risk}.jsonl")
        with open(out_path, "a", encoding="utf-8") as fout:
            fout.write(json.dumps(data, ensure_ascii=False) + "\n")
