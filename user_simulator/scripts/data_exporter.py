"""
数据导出模块
将用户模拟器生成的对话数据转换为SFT训练所需的格式
"""
import json
from typing import List, Dict, Any, Optional
from pathlib import Path


class SFTDataExporter:
    """SFT训练数据导出器"""
    
    @staticmethod
    def export_to_messages_format(
        conversations: List[Dict[str, Any]],
        output_path: str,
        include_metadata: bool = True
    ) -> None:
        """
        导出为messages格式（适用于transformers和Qwen模型）
        
        格式：
        {
            "messages": [
                {"role": "user", "content": "..."},
                {"role": "assistant", "content": "..."}
            ]
        }
        
        Args:
            conversations: 对话列表，每个对话包含dialogue_history和metadata
            output_path: 输出文件路径
            include_metadata: 是否包含元数据（患者画像、背景等）
        """
        sft_data = []
        
        for conv in conversations:
            dialogue_history = conv.get("dialogue_history", [])
            if not dialogue_history:
                continue
            
            # 构建messages格式
            messages = []
            for turn in dialogue_history:
                role = turn.get("role", "user")
                content = turn.get("content", "")
                
                # 转换角色名称：user -> user, assistant -> assistant
                if role == "user" or role == "患者":
                    messages.append({"role": "user", "content": content})
                elif role == "assistant" or role == "助手" or role == "照护师":
                    messages.append({"role": "assistant", "content": content})
            
            # 如果只有患者对话，需要添加占位符或提示
            # 确保messages是成对的（user-assistant交替）
            if len(messages) > 0 and messages[-1]["role"] == "user":
                # 最后一个如果是user，添加一个assistant占位符
                messages.append({
                    "role": "assistant",
                    "content": "[需要照护师回复]"
                })
            
            item = {"messages": messages}
            
            # 添加元数据（可选）
            if include_metadata:
                metadata = {}
                if "persona" in conv:
                    metadata["persona"] = conv["persona"]
                if "background" in conv:
                    metadata["background"] = conv["background"]
                if "story" in conv:
                    metadata["story"] = conv["story"]
                if "dialogue_topic" in conv:
                    metadata["dialogue_topic"] = conv["dialogue_topic"]
                if metadata:
                    item["metadata"] = metadata
            
            sft_data.append(item)
        
        # 保存为JSONL格式（每行一个JSON对象，适合大文件）
        output_path = Path(output_path)
        if output_path.suffix == ".jsonl":
            with open(output_path, 'w', encoding='utf-8') as f:
                for item in sft_data:
                    f.write(json.dumps(item, ensure_ascii=False) + '\n')
        else:
            # 保存为JSON格式
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(sft_data, f, ensure_ascii=False, indent=2)
    
    @staticmethod
    def export_to_conversation_format(
        conversations: List[Dict[str, Any]],
        output_path: str
    ) -> None:
        """
        导出为conversation格式（适用于某些训练框架）
        
        格式：
        {
            "conversation": [
                {"role": "user", "content": "..."},
                {"role": "assistant", "content": "..."}
            ]
        }
        
        Args:
            conversations: 对话列表
            output_path: 输出文件路径
        """
        sft_data = []
        
        for conv in conversations:
            dialogue_history = conv.get("dialogue_history", [])
            if not dialogue_history:
                continue
            
            conversation = []
            for turn in dialogue_history:
                role = turn.get("role", "user")
                content = turn.get("content", "")
                
                if role == "user" or role == "患者":
                    conversation.append({"role": "user", "content": content})
                elif role == "assistant" or role == "助手" or role == "照护师":
                    conversation.append({"role": "assistant", "content": content})
            
            if len(conversation) > 0:
                sft_data.append({"conversation": conversation})
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(sft_data, f, ensure_ascii=False, indent=2)
    
    @staticmethod
    def export_to_instruction_format(
        conversations: List[Dict[str, Any]],
        output_path: str,
        system_prompt: Optional[str] = None
    ) -> None:
        """
        导出为instruction格式（适用于某些训练框架）
        
        格式：
        {
            "instruction": "系统提示",
            "input": "用户输入",
            "output": "助手输出"
        }
        
        Args:
            conversations: 对话列表
            output_path: 输出文件路径
            system_prompt: 系统提示词
        """
        sft_data = []
        system_prompt = system_prompt or "你是一位专业的血糖异常患者照护师，擅长高情商地和患者聊天，为患者提供专业的帮助，宽慰患者的情绪。"
        
        for conv in conversations:
            dialogue_history = conv.get("dialogue_history", [])
            if not dialogue_history:
                continue
            
            # 将多轮对话转换为instruction格式
            # 方法1：每轮对话作为一个样本
            for i in range(0, len(dialogue_history) - 1, 2):
                if i + 1 < len(dialogue_history):
                    user_turn = dialogue_history[i]
                    assistant_turn = dialogue_history[i + 1]
                    
                    if user_turn.get("role") in ["user", "患者"] and \
                       assistant_turn.get("role") in ["assistant", "助手", "照护师"]:
                        # 构建历史上下文
                        history = ""
                        for j in range(i):
                            turn = dialogue_history[j]
                            role_name = "用户" if turn.get("role") in ["user", "患者"] else "照护师"
                            history += f"{role_name}: {turn.get('content', '')}\n"
                        
                        item = {
                            "instruction": system_prompt,
                            "input": history + f"用户: {user_turn.get('content', '')}",
                            "output": assistant_turn.get("content", "")
                        }
                        sft_data.append(item)
            
            # 方法2：整个对话作为一个样本（如果最后是用户，需要等待回复）
            # 这里暂时不实现，因为需要完整的对话对
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(sft_data, f, ensure_ascii=False, indent=2)
    
    @staticmethod
    def export_to_llamafactory_format(
        conversations: List[Dict[str, Any]],
        output_path: str
    ) -> None:
        """
        导出为LLaMA-Factory格式
        
        格式：
        {
            "conversation": [
                {"from": "human", "value": "..."},
                {"from": "gpt", "value": "..."}
            ]
        }
        
        Args:
            conversations: 对话列表
            output_path: 输出文件路径
        """
        sft_data = []
        
        for conv in conversations:
            dialogue_history = conv.get("dialogue_history", [])
            if not dialogue_history:
                continue
            
            conversation = []
            for turn in dialogue_history:
                role = turn.get("role", "user")
                content = turn.get("content", "")
                
                if role == "user" or role == "患者":
                    conversation.append({"from": "human", "value": content})
                elif role == "assistant" or role == "助手" or role == "照护师":
                    conversation.append({"from": "gpt", "value": content})
            
            if len(conversation) > 0:
                sft_data.append({"conversation": conversation})
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(sft_data, f, ensure_ascii=False, indent=2)
    
    @staticmethod
    def export_to_multiple_formats(
        conversations: List[Dict[str, Any]],
        output_dir: str,
        formats: List[str] = None
    ) -> Dict[str, str]:
        """
        导出为多种格式
        
        Args:
            conversations: 对话列表
            output_dir: 输出目录
            formats: 格式列表，可选: ["messages", "conversation", "instruction", "llamafactory"]
            
        Returns:
            导出的文件路径字典
        """
        if formats is None:
            formats = ["messages", "conversation", "instruction"]
        
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_files = {}
        
        if "messages" in formats:
            messages_path = output_dir / "sft_data_messages.jsonl"
            SFTDataExporter.export_to_messages_format(conversations, str(messages_path))
            output_files["messages"] = str(messages_path)
        
        if "conversation" in formats:
            conv_path = output_dir / "sft_data_conversation.json"
            SFTDataExporter.export_to_conversation_format(conversations, str(conv_path))
            output_files["conversation"] = str(conv_path)
        
        if "instruction" in formats:
            inst_path = output_dir / "sft_data_instruction.json"
            SFTDataExporter.export_to_instruction_format(conversations, str(inst_path))
            output_files["instruction"] = str(inst_path)
        
        if "llamafactory" in formats:
            llama_path = output_dir / "sft_data_llamafactory.json"
            SFTDataExporter.export_to_llamafactory_format(conversations, str(llama_path))
            output_files["llamafactory"] = str(llama_path)
        
        return output_files

