import json
import time
import requests
from tqdm import tqdm

# ================== 配置 ==================
API_KEY = API_KEY
API_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"

MODEL_NAME = "qwen-plus"  # qwen-max / qwen-plus / qwen-turbo

INPUT_PATH = "/Users/ningjia/Downloads/chromeDownload/all_dialogues_assistant_thinking.jsonl"
OUTPUT_PATH = "/Users/ningjia/desktop/jiu_an/output_with_class.jsonl"

SLEEP_TIME = 3  # 防止限流


# ================== ENUM 定义 ==================
PRIMARY_CLASSES = [
    "HYPOGLYCEMIA",
    "HYPERGLYCEMIA",
    "EXERCISE_SAFETY",
    "DIET_MANAGEMENT",
    "MEDICATION_ADHERENCE",
    "GLUCOSE_MONITORING",
    "MEDICAL_VISIT",
    "SYMPTOM_ASSESSMENT",
    "EDUCATION",
    "BEHAVIOR_CHANGE",
    "EMOTIONAL_SUPPORT",
    "SAFETY_CRITICAL"
]

SECONDARY_CLASSES = [
    "EXERCISE_INDUCED",
    "FASTING_RELATED",
    "MEDICATION_RELATED",
    "POSTPRANDIAL",
    "GENERAL"
]

RISK_LEVELS = ["LOW", "MEDIUM", "HIGH"]


# ================== Prompt ==================
SYSTEM_PROMPT = """
你是一名医疗对话数据标注专家。
你的任务是对糖尿病患者与医疗助手的对话进行主题分类，而不是提供医疗建议。
""".strip()

USER_PROMPT_TEMPLATE = """
请根据以下完整对话内容，为该对话生成【结构化分类标签】。

【重要规则】
- 只能从给定的枚举值中选择，不得创造新标签
- primary_class 只能选 1 个
- supporting_classes 最多 3 个，可为空
- 如果不确定，选择最接近的枚举值

【PRIMARY_CLASS（只能选一个）】
{primary_classes}

【SECONDARY_CLASS（只能选一个）】
{secondary_classes}

【RISK_LEVEL（只能选一个）】
LOW / MEDIUM / HIGH

【输出格式（严格 JSON）】
{{
  "primary_class": "ENUM",
  "secondary_class": "ENUM",
  "supporting_classes": ["ENUM"],
  "risk_level": "ENUM"
}}

对话如下：
{dialogue}
""".strip()


# ================== DashScope 调用 ==================
def call_dashscope(dialogue_json: dict) -> dict:
    prompt = USER_PROMPT_TEMPLATE.format(
        primary_classes=", ".join(PRIMARY_CLASSES),
        secondary_classes=", ".join(SECONDARY_CLASSES),
        dialogue=json.dumps(dialogue_json, ensure_ascii=False)
    )

    payload = {
        "model": MODEL_NAME,
        "input": {
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ]
        },
        "parameters": {
            "temperature": 0.0
        }
    }

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    resp = requests.post(API_URL, headers=headers, json=payload, timeout=60)
    resp.raise_for_status()

    text = resp.json()["output"]["text"]
    return json.loads(text)


# ================== 输出校验 ==================
def validate_annotation(ann: dict):
    if ann["primary_class"] not in PRIMARY_CLASSES:
        raise ValueError(f"Invalid primary_class: {ann['primary_class']}")

    if ann["secondary_class"] not in SECONDARY_CLASSES:
        raise ValueError(f"Invalid secondary_class: {ann['secondary_class']}")

    if ann["risk_level"] not in RISK_LEVELS:
        raise ValueError(f"Invalid risk_level: {ann['risk_level']}")

    for c in ann.get("supporting_classes", []):
        if c not in PRIMARY_CLASSES:
            raise ValueError(f"Invalid supporting_class: {c}")


# ================== 主流程 ==================
def main():
    with open(INPUT_PATH, "r", encoding="utf-8") as fin, \
         open(OUTPUT_PATH, "w", encoding="utf-8") as fout:

        for line in tqdm(fin, desc="Classifying"):
            if not line.strip():
                continue

            data = json.loads(line)

            try:
                annotation = call_dashscope(data)
                validate_annotation(annotation)
            except Exception as e:
                # 出错时保留原数据，方便回溯
                data["class_annotation_error"] = str(e)
                fout.write(json.dumps(data, ensure_ascii=False) + "\n")
                continue

            # 生成 system prepend（可选，训练时可以不喂）
            system_tag = (
                f"【CLASS={annotation['primary_class']} | "
                f"SUB={annotation['secondary_class']} | "
                f"RISK={annotation['risk_level']}】"
            )

            data["class_annotation"] = annotation
            data["dialogue_history"] = [
                {"role": "system", "content": system_tag}
            ] + data.get("dialogue_history", [])

            fout.write(json.dumps(data, ensure_ascii=False) + "\n")
            time.sleep(SLEEP_TIME)


if __name__ == "__main__":
    main()
