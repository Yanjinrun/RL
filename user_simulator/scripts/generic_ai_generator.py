"""
通用AI对话生成器
用于生成未经医疗领域专门优化的通用AI助手的回复
"""
from typing import List, Dict
from .api_client import QwenAPIClient


class GenericAIGenerator:
    """
    通用AI对话生成器
    负责生成通用AI助手（无医疗微调）的回复
    """

    def __init__(self, api_client: QwenAPIClient):
        """
        初始化通用AI生成器
        
        Args:
            api_client: API客户端实例
        """
        self.api_client = api_client

    def generate_reply(
        self,
        dialogue_history: List[Dict[str, str]]
    ) -> str:
        """
        生成通用AI助手的一轮回复
        
        Args:
            dialogue_history: 对话历史，格式: [{"role": "user/assistant", "content": "..."}, ...]
            
        Returns:
            生成的回复文本
        """
        prompt = self._build_prompt(dialogue_history)

        result = self.api_client.call(
            prompt=prompt,
            model="qwen-turbo",  # 使用通用模型
            temperature=0.7,
            max_tokens=200
        )

        return result.strip()
    
    def _build_prompt(
        self,
        dialogue_history: List[Dict[str, str]]
    ) -> str:
        """
        构建通用AI助手的提示词
        不使用医疗领域的专业提示词，只作为普通AI助手
        """
        # 构建对话历史文本（限制长度，只取最近6轮）
        history_text = ""
        for msg in dialogue_history[-6:]:
            role = "用户" if msg.get("role") == "user" else "助手"
            content = msg.get("content", "")
            # 限制每条消息长度
            if len(content) > 150:
                content = content[:147] + "..."
            history_text += f"{role}: {content}\n"

        prompt = f"""你是一个友好的AI助手，正在与用户进行对话。请根据对话历史，自然地回复用户。

# 对话历史
{history_text}

# 回复要求
- 回复要简洁、友好、有帮助
- 使用自然的口语化表达
- 如果用户询问医疗相关问题，可以提供一般性信息，但应提醒用户咨询专业医生
- 回复长度控制在20-80字之间
- 直接输出对话内容，不要包含思考过程

# 你的回复："""

        return prompt

