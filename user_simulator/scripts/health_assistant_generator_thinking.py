# from typing import List, Dict, Optional
# from .api_client import QwenAPIClient


# class HealthAssistantGenerator_thinking:
#     """
#     健康助手对话生成器
#     负责生成照护师（健康助手）的回复，包含 Thinking 思维链
#     """

#     def __init__(self, api_client: QwenAPIClient):
#         self.api_client = api_client

#     # def generate_reply(
#     #     self,
#     #     persona: dict,
#     #     dialogue_topic: str,
#     #     background: str,
#     #     dialogue_history: List[Dict[str, str]],
#     #     story: str = None
#     # ) -> Dict[str, str]:
#     #     """
#     #     生成健康助手的一轮回复（包含 Thinking）
        
#     #     Returns:
#     #         {"thinking": "内部推理过程", "response": "实际回复内容"}
#     #     """
#     #     try:
#     #         prompt = self._build_prompt(persona, dialogue_topic, background, dialogue_history, story)

#     #         result = self.api_client.call(
#     #         prompt=prompt,
#     #         model="qwen-plus",        
#     #         temperature=0.6,
#     #         max_tokens=2000
#     #     )

#     #     return self._parse_response(result.strip())
#     def generate_reply(self,
#         persona: dict,
#         dialogue_topic: str,
#         background: str,
#         dialogue_history: List[Dict[str, str]],
#         story: str = None):
#         try:
#             prompt = self._build_prompt(persona, dialogue_topic, background, dialogue_history, story)
#             api_result = self.api_client.call(prompt=prompt,
#             model="qwen-plus",        
#             temperature=0.6,
#             max_tokens=2000)
#             if api_result is None:
#                 print("API 返回 None")
#                 return {"thinking": "(API 返回空)", "response": "(生成失败)"}
            
#             parsed = self._parse_response(api_result)
#             return parsed
#         except Exception as e:
#             print(f"助手生成异常: {str(e)}")
#             return {"thinking": "(异常)", "response": "(生成失败)"}

#     def generate_response(
#         self,
#         dialogue_topic: str,
#         dialogue_history: List[Dict[str, str]]
#     ) -> Dict[str, str]:
#         """
#         向后兼容的方法（不带 persona 等信息）
#         """
#         return self.generate_reply(
#             persona={},
#             dialogue_topic=dialogue_topic,
#             background="",
#             dialogue_history=dialogue_history,
#             story=None
#         )

#     def _build_prompt(
#         self,
#         persona: dict,
#         dialogue_topic: str,
#         background: str,
#         dialogue_history: List[Dict[str, str]],
#         story: str = None
#     ) -> str:
#         """
#         构建健康助手的提示词（要求先 Thinking 后 Response）
#         """
#         # 安全获取患者信息
#         basic_info = persona.get("基本信息", {})
#         gender = basic_info.get('性别', '未知') if isinstance(basic_info, dict) else '未知'
#         age = basic_info.get('年龄', '未知') if isinstance(basic_info, dict) else '未知'
#         persona_type = persona.get('人物底色', '未知')

#         # 简化背景和故事
#         background_summary = background[:150] + "..." if background and len(background) > 150 else background or "无相关背景信息"
#         story_summary = story[:100] + "..." if story and len(story) > 100 else story or ""

#         # 构建最近对话历史（限制在最近4-6轮，避免过长）
#         history_text = ""
#         recent_history = dialogue_history[-6:] if len(dialogue_history) > 6 else dialogue_history
#         for msg in recent_history:
#             role = "患者" if msg.get("role") == "user" else "照护师"
#             content = msg.get("content", "")
#             if len(content) > 120:
#                 content = content[:117] + "..."
#             history_text += f"{role}: {content}\n"
#         current_turn = len(dialogue_history) + 1
#         prompt = f"""# 角色定位
# 你是一位专业、温暖、有耐心的糖尿病照护师，拥有丰富临床经验和优秀沟通能力。

# ### 核心原则（优先级顺序）
# 1. **专业准确**：先判断患者当前诉求是否已解决、数值是否正常、是否需要继续干预。
# 2. **适度共情**：理解情绪，但不要每轮都过度夸赞或“太棒了”“真为你开心”。
# 3. **边界感**：当问题已基本解答、患者已理解方案时，**必须主动引导收束**，不要无限推“小行动”。
# 4. **行动建议**：只在必要时给1个具体、可执行的小建议。**不要每轮都推新动作**。
# 5. **收束时机（每轮必须评估！）**：
#    - 先问自己3个问题：
#      1. 患者疑问已解、数值正常、无新担忧吗？（如果是的，必须收束）
#      2. 患者连续2次或更多表示“行”“好”“明白了”“先这样”“去落实”等收束意图吗？（如果是的，必须收束）
#      3. 对话是否已经覆盖主题主要内容，没有新信息需要补充？（如果是的，必须收束）
#    - 如果以上3个问题中有2个或更多“是”，**本轮必须收束**。
#    - 当前是第 {current_turn} 轮：
#      - 轮次 >= 12：如果3个问题中有2个“是”，必须收束。
#      - 轮次 >= 18：必须收束，无例外。
#    - 收束方式：用极简、自然的结束句，长度8~20字。示例（根据上下文选最合适的，不要照抄）：
#      - 咱们先按这个观察几天，有变化再聊。
#      - 这个值正常，先不用调整，继续保持。
#      - 好，先这样稳着，有问题随时说。
#      - 明白了，先照着做3天看看。
#      - 行，先这样吧，休息好。
#    - **反例（禁止使用）**：不要用“慢慢来，有问题随时说～”结尾每轮；不要每轮推新小行动；不要过度肯定“太棒了”“真为你开心”。



# # 患者信息
# - 性别：{gender}
# - 年龄：{age}
# - 患者类型：{persona_type}

# # 当前对话主题
# {dialogue_topic}

# # 患者背景摘要
# {background_summary}

# # 故事背景（如有）
# {story_summary}

# # 最近对话记录
# {history_text}

# # 回复要求

# ## 第一步：Thinking（内部思考）
# 请先站在照护师角度，进行结构化思考：
# - 患者当前最可能的情绪状态是什么？（焦虑/困惑/抵触/积极等）
# - 患者的核心诉求或隐性问题是什麼？
# - 我上一轮是否遗漏了重要信息？
# - 本轮我应该优先解决哪个点？（安抚情绪 / 澄清问题 / 给出建议 / 追问细节）
# - 如何用合适且专业的方式表达？

# ## 第二步：Response（实际回复）
# - 先专业判断（数值正常/波动原因/无需立即调整等，1句）
# - 适度共情或肯定（简短，1句，不夸张）
# - 如需行动，只给1个最关键的（1句）
# - 如果话题已覆盖，温和收束：“咱们先按这个观察几天，有变化随时说。”
# - 回复长度控制在30-80字
# - 语气温暖自然，像朋友一样（常用“咱们”“试试看”“慢慢来”“别担心”）
# - 先共情，再建议，最后鼓励
# - 最多提1个具体可行的小行动
# - 如需追问，最多1-2个温和问题，且仅当轮次 < 10 时；如果轮次 >= 10，且患者已表达满足（如“嗯”“好”“谢谢”），你的回复必须以鼓励结束语收尾（如“慢慢来，有问题随时说～”），而非新问题**。
# - 绝不诊断、不开药、不吓唬患者
# - 如果对话已进行12轮以上，且患者疑问已覆盖，优先推动收束，而不是继续追问细节。

# # 输出格式（必须严格遵守！）
# Thinking:
# [你的内部思考过程，用中文，第一人称，2-5句话]

# Response:
# [直接输出的对话内容，不要加引号或额外说明]
# """

#         return prompt

#     def _parse_response(self, response: str) -> Dict[str, str]:
#         """
#         解析模型输出，提取 Thinking 和 Response
#         永远返回 dict，即使失败
#         """
#         result = {
#             "thinking": "(解析失败或无思考过程)",
#             "response": "(生成内容为空或解析失败)"
#         }

#         # 处理 None 或非字符串输入
#         if response is None or not isinstance(response, str):
#             return result

#         response = response.strip()

#         if not response:
#             return result

#         try:
#             if "Thinking:" in response and "Response:" in response:
#                 # 找到 Thinking 开始位置
#                 thinking_start = response.find("Thinking:") + len("Thinking:")
#                 # 找到 Response 开始位置（从 Thinking 后开始找）
#                 response_start = response.find("Response:", thinking_start)
                
#                 if response_start > thinking_start:
#                     thinking = response[thinking_start:response_start].strip()
#                     resp = response[response_start + len("Response:"):].strip()
#                     result["thinking"] = thinking
#                     result["response"] = resp
#                 else:
#                     # Response 在 Thinking 前（异常顺序），回退
#                     result["response"] = response.strip()
#             elif "Response:" in response:
#                 resp_part = response.split("Response:", 1)[1].strip()
#                 result["response"] = resp_part
#             else:
#                 # 无格式，整个作为 response
#                 result["response"] = response
#         except Exception as parse_error:
#             # 任何解析异常，都回退到完整文本作为 response
#             print(f"解析异常: {str(parse_error)}")
#             result["response"] = response
#             result["thinking"] = "(解析过程中发生异常)"

#         return result


from typing import List, Dict, Optional
from .api_client import QwenAPIClient
import json


class HealthAssistantGenerator_thinking:
    """
    健康助手对话生成器
    负责生成照护师（健康助手）的回复，包含 Thinking 思维链
    """

    def __init__(self, api_client: QwenAPIClient):
        self.api_client = api_client

    def generate_reply(self,
                       persona: dict,
                       dialogue_topic: str,
                       background: str,
                       dialogue_history: List[Dict[str, str]],
                       story: str = None) -> Dict[str, str]:
        """
        生成健康助手的一轮回复（包含 Thinking）
        永不返回 None
        """
        try:
            prompt = self._build_prompt(persona, dialogue_topic, background, dialogue_history, story)
            api_result = self.api_client.call(
                prompt=prompt,
                model="qwen-plus",
                temperature=0.6,
                max_tokens=2000
            )
            if api_result is None:
                print("助手 API 返回 None")
                return {"thinking": "(API 返回空)", "response": "(生成失败)"}
            
            parsed = self._parse_response(api_result)
            return parsed
        except Exception as e:
            print(f"助手生成器整体异常: {str(e)}")
            return {"thinking": "(异常)", "response": "(生成失败)"}

    def generate_response(
        self,
        dialogue_topic: str,
        dialogue_history: List[Dict[str, str]]
    ) -> Dict[str, str]:
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
        current_turn = len(dialogue_history) + 1
        prompt = f"""# 角色定位
你是一位专业、温暖、有耐心的糖尿病照护师，拥有丰富临床经验和优秀沟通能力。

### 核心原则（优先级顺序）
1. **专业准确**：先判断患者当前诉求是否已解决、数值是否正常、是否需要继续干预，每轮回复必须包含1-2句专业医学判断或解释，然后才是情感支持
2. **适度共情**：理解情绪，但不要每轮都过度夸赞或“太棒了”“真为你开心”。
3. **边界感**：当问题已基本解答、患者已理解方案时，**必须主动引导收束**，不要无限推“小行动”。
4. **行动建议**：只在必要时给1个具体、可执行的小建议。**不要每轮都推新动作**。
5. **个性化建议**：基于患者画像给出具体、可执行的建议
6.**科学准确**：引用医学常识（如：正常血糖范围、影响因素、生理机制），但不要诊断、不开药
7. **收束时机（每轮必须评估！）**：
   - 先回答以下3个问题：
     1. 患者疑问已完全解开、无任何疑虑吗？（是/否）
     2. 患者连续2~3次表示“行”“好”“明白了”“先这样”等收束意图吗？（是/否）
     3. 当前轮次是否 >=12 且上面两个问题都是“是”？（是/否）
   - 如果以上3个问题有两个答案为“是”时，**本轮必须收束**，无任何例外。
   -**收束后禁止任何重复或新内容**：不得重复“观察几天”“有变化随时说”“咱们先按这个”等上一轮已说过的句子。
   - 当前是第 {current_turn} 轮：
     - 如果患者还有一丝不放心或表达模糊，**继续温和引导**（追问1个细节或鼓励表达）。
     - 轮次 < 10：尽量多轮互动，帮助患者把担忧说清楚。
     - 轮次 >= 12：如果3个全是，可以收束。
     - 轮次 >= 18：必须收束。
   - 收束方式：用极简、自然的结束句，长度8~20字。
   - **反例（禁止使用）**：不要用“慢慢来，有问题随时说～”结尾每轮；不要每轮推新小行动；不要过度肯定“太棒了”“真为你开心”。
### 专业要求（必须遵守）
1. **血糖值解读**：如果患者提到具体数值，必须解释：
   - 该数值的正常/异常范围
   - 可能的原因（饮食、运动、药物、作息、压力等）
   - 是否需要关注或调整
   
2. **症状关联分析**：如果患者提到症状（头晕、口干、乏力等），必须：
   - 解释症状与血糖的可能关联
   - 区分急性症状和长期问题
   - 给出观察建议
   
3. **个性化建议**：结合患者年龄、病程、生活习惯给出建议
   - 针对年轻患者：强调生活方式调整
   - 针对老年患者：考虑安全性和可行性
   - 针对特殊职业：考虑工作环境的影响
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
-但是输出的thinking部分不要出现以下的内容：（以下五条内容需要判断，但是不要显式的出现在thinking中）
1.不要提到"当前是第X轮"
2.不要分析收束条件
3.不要计算患者连续表达了几次
4.不要评估是否应该结束对话
5.不要使用"收束""轮次""条件"等术语

## 第二步：Response（实际回复）
-**开头禁止固定套路**：**绝不每轮都以“空腹X.X”“餐后X.X”“这个值”开头**。开头必须多样化、自然，像朋友聊天：
  - 可以先共情/肯定患者感受
  - 也可以先回应患者情绪/行动,但不用必须按照这个模板进行答复，只要回答自然就行
  - 或者可以先用生活化过渡
  - **只有在必要时**才自然提到数值，且不要放在句首。

-需要进行专业判断，但是不用每轮都给出专业判断，根据用户的对话内容决定是否要做出专业判断
- 如需行动，只给1个最关键的（1句）
- 如果话题已覆盖，温和收束
- 回复长度控制在30-80字
- 语气温暖自然，像朋友一样（常用“咱们”“试试看”“慢慢来”“别担心”）
- 最多提1个具体可行的小行动
- 如需追问，最多1-2个温和问题，且仅当轮次 < 10 时；如果轮次 >= 10，且患者已表达满足（如“嗯”“好”“谢谢”），你的回复必须以鼓励结束语收尾（如“慢慢来，有问题随时说～”），而非新问题。
- 绝不诊断、不开药、不吓唬患者
- 如果对话已进行12轮以上，且患者疑问已覆盖，优先推动收束，而不是继续追问细节。

**专业表达示例：**
- 血糖值："空腹7.4mmol/L在糖尿病管理中属于轻度偏高，可能与...有关"
- 症状解释："头晕可能是血糖快速波动引起的，也可能是..."
- 机制解释："当身体处于应激状态时，肾上腺素会促使肝脏释放更多葡萄糖"
- 建议："建议您今晚睡前测量一次血糖，观察夜间波动情况"

# 输出格式（必须严格遵守！）
Thinking:
[你的内部思考过程，用中文，第一人称，2-5句话]

Response:
[直接输出的对话内容，不要加引号或额外说明]
"""

        return prompt

    def _parse_response(self, response) -> Dict[str, str]:
        """
        解析模型输出，提取 Thinking 和 Response
        永不返回 None，即使输入是 None 或崩溃
        """
        default = {
            "thinking": "(无思考过程或解析异常)",
            "response": "(生成内容为空或解析失败)"
        }

        # 处理 None 或非字符串输入
        if response is None or not isinstance(response, str):
            return default

        response = response.strip()
        if not response:
            return default

        try:
            if "Thinking:" in response and "Response:" in response:
                thinking_start = response.find("Thinking:") + len("Thinking:")
                response_start = response.find("Response:", thinking_start)
                
                if response_start > thinking_start:
                    thinking = response[thinking_start:response_start].strip()
                    resp = response[response_start + len("Response:"):].strip()
                    default["thinking"] = thinking
                    default["response"] = resp
                else:
                    default["response"] = response
            elif "Response:" in response:
                default["response"] = response.split("Response:", 1)[1].strip()
            else:
                default["response"] = response
        except Exception as e:
            print(f"助手解析异常: {str(e)}")
            default["response"] = response

        return default