# 基线对话生成 - 快速开始

## 已完成的工作

✅ **场景提示词JSON文件** (`data/scene_prompts.json`)
- 包含12个场景的完整提示词
- 每个场景包含：场景名称、描述、患者画像摘要、对话目标、患者模拟器指令等

✅ **通用AI对话生成器** (`scripts/generic_ai_generator.py`)
- 区别于专业的健康助手
- 使用通用模型，无医疗领域专门优化
- 提供简洁友好的对话回复

✅ **基线对话生成脚本** (`scripts/generate_baseline_dialogues.py`)
- 使用场景提示词驱动病人模拟器与通用AI对话
- 支持批量生成所有场景或单独生成指定场景
- 自动保存对话结果为JSON格式

✅ **入口脚本** (`generate_baseline.py`)
- 便于直接执行的命令行入口

## 快速开始

### 1. 设置API密钥

```bash
export QWEN_API_KEY="your-api-key-here"
```

### 2. 生成所有场景的对话

```bash
cd /home/zy/project2/RL/user_simulator/scripts
python generate_baseline.py \
    --prompts-file data/scene_prompts.json \
    --output-dir output/baseline_dialogues \
    --max-turns 10
```

### 3. 生成单个场景的对话（测试用）

```bash
python generate_baseline.py \
    --prompts-file data/scene_prompts.json \
    --output-dir output/baseline_dialogues \
    --max-turns 10 \
    --scene HYPOGLYCEMIA
```

## 输出结果

生成的对话将保存在 `output/baseline_dialogues/` 目录下：

- `HYPOGLYCEMIA_dialogue.json` - 低血糖场景对话
- `HYPERGLYCEMIA_dialogue.json` - 高血糖场景对话
- `MEDICATION_ADHERENCE_dialogue.json` - 用药依从性场景对话
- ... (其他9个场景)
- `all_scenes_summary.json` - 所有场景的汇总文件

## 注意事项

1. **API密钥**：确保已设置 `QWEN_API_KEY` 环境变量或在 `config.py` 中配置
2. **API配额**：生成12个场景的对话需要较多API调用，请确保有足够配额
3. **网络连接**：确保可以访问阿里云百炼API服务

## 后续步骤

生成的基线对话数据可以用于：
1. 与训练的专业"医生AI"对话效果进行对比
2. 使用奖励函数评估通用AI和专业AI的回复质量
3. 分析通用AI在不同场景下的表现特点

## 更多信息

详细使用说明请参考：`BASELINE_DIALOGUE_GENERATION.md`

