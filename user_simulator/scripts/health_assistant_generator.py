from typing import List, Dict
from .api_client import QwenAPIClient


class HealthAssistantGenerator:
    """
    健康助手对话生成器
    负责生成照护师（健康助手）的回复
    """

    def __init__(self, api_client: QwenAPIClient):
        self.api_client = api_client

    def generate_reply(
        self,
        persona: dict,
        dialogue_topic: str,
        background: str,
        dialogue_history: List[Dict[str, str]],
        story: str = None
    ) -> str:
        """
        生成健康助手的一轮回复
        """
        prompt = self._build_prompt(persona, dialogue_topic, background, dialogue_history, story)

        result = self.api_client.call(
            prompt=prompt,
            model="qwen-turbo",  # 改为turbo模型，可能更稳定
            temperature=0.6,
            max_tokens=150      # 进一步限制字数
        )

        return result.strip()
    
    def generate_response(
        self,
        dialogue_topic: str,
        dialogue_history: List[Dict[str, str]]
    ) -> str:
        """
        向后兼容的方法
        """
        return self.generate_reply(
            persona={},
            dialogue_topic=dialogue_topic,
            background="",
            dialogue_history=dialogue_history,
            story=None
        )

    def _build_prompt(
        self,
        persona: dict,
        dialogue_topic: str,
        background: str,
        dialogue_history: List[Dict[str, str]],
        story: str = None
    ) -> str:
        """
        构建健康助手提示词
        """
        # 安全地获取患者信息
        basic_info = persona.get("基本信息", {})
        gender = basic_info.get('性别', '未知') if isinstance(basic_info, dict) else '未知'
        age = basic_info.get('年龄', '未知') if isinstance(basic_info, dict) else '未知'
        persona_type = persona.get('人物底色', '未知')
        
        # 简化背景和故事信息
        background_summary = background[:100] + "..." if background and len(background) > 100 else background or "无相关信息"
        story_summary = story[:80] + "..." if story and len(story) > 80 else story or ""

        # 构建对话历史文本（限制长度）
        history_text = ""
        for msg in dialogue_history[-4:]:  # 只取最近4轮
            role = "患者" if msg.get("role") == "user" else "照护师"
            content = msg.get("content", "")
            # 限制每条消息长度
            if len(content) > 100:
                content = content[:97] + "..."
            history_text += f"{role}: {content}\n"

        prompt = f"""# 角色定位
你是一位专业的血糖异常患者照护师，拥有医学背景和丰富的临床经验。

# 核心沟通原则
1. 共情为先，站在患者角度思考
2. 积极倾听，让患者充分表达
3. 鼓励肯定，及时肯定患者的努力
4. 尊重选择，提供选项而非命令
5. 耐心包容，对患者的提问保持耐心

# 患者基本信息
- 性别：{gender}
- 年龄：{age}
- 患者类型：{persona_type}

# 对话主题
{dialogue_topic}

# 对话历史（最近4轮）
{history_text}

# 回复要求
## 风格要求
- 使用简短、直接的句子，每轮回复20-60字
- 语气温暖友好，像朋友聊天一样自然
- 使用日常口语词汇，如"咱们"、"试试看"、"慢慢来"
- 避免使用复杂医学术语

## 内容要求
- 如果信息不足，可以提出1-2个澄清性问题
- 如果信息足够，给出具体、可行的建议
- 如果患者情绪焦虑，给予适当安抚
- 不进行医学诊断，不开具处方或调整药物剂量

## 注意事项
- 回复要简短、口语化、有同理心
- 避免信息过载，一个轮次中信息量要小
- 不要包含思考过程，直接输出对话内容

# 你的回复（请直接输出对话内容）："""

        return prompt