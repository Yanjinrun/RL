from typing import List, Dict, Optional
from .api_client import QwenAPIClient


class HealthAssistantGenerator_thinking:
    """
    健康助手对话生成器
    负责生成照护师（健康助手）的回复，包含 Thinking 思维链
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
    ) -> Dict[str, str]:
        """
        生成健康助手的一轮回复（包含 Thinking）
        
        Returns:
            {"thinking": "内部推理过程", "response": "实际回复内容"}
        """
        prompt = self._build_prompt(persona, dialogue_topic, background, dialogue_history, story)

        result = self.api_client.call(
            prompt=prompt,
            model="qwen-plus",        
            temperature=0.8,
            max_tokens=2000
        )

        return self._parse_response(result.strip())

    def generate_response(
        self,
        dialogue_topic: str,
        dialogue_history: List[Dict[str, str]]
    ) -> Dict[str, str]:
        """
        向后兼容的方法（不带 persona 等信息）
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
        构建健康助手的提示词（要求先 Thinking 后 Response）
        """
        # 安全获取患者信息
        basic_info = persona.get("基本信息", {})
        gender = basic_info.get('性别', '未知') if isinstance(basic_info, dict) else '未知'
        age = basic_info.get('年龄', '未知') if isinstance(basic_info, dict) else '未知'
        persona_type = persona.get('人物底色', '未知')

        # 简化背景和故事
        background_summary = background[:150] + "..." if background and len(background) > 150 else background or "无相关背景信息"
        story_summary = story[:100] + "..." if story and len(story) > 100 else story or ""

        # 构建最近对话历史（限制在最近4-6轮，避免过长）
        history_text = ""
        recent_history = dialogue_history[-6:] if len(dialogue_history) > 6 else dialogue_history
        for msg in recent_history:
            role = "患者" if msg.get("role") == "user" else "照护师"
            content = msg.get("content", "")
            if len(content) > 120:
                content = content[:117] + "..."
            history_text += f"{role}: {content}\n"

        prompt = f"""# 角色定位
你是一位专业、温暖、有耐心的糖尿病照护师，拥有丰富临床经验和优秀沟通能力。

# 核心沟通原则
1. 共情为先：始终理解患者情绪，给予情感支持
2. 积极倾听：鼓励患者表达，不打断
3. 鼓励肯定：及时认可患者的努力和进步
4. 尊重选择：提供建议而非命令
5. 科学专业：解释清晰，避免医学术语恐吓

# 患者信息
- 性别：{gender}
- 年龄：{age}
- 患者类型：{persona_type}

# 当前对话主题
{dialogue_topic}

# 患者背景摘要
{background_summary}

# 故事背景（如有）
{story_summary}

# 最近对话记录
{history_text}

# 回复要求

## 第一步：Thinking（内部思考）
请先站在照护师角度，进行结构化思考：
- 患者当前最可能的情绪状态是什么？（焦虑/困惑/抵触/积极等）
- 患者的核心诉求或隐性问题是什麼？
- 我上一轮是否遗漏了重要信息？
- 本轮我应该优先解决哪个点？（安抚情绪 / 澄清问题 / 给出建议 / 追问细节）
- 如何用合适且专业的方式表达？

## 第二步：Response（实际回复）
- 回复长度控制在30-80字
- 语气温暖自然，像朋友一样（常用“咱们”“试试看”“慢慢来”“别担心”）
- 先共情，再建议，最后鼓励
- 最多提1个具体可行的小行动
- 如需追问，最多1-2个温和问题，且仅当轮次 < 10 时；如果轮次 >= 10，且患者已表达满足（如“嗯”“好”“谢谢”），你的回复必须以鼓励结束语收尾（如“慢慢来，有问题随时说～”），而非新问题**。
- 绝不诊断、不开药、不吓唬患者
- 如果对话已进行8轮以上，且患者疑问已覆盖，优先推动收束，而不是继续追问细节。

# 输出格式（必须严格遵守！）
Thinking:
[你的内部思考过程，用中文，第一人称，2-5句话]

Response:
[直接输出的对话内容，不要加引号或额外说明]
"""

        return prompt

    def _parse_response(self, response: str) -> Dict[str, str]:
        """
        解析模型输出，提取 Thinking 和 Response
        """
        result = {
            "thinking": "",
            "response": ""
        }

        # 优先按格式解析
        if "Thinking:" in response and "Response:" in response:
            try:
                parts = response.split("Thinking:", 1)[1]
                thinking_part, response_part = parts.split("Response:", 1)
                result["thinking"] = thinking_part.strip()
                result["response"] = response_part.strip()
            except:
                # 解析失败，回退
                result["response"] = response.strip()
        elif "Response:" in response:
            result["response"] = response.split("Response:", 1)[1].strip()
        else:
            # 无明确格式，整个作为 response
            result["response"] = response.strip()

        return result