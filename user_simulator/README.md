# 用户模拟器

基于强化学习的多轮对话策略优化项目 - 用户模拟器部分

## 功能模块

1. **患者画像生成** (`persona_generator.py`): 根据规则拼接生成的用户画像进行重写和扩写
2. **背景生成** (`background_generator.py`): 生成患者24小时生活状态
3. **故事生成** (`story_generator.py`): 根据主题和患者特点生成故事背景
4. **对话生成** (`dialogue_generator.py`): 生成患者与照护师的多轮对话

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

### 1. 基本使用

```bash
# 生成完整对话（默认模式）
python main.py --mode conversation --topic "对话主题" --max-turns 10
#生成完整的对话（随机生成对话主题，不限制对话次数）
python main_random_topic.py   

# 只生成患者画像 data文件夹被gitignore了，需要自己创建并下载一下
python main.py --mode persona --persona-file data/patient_structured/patient_structured_50_desensitize.json

# 只生成24小时生活状态
python main.py --mode background --topic "对话主题"

# 只生成故事背景
python main.py --mode story --topic "对话主题"

# 只生成一轮对话
python main.py --mode dialogue --topic "对话主题"
```

### 2. 使用自定义API密钥

```bash
python main.py --api-key "your-api-key" --mode conversation
```

### 3. 保存结果

```bash
python main.py --mode conversation --output output/conversation.json
```

## 配置

在 `config.py` 中可以修改：
- API密钥（默认从环境变量 `QWEN_API_KEY` 读取）
- API基础URL
- 默认模型参数

## 代码结构

```
user_simulator/
├── scripts/
│   ├── __init__.py
│   ├── api_client.py          # API客户端
│   ├── persona_generator.py   # 患者画像生成
│   ├── background_generator_thinking.py # 背景生成
│   ├── story_generator.py     # 故事生成
│   └── dialogue_generator.py  # 对话生成
├── config.py                  # 配置文件
├── main.py                    # 主程序入口
├── requirements.txt           # 依赖包
└── README.md                  # 说明文档
```

## API说明

### QwenAPIClient

阿里百炼Qwen系列模型API客户端

```python
from scripts import QwenAPIClient

client = QwenAPIClient(api_key="your-api-key")
result = client.call(prompt="你的提示词", model="qwen-plus")
```

### PersonaGenerator

患者画像生成器

```python
from scripts import PersonaGenerator, QwenAPIClient

api_client = QwenAPIClient(api_key="your-api-key")
generator = PersonaGenerator(api_client)
persona_text = generator.generate_persona(raw_persona_dict)
```

### BackgroundGenerator

背景生成器

```python
from scripts import BackgroundGenerator, QwenAPIClient

api_client = QwenAPIClient(api_key="your-api-key")
generator = BackgroundGenerator(api_client)
background = generator.generate_background(persona_dict, dialogue_topic)
```

### StoryGenerator

故事生成器

```python
from scripts import StoryGenerator, QwenAPIClient

api_client = QwenAPIClient(api_key="your-api-key")
generator = StoryGenerator(api_client)
story = generator.generate_story(persona_dict, topic)
```

### DialogueGenerator

对话生成器

```python
from scripts import DialogueGenerator, QwenAPIClient

api_client = QwenAPIClient(api_key="your-api-key")
generator = DialogueGenerator(api_client)
result = generator.generate_response(
    persona=persona_dict,
    dialogue_topic=topic,
    background=background,
    dialogue_history=history
)
```

## 注意事项

1. 确保API密钥有效且有足够的配额
2. 生成对话时，建议先生成背景和故事，再生成对话
3. 对话生成遵循"开场→互动→聚焦→收束"的节奏
4. 每轮对话长度控制在8-30字，最多40字

