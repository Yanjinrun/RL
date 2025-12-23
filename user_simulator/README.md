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

# 只生成患者画像
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
│   ├── background_generator.py # 背景生成
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

## SFT数据导出

用户模拟器生成的对话数据可以导出为SFT（监督微调）训练所需的格式，方便与SFT部分的工作衔接。

### 支持的格式

1. **messages格式（推荐）**: 适用于transformers库和Qwen模型
   ```json
   {
     "messages": [
       {"role": "user", "content": "..."},
       {"role": "assistant", "content": "..."}
     ],
     "metadata": {...}
   }
   ```

2. **conversation格式**: 适用于某些自定义训练框架
   ```json
   {
     "conversation": [
       {"role": "user", "content": "..."},
       {"role": "assistant", "content": "..."}
     ]
   }
   ```

3. **instruction格式**: 适用于instruction-following训练
   ```json
   {
     "instruction": "系统提示",
     "input": "用户输入",
     "output": "助手输出"
   }
   ```

4. **llamafactory格式**: 适用于LLaMA-Factory训练框架
   ```json
   {
     "conversation": [
       {"from": "human", "value": "..."},
       {"from": "gpt", "value": "..."}
     ]
   }
   ```

### 使用方法

#### 方法1: 使用命令行导出

```bash
# 生成对话并自动导出SFT数据
python3 main.py --mode conversation \
  --topic "对话主题" \
  --max-turns 10 \
  --export-sft \
  --sft-format messages \
  --sft-output-dir output/sft_data
```

#### 方法2: 使用Python代码导出

```python
from scripts import SFTDataExporter

# 准备对话数据（从用户模拟器生成）
conversations = [
    {
        "dialogue_history": [
            {"role": "user", "content": "患者说的话"},
            {"role": "assistant", "content": "照护师说的话"}
        ],
        "persona": {...},
        "background": "...",
        "story": "...",
        "dialogue_topic": "..."
    }
]

# 导出为messages格式（JSONL）
SFTDataExporter.export_to_messages_format(
    conversations=conversations,
    output_path="output/sft_data.jsonl",
    include_metadata=True
)

# 或一次性导出所有格式
output_files = SFTDataExporter.export_to_multiple_formats(
    conversations=conversations,
    output_dir="output/sft_data",
    formats=["messages", "conversation", "instruction", "llamafactory"]
)
```

#### 方法3: 运行示例脚本

```bash
python3 export_sft_example.py
```

### 数据格式说明

**messages格式（JSONL）**：
- 每行一个JSON对象
- 包含`messages`数组，格式为`[{"role": "user/assistant", "content": "..."}]`
- 可选包含`metadata`字段，保存患者画像、背景等信息
- **推荐使用此格式**，适用于transformers库和Qwen模型

**注意事项**：
- 当前用户模拟器只生成患者对话，需要配合照护师回复才能用于SFT训练
- 如果对话以患者发言结束，会自动添加`[需要照护师回复]`占位符
- metadata字段包含完整的患者画像和背景信息，可用于训练时的上下文理解

## 注意事项

1. 确保API密钥有效且有足够的配额
2. 生成对话时，建议先生成背景和故事，再生成对话
3. 对话生成遵循"开场→互动→聚焦→收束"的节奏
4. 每轮对话长度控制在8-30字，最多40字
5. SFT数据导出时，确保对话包含患者和照护师的完整对话对

