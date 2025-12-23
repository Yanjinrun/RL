"""
配置文件
"""
import os

# API配置
API_KEY = os.getenv("QWEN_API_KEY", "")
API_BASE_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"

# 模型配置
DEFAULT_MODEL = "qwen-plus"
DEFAULT_TEMPERATURE = 0.7
DEFAULT_MAX_TOKENS = 2000

# 数据路径
DATA_DIR = "data"
PERSONA_DIR = os.path.join(DATA_DIR, "patient_structured")
OUTPUT_DIR = "output"

