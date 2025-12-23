# SFT训练数据格式说明

本文档说明用户模拟器导出的SFT训练数据格式，方便与SFT部分的工作衔接。

## 数据格式概览

用户模拟器支持导出4种SFT训练数据格式：

1. **messages格式**（推荐）- 适用于transformers和Qwen模型
2. **conversation格式** - 适用于自定义训练框架
3. **instruction格式** - 适用于instruction-following训练
4. **llamafactory格式** - 适用于LLaMA-Factory框架

## 1. messages格式（推荐）

### 文件格式
- **文件扩展名**: `.jsonl`（JSON Lines，每行一个JSON对象）
- **适用框架**: transformers库、Qwen模型、大多数现代LLM训练框架

### 数据结构

```json
{
  "messages": [
    {
      "role": "user",
      "content": "中午在外面吃饭，餐后两小时测到16.4，刚补了胰岛素。"
    },
    {
      "role": "assistant",
      "content": "16.4确实有点高，不过你已经及时补了胰岛素，这很好。现在感觉怎么样？"
    },
    {
      "role": "user",
      "content": "16.4是不是已经超过安全线了？"
    },
    {
      "role": "assistant",
      "content": "16.4确实超过了正常范围，但偶尔一次高血糖不会立即造成严重伤害。重要的是你已经处理了，现在需要观察后续的血糖变化。"
    }
  ],
  "metadata": {
    "persona": {
      "患者基本信息": "...",
      "核心性格特征": "..."
    },
    "background": "24小时生活状态描述...",
    "story": "故事背景描述...",
    "dialogue_topic": "对话主题..."
  }
}
```

### 字段说明

- **messages**: 对话消息数组，按时间顺序排列
  - `role`: 角色，`"user"`表示患者，`"assistant"`表示照护师
  - `content`: 消息内容
- **metadata**（可选）: 元数据，包含患者画像、背景等信息

### 使用示例（transformers）

```python
from datasets import load_dataset

# 加载JSONL格式数据
dataset = load_dataset("json", data_files="sft_data_messages.jsonl")

# 数据会自动转换为训练格式
for example in dataset["train"]:
    messages = example["messages"]
    # 可以直接用于训练
```

### 使用示例（Qwen训练）

```python
from transformers import AutoTokenizer, AutoModelForCausalLM

tokenizer = AutoTokenizer.from_pretrained("Qwen/Qwen-7B-Chat")
model = AutoModelForCausalLM.from_pretrained("Qwen/Qwen-7B-Chat")

# 格式化对话
messages = [
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."}
]

# 转换为模型输入
text = tokenizer.apply_chat_template(messages, tokenize=False)
```

## 2. conversation格式

### 文件格式
- **文件扩展名**: `.json`
- **适用框架**: 自定义训练框架

### 数据结构

```json
[
  {
    "conversation": [
      {
        "role": "user",
        "content": "中午在外面吃饭，餐后两小时测到16.4，刚补了胰岛素。"
      },
      {
        "role": "assistant",
        "content": "16.4确实有点高，不过你已经及时补了胰岛素，这很好。"
      }
    ]
  }
]
```

## 3. instruction格式

### 文件格式
- **文件扩展名**: `.json`
- **适用框架**: instruction-following训练

### 数据结构

```json
[
  {
    "instruction": "你是一位专业的血糖异常患者照护师，擅长高情商地和患者聊天，为患者提供专业的帮助，宽慰患者的情绪。",
    "input": "用户: 中午在外面吃饭，餐后两小时测到16.4，刚补了胰岛素。",
    "output": "16.4确实有点高，不过你已经及时补了胰岛素，这很好。现在感觉怎么样？"
  }
]
```

## 4. llamafactory格式

### 文件格式
- **文件扩展名**: `.json`
- **适用框架**: LLaMA-Factory

### 数据结构

```json
[
  {
    "conversation": [
      {
        "from": "human",
        "value": "中午在外面吃饭，餐后两小时测到16.4，刚补了胰岛素。"
      },
      {
        "from": "gpt",
        "value": "16.4确实有点高，不过你已经及时补了胰岛素，这很好。"
      }
    ]
  }
]
```

## 数据完整性说明

### 当前状态

用户模拟器目前**只生成患者对话**，不包含照护师回复。因此：

1. **导出的数据中只有`role: "user"`的消息**
2. **如果对话以患者发言结束，会自动添加占位符**：
   ```json
   {
     "role": "assistant",
     "content": "[需要照护师回复]"
   }
   ```

### 完整训练数据的构建

要用于SFT训练，需要：

1. **使用用户模拟器生成患者对话**
2. **使用照护师模型/API生成照护师回复**
3. **将两者组合成完整的对话对**
4. **导出为SFT格式**

### 建议的工作流程

```
用户模拟器生成患者对话
    ↓
照护师模型生成回复（SFT部分负责）
    ↓
组合成完整对话对
    ↓
导出为SFT训练格式
    ↓
用于SFT训练
```

## 数据质量要求

1. **对话对完整性**: 确保每个用户消息都有对应的助手回复
2. **角色交替**: user和assistant应该交替出现
3. **内容质量**: 确保对话内容符合医疗健康对话规范
4. **元数据完整性**: 保留患者画像和背景信息，便于理解上下文

## 与SFT部分的衔接

### 输入要求

SFT部分需要：
- 完整的对话对（患者+照护师）
- 格式化的训练数据（messages格式推荐）
- 可选的元数据（用于上下文理解）

### 输出格式

用户模拟器提供：
- ✅ 患者对话（已生成）
- ✅ 数据格式转换（已实现）
- ❌ 照护师回复（需要SFT部分补充）

### 建议的接口

```python
# SFT部分可以这样使用用户模拟器的输出
from scripts import SFTDataExporter

# 1. 加载用户模拟器生成的对话
with open("user_simulator_output.json", "r") as f:
    user_dialogues = json.load(f)

# 2. 为每个患者对话生成照护师回复
complete_dialogues = []
for dialogue in user_dialogues:
    patient_turns = [t for t in dialogue["dialogue_history"] if t["role"] == "user"]
    
    # 使用照护师模型生成回复
    for patient_turn in patient_turns:
        caregiver_response = generate_caregiver_response(patient_turn["content"])
        dialogue["dialogue_history"].append({
            "role": "assistant",
            "content": caregiver_response
        })
    
    complete_dialogues.append(dialogue)

# 3. 导出为SFT格式
SFTDataExporter.export_to_messages_format(
    conversations=complete_dialogues,
    output_path="sft_training_data.jsonl"
)
```

## 文件示例

完整的数据文件示例请参考：
- `output/sft_data/sft_data_messages.jsonl` - messages格式示例
- `output/sft_data/sft_data_conversation.json` - conversation格式示例
- `output/sft_data/sft_data_instruction.json` - instruction格式示例
- `output/sft_data/sft_data_llamafactory.json` - llamafactory格式示例

