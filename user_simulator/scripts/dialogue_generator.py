# """
# 患者对话生成模块
# 生成患者与照护师的多轮对话
# """
# from typing import Dict, Any, List, Optional
# from .api_client import QwenAPIClient


# class DialogueGenerator:
#     """患者对话生成器"""
    
#     def __init__(self, api_client: QwenAPIClient):
#         """
#         初始化对话生成器
        
#         Args:
#             api_client: API客户端实例
#         """
#         self.api_client = api_client
    
#     def generate_response(self,
#                           persona: Dict[str, Any],
#                           dialogue_topic: str,
#                           background: str,
#                           dialogue_history: List[Dict[str, str]],
#                           story: Optional[str] = None) -> Dict[str, str]:
#         """
#         生成患者的一轮对话回复
        
#         Args:
#             persona: 患者用户画像
#             dialogue_topic: 对话主题
#             background: 24小时生活状态
#             dialogue_history: 对话历史，格式: [{"role": "user/assistant", "content": "..."}, ...]
#             story: 故事背景（可选）
            
#         Returns:
#             包含Thinking和Response的字典
#         """
#         # 构建提示词
#         prompt = self._build_dialogue_prompt(persona, dialogue_topic, background, dialogue_history, story)
        
#         # 调用API生成
#         result = self.api_client.call(
#             prompt=prompt,
#             model="qwen-plus",
#             temperature=0.65,
#             max_tokens=2000
#         )
        
#         # 解析结果
#         return self._parse_response(result)
    
#     def _build_dialogue_prompt(self,
#                                persona: Dict[str, Any],
#                                dialogue_topic: str,
#                                background: str,
#                                dialogue_history: List[Dict[str, str]],
#                                story: Optional[str] = None) -> str:
#         """构建对话生成的提示词"""
#         current_turn = len(dialogue_history) + 1
        
#         prompt = f"""### 任务描述
# 你是一位血糖异常患者。请围绕对话主题，结合患者用户画像，生成一轮患者回复。

# ### 核心规则（必须严格遵守，优先级最高！）
# 对话必须遵循"开场→互动→聚焦→收束"节奏，不可跳级：
# 1. 开场：首轮建立场景、情绪、主诉，不要直奔主题。
# 2. 互动/补充：回应照护师、补充信息，明确诉求。
# 3. 聚焦：判断照护师建议是否解答疑问、满足需求。
# 4. 收束：疑问真正解决、内心有底时，必须主动结束。

# **收束判断（每轮必须认真评估）**：
# - 只有当你内心真正觉得“问题已解决”“诉求得到满足”“已经安心/有底”时，才收束。
# - 如果照护师连续2~3次给出你真正关心的答案/建议/安慰，且你没有新的疑问或担忧，**本轮必须主动收束**。
# - 禁止无限追问：本轮问题与上上轮本质相同（换说法/场景），视为重复，必须结束。
# - 当前是第 {current_turn} 轮：
#   - 轮次 >= 10：如果你觉得话题已覆盖，优先考虑收束
#   - 轮次 >= 20：除非还有关键未解疑问，否则必须收束
# - 收束方式：用**自然、多样、口语化**结束语，长度10~30字，必须包含感谢/行动/安心感。
#   **必须个性化！禁止重复模板句**。根据上下文和情绪变化，例如：
#   - 谢谢你，我今晚就早点睡试试～
#   - 嗯，方向清楚了，先去按你说的做，谢谢！
#   - 感觉踏实多了，谢谢你的耐心～
#   - 好的，我懂了，先稳住再说，谢谢你！
#   - 心里亮堂了，先去执行，谢谢～
#   - 太感谢了，我先消化一下这些建议。
#   - 嗯，有谱了，谢谢你的陪伴！
#   - 谢谢，聊得真开心，先去调整一下～
#   - 感觉好多了，先试几天看看，谢谢！
#   - 明白了～心里有底了，先去行动起来。
#   - 谢谢你，我先去试试你说的办法～
#   - 嗯嗯，谢谢～先稳住再说。
#   - 好，我记住了，先照着做几天。
#   - 谢谢，方向有了，我先去试试看～
#   - 聊了这么多，我心里舒服多了，谢谢你！
#   - 谢谢你的建议，我先去落实～

# 其他规则：
# - 每回合只做1件事，最多1个问题。
# - 最多提供1个新数据。
# - 回复长度8~30字为主，必要时到40字。
# - 语言口语化，根据画像调整（非医学爱好者避免医学术语）。
# - 主动性、配合度参照画像中的语言表现层与互动干扰项。

# ### 回复生成流程
# 1. 代入患者情绪、思维模式。
# 2. 先判断本轮是否满足收束条件（最重要！）。
# 3. 生成回复（Response）：自然口语化，与上轮不相似。

# ### 输出格式（必须严格遵守）
# Response:
# [患者回复，一句话]

# ### 对话主题
# {dialogue_topic}

# ### 患者用户画像
# {json.dumps(persona, ensure_ascii=False, indent=2)}

# ### 患者24小时生活状态
# {background}

# ### 对话上下文
# """
        
#         prompt += f"{dialogue_topic}\n\n"
        
#         # 添加故事背景（如果有）
#         if story:
#             prompt += f"### 故事背景\n{story}\n\n"
        
#         # 添加用户画像
#         import json
#         prompt += "### 患者用户画像\n"
#         prompt += json.dumps(persona, ensure_ascii=False, indent=2)
#         prompt += "\n\n"
        
#         # 添加24小时生活状态
#         prompt += f"### 患者24小时生活状态\n{background}\n\n"
        
#         # 添加对话历史
#         if dialogue_history:
#             prompt += "### 对话上下文\n"
#             for msg in dialogue_history:
#                 role_name = "患者" if msg["role"] == "user" else "照护师"
#                 prompt += f"{role_name}: {msg['content']}\n"
#             prompt += "\n"
#         else:
#             prompt += "### 对话上下文\n对话开始，你是患者，请你先发起话题，用简短的回复开启倾听\n\n"
        
#         prompt = prompt.replace("{current_turn}", str(len(dialogue_history) + 1))  # 在返回prompt前替换

#         return prompt
    
#     def _parse_response(self, response: str) -> Dict[str, str]:
#         """
#         解析API返回的响应，提取Thinking和Response
        
#         Args:
#             response: API返回的原始文本
            
#         Returns:
#             包含thinking和response的字典
#         """
#         result = {
#             "thinking": "",
#             "response": ""
#         }
        
#         # # 尝试解析格式化的输出
#         # if "Thinking:" in response:
#         #     parts = response.split("Thinking:", 1)
#         #     if len(parts) > 1:
#         #         thinking_part = parts[1]
#         #         if "Response:" in thinking_part:
#         #             thinking, response_part = thinking_part.split("Response:", 1)
#         #             result["thinking"] = thinking.strip()
#         #             result["response"] = response_part.strip()
#         #         else:
#         #             result["thinking"] = thinking_part.strip()
#         # elif "Response:" in response:
#         #     parts = response.split("Response:", 1)
#         #     result["response"] = parts[1].strip()
#         # else:
#         #     # 如果没有明确格式，将整个响应作为response
#         #     result["response"] = response.strip()
        
#         # return result

#         if "Response:" in response:
#             parts = response.split("Response:", 1)
#             result["response"] = parts[1].strip()
#         else:
#             result["response"] = response.strip()
    
#         return result
"""
患者对话生成模块
生成患者与照护师的多轮对话
"""
from typing import Dict, Any, List, Optional
import json
from .api_client import QwenAPIClient


class DialogueGenerator:
    """患者对话生成器"""
    PATIENT_END_KEYWORDS = [
    "先这样", "明白了", "先去", "去落实", "先睡", "晚安", 
    "就这样", "先稳", "先观察", "先试试", "先这样吧", 
    "行，先这样", "好的，谢谢", "谢谢，再见", "明白了，谢谢",
    "先不聊了", "我先去忙", "结束", "差不多了", "可以了",
    "今天就到这", "先这样哈", "我先下了", "拜拜", "回头聊",
    "我明白了", "清楚了", "懂了", "了解", "知道了"
]

    ASSISTANT_END_KEYWORDS = [
    "先观察", "有变化再聊", "先这样", "慢慢来", "先稳着", 
    "先休息", "先这样吧", "下次见", "晚安", "再见",
    "咱们先这样", "先按这个来", "先试试看", "有情况再说",
    "先聊到这", "今天先这样", "你先试试", "回头联系"
]
    
    
    def __init__(self, api_client: QwenAPIClient):
        """
        初始化对话生成器
        
        Args:
            api_client: API客户端实例
        """
        self.api_client = api_client
    
    def generate_response(self,
                          persona: Dict[str, Any],
                          dialogue_topic: str,
                          background: str,
                          dialogue_history: List[Dict[str, str]],
                          story: Optional[str] = None) -> Dict[str, str]:
        """
        生成患者的一轮对话回复
        
        Args:
            persona: 患者用户画像
            dialogue_topic: 对话主题
            background: 24小时生活状态
            dialogue_history: 对话历史
            story: 故事背景（可选）
            
        Returns:
            包含Thinking和Response的字典
        """
        # 构建提示词
        prompt = self._build_dialogue_prompt(persona, dialogue_topic, background, dialogue_history, story)
        
        # 调用API生成
        result = self.api_client.call(
            prompt=prompt,
            model="qwen-plus",
            temperature=0.6,  # 降低创造性，确保执行规则
            max_tokens=1500
        )
        
        # 解析结果（严格解析 Thinking 和 Response）
        return self._parse_response(result)
    
    def _build_dialogue_prompt(self,
                           persona: Dict[str, Any],
                           dialogue_topic: str,
                           background: str,
                           dialogue_history: List[Dict[str, str]],
                           story: Optional[str] = None) -> str:
        current_turn = len(dialogue_history) + 1
        
        prompt = f"""### 任务描述
你是一位真实的血糖异常患者，正在和照护师聊天。请围绕对话主题，结合患者画像，生成一轮自然回复。

### 核心规则（必须严格遵守，优先级最高！）
- 对话节奏：开场 → 互动/补充（可多轮） → 聚焦结果 → 自然收束。**不要过早结束**。
- 每回合只做1件事，可以是表达感受、确认理解、补充细节、自我总结，但**最多1个问题**。
-**优先使用陈述句**，带情绪、自我反思或行动承诺（如“我觉得……”“我打算……”“这样应该行吧”）。
- 回复长度8~40字为主。
- 语言口语化，根据画像调整。
- **多样化表达**：每轮回复必须和上轮不同，避免重复词句或结构（如不要每轮都说“明早测完发你”）。

**自然收束判断（每轮必须先评估，但不要过早结束！）**：
- 先问自己3个问题：
  1. 本轮还有新的疑问/担忧/想确认的点吗？（如果有，继续问）
  2. 照护师的回答是否让我完全放心、没有一丝疑虑？（如果还有疑虑，继续追问或表达）
  3. 我是否已经清楚下一步怎么做，且内心有底？（如果没底，继续互动）
- **只有3个问题有两个答案为“是”时，或轮次 >=12 时，才收束**。
- **收束后禁止重复**：不得重复上一轮已说过的行动计划或句子（如“明早测完发你”“后天再看”）。
- **严禁每轮都问问题**：如果上轮已问过，本轮优先用陈述句表达理解、感受或计划。
- 如果照护师回答后你还有一丝不放心或想再确认细节，**必须继续问或补充**。
- **严禁过早结束**：至少互动3~5轮后再考虑收束。
### 强制收束规则（必须严格遵守！）
**在以下情况下，你本轮必须使用结束语结束对话：**
1. 你的问题已经得到满意解答
2. 你知道了下一步该怎么做
3. 你感觉放心/安心/踏实了
4. 对话已进行8轮以上且话题已充分讨论

**结束语必须明确包含结束意图！** 例如：
- "行，先这样吧，谢谢你。"
- "好的，我明白了，先按你说的做。"
- "心里踏实多了，谢谢，我先去忙了。"
- "知道了，我去试试，有问题再找你。"
- "谢谢，先这样，再见。"

**禁止**在应该结束时继续问问题！
**禁止**使用模糊的、不含结束意图的回复！
- 当前是第 {current_turn} 轮：
  - 轮次 < 8：尽量继续互动，可以提出新的问题，不要轻易收束。
  - 轮次 >= 12：如果3个问题全“是”，可以收束。
  - 轮次 >= 18：必须收束。
- 收束方式：用极简、自然、日常结束句，长度8~15字。示例：
  - 那我先去试试。
  - 嗯，明白了，先这样。
  - 行，我记住了。
  - 好，先照着做几天。
  - 明白了，先稳住。
  - 行，先这样吧。
  - 明白了，晚安。
- **反例（禁止使用）**：不要用“谢谢”“心里踏实”“暖暖的”“懂我”等词；不要每轮感谢。

### 回复生成流程
1. 评估收束：严格回答3个问题。如果有两个答案为“是”，生成结束句；否则，继续正常互动。
2. 生成回复（Response）：自然口语化，一句话。如果没收束，可以追问细节或表达情绪。
    ### 输出格式（必须严格遵守）
    
    Response:
    [患者回复，一句话]

    ### 对话主题
    {dialogue_topic}

    ### 患者用户画像
    {json.dumps(persona, ensure_ascii=False, indent=2)}

    ### 患者24小时生活状态
    {background}

    ### 对话上下文
    """
        
        if dialogue_history:
            for msg in dialogue_history:
                role_name = "患者" if msg["role"] == "user" else "照护师"
                prompt += f"{role_name}: {msg['content']}\n"
            prompt += "\n"
        else:
            prompt += "### 对话上下文\n对话开始，你是患者，请先发起话题，用简短回复开启倾听\n\n"
        
        if story:
            prompt += f"### 故事背景\n{story}\n\n"
        
        return prompt
    def _parse_response(self, response: str) -> Dict[str, str]:
        """
        严格解析API返回的响应，提取Thinking和Response
        """
        result = {"thinking": "(无思考过程)", "response": "(解析失败)"}
        
        # 严格按格式分割
        thinking_marker = "Thinking:"
        response_marker = "Response:"
        
        if thinking_marker in response and response_marker in response:
            # 先找 Thinking
            thinking_start = response.find(thinking_marker) + len(thinking_marker)
            response_start = response.find(response_marker, thinking_start)
            
            if response_start > thinking_start:
                thinking = response[thinking_start:response_start].strip()
                response_text = response[response_start + len(response_marker):].strip()
                result["thinking"] = thinking
                result["response"] = response_text
        
        # 兜底：如果没有格式，取最后一段作为 response
        if result["response"] == "(解析失败)":
            lines = response.splitlines()
            for line in reversed(lines):
                stripped = line.strip()
                if stripped:
                    result["response"] = stripped
                    break
        
        return result
