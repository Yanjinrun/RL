"""
SFT数据导出示例
演示如何将用户模拟器生成的对话数据导出为SFT训练格式
"""
import json
from scripts import SFTDataExporter
from pathlib import Path


def example_export_sft():
    """示例：导出SFT训练数据"""
    
    # 示例：从文件加载对话数据
    # 假设这是用户模拟器生成的对话数据
    conversation_data = {
        "dialogue_history": [
            {
                "role": "user",
                "content": "中午在外面吃饭，餐后两小时测到16.4，刚补了胰岛素。",
                "thinking": "今天血糖冲到16.4，补针又晚了，心里发慌。"
            },
            {
                "role": "user",
                "content": "16.4是不是已经超过安全线了？",
                "thinking": "这数值太高了，担心有没有伤到神经或血管。"
            },
            {
                "role": "user",
                "content": "现在降到10.2了，这种情况还会损伤器官吗？",
                "thinking": "虽然降下来了，但还是担心器官损伤。"
            }
        ],
        "persona": {
            "患者基本信息": "该患者是一位慢性病管理参与者，性格内敛，注重隐私",
            "核心性格特征": "患者以'焦虑确认的守线者'为核心底色"
        },
        "background": "### 24小时生活状态\n- **饮食情况**: 早餐7:00在家吃...",
        "story": "患者今日上午带孩子前往游乐园活动...",
        "dialogue_topic": "患者上午带娃在游乐园玩，中午在外面的餐厅吃饭。血糖最高值达到了16.4mmol/L"
    }
    
    # 转换为列表格式（SFT导出器需要列表）
    conversations = [conversation_data]
    
    # 创建输出目录
    output_dir = Path("output/sft_data")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 60)
    print("SFT数据导出示例")
    print("=" * 60)
    
    # 1. 导出为messages格式（推荐，适用于Qwen和transformers）
    print("\n[1] 导出为messages格式（JSONL）...")
    messages_path = output_dir / "sft_data_messages.jsonl"
    SFTDataExporter.export_to_messages_format(
        conversations=conversations,
        output_path=str(messages_path),
        include_metadata=True
    )
    print(f"✓ 已保存到: {messages_path}")
    
    # 显示前几行内容
    with open(messages_path, 'r', encoding='utf-8') as f:
        first_line = f.readline()
        data = json.loads(first_line)
        print("\n示例内容:")
        print(json.dumps(data, ensure_ascii=False, indent=2)[:500] + "...")
    
    # 2. 导出为conversation格式
    print("\n[2] 导出为conversation格式...")
    conv_path = output_dir / "sft_data_conversation.json"
    SFTDataExporter.export_to_conversation_format(
        conversations=conversations,
        output_path=str(conv_path)
    )
    print(f"✓ 已保存到: {conv_path}")
    
    # 3. 导出为instruction格式
    print("\n[3] 导出为instruction格式...")
    inst_path = output_dir / "sft_data_instruction.json"
    SFTDataExporter.export_to_instruction_format(
        conversations=conversations,
        output_path=str(inst_path),
        system_prompt="你是一位专业的血糖异常患者照护师，擅长高情商地和患者聊天，为患者提供专业的帮助，宽慰患者的情绪。"
    )
    print(f"✓ 已保存到: {inst_path}")
    
    # 4. 导出为LLaMA-Factory格式
    print("\n[4] 导出为LLaMA-Factory格式...")
    llama_path = output_dir / "sft_data_llamafactory.json"
    SFTDataExporter.export_to_llamafactory_format(
        conversations=conversations,
        output_path=str(llama_path)
    )
    print(f"✓ 已保存到: {llama_path}")
    
    # 5. 一次性导出所有格式
    print("\n[5] 一次性导出所有格式...")
    output_files = SFTDataExporter.export_to_multiple_formats(
        conversations=conversations,
        output_dir=str(output_dir / "all_formats"),
        formats=["messages", "conversation", "instruction", "llamafactory"]
    )
    print("✓ 所有格式已导出:")
    for format_name, file_path in output_files.items():
        print(f"  - {format_name}: {file_path}")
    
    print("\n" + "=" * 60)
    print("导出完成！")
    print("=" * 60)
    print("\n说明:")
    print("- messages格式（JSONL）: 适用于transformers库和Qwen模型，推荐使用")
    print("- conversation格式: 适用于某些自定义训练框架")
    print("- instruction格式: 适用于instruction-following训练")
    print("- llamafactory格式: 适用于LLaMA-Factory训练框架")
    print("\n注意: 当前导出的数据只包含患者对话，需要配合照护师回复才能用于SFT训练。")


if __name__ == "__main__":
    example_export_sft()

