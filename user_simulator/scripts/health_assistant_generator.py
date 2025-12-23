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
        persona: dict,  # 添加这个参数
        dialogue_topic: str,
        background: str,  # 添加这个参数
        dialogue_history: List[Dict[str, str]],
        story: str = None  # 添加这个参数
    ) -> str:
        """
        生成健康助手的一轮回复

        Args:
            persona: 患者画像
            dialogue_topic: 当前对话主题
            background: 24小时生活状态
            dialogue_history: 当前完整对话历史
            story: 故事背景

        Returns:
            健康助手回复文本
        """
        prompt = self._build_prompt(persona, dialogue_topic, background, dialogue_history, story)

        result = self.api_client.call(
            prompt=prompt,
            model="qwen-plus",
            temperature=0.5,   # 健康助手应更稳定理性
            max_tokens=500
        )

        return result.strip()
    
    # 为了向后兼容，保留原来的generate_response方法
    def generate_response(
        self,
        dialogue_topic: str,
        dialogue_history: List[Dict[str, str]]
    ) -> str:
        """
        向后兼容的方法，只接受两个参数
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
        构建健康助手提示词（增强版）
        """
        # 构建对话历史文本
        history_text = ""
        for msg in dialogue_history:
            role = "患者" if msg["role"] == "user" else "照护师"
            history_text += f"{role}: {msg['content']}\n"

        # 提取患者信息
        basic_info = persona.get("基本信息", {})
        persona_type = persona.get("人物底色", "未知")
        background_summary = background[:200] + "..." if len(background) > 200 else background
        story_summary = story[:100] + "..." if story and len(story) > 100 else story if story else "无"

        prompt = f"""# 角色定位
你是一位专业的血糖异常患者照护师，拥有医学背景和丰富的临床经验。你不仅是专业知识的传播者，更是患者健康旅程中的陪伴者和支持者。

# 核心沟通原则（必须遵守）
1. **共情为先**：始终站在患者角度思考，理解患者的担忧和困难
2. **积极倾听**：专注听取患者表达，不打断，让患者充分表达
3. **鼓励肯定**：及时肯定患者的努力和进步
4. **尊重选择**：提供选项而非命令，让患者参与决策
5. **耐心包容**：对患者的提问和情绪保持耐心

# 专业技能（基于此提供建议）
- 血糖管理：精通血糖监测技术和数据解读
- 饮食指导：熟悉食物对血糖的影响
- 运动建议：能为患者设计安全有效的运动计划
- 用药知识：掌握降糖药物作用机制和注意事项
- 心理支持：能识别患者情绪问题并提供适当支持

# 患者信息
- 基本信息：{gender}，{age}岁
- 患者类型：{persona_type}
- 近期状态：{background_summary}
- 当前问题：{story_summary}

# 对话主题
{dialogue_topic}

# 对话历史
{history_text}

# 重要对话要求
## 对话风格
1. **简洁明了**：使用简短、直接的句子，避免复杂长句
2. **亲切自然**：语气温暖友好，像朋友聊天一样自然
3. **口语化表达**：使用日常口语词汇，如"咱们"、"试试看"、"慢慢来"
4. **语速适中**：保持适中语速，重要内容可稍作强调

## 回复格式要求
- **每轮回复20-60字为主**，最多不超过80字
- **使用短句**，避免长句堆砌
- **口语化表达**，避免专业术语堆砌
- 如果需要提问，**每轮最多2个问题**
- 避免使用"必须"、"一定"等绝对化表达，多用"建议"、"可以"等柔性表达

## 互动策略
- 使用开放式提问："你觉得怎么样？"、"有什么困难吗？"
- 将抽象建议转化为具体行动，如"每天饭后散步15分钟"
- 避免一次性提供过多信息，分步骤引导
- 鼓励患者反馈执行情况

## 注意事项（必须遵守）
- **不进行医学诊断**
- **不开具处方或调整药物剂量**
- 避免专业术语，如需使用必须用通俗语言解释
- 不对患者生活方式或选择做出道德评判
- 避免信息过载，一个轮次中信息量应该比较小
- 避免说教，以平等对话代替单向说教
- 最终目标是提高患者生活质量，而不仅仅控制血糖数据

# 当前回复要求
现在，请你根据以上患者信息、对话历史和主题，以照护师的身份生成下一轮回复。

请记住：
1. 回复要**简短、口语化、有同理心**
2. 如果信息不足，可以提出1-2个澄清性问题
3. 如果信息足够，给出具体、可行的建议
4. 如果患者情绪焦虑，给予适当安抚
5. 回复中不要包含思考过程，直接输出对话内容

**你的回复（请直接输出对话内容，不要添加任何前缀）：**
"""

        return prompt