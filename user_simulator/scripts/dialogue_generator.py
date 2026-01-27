"""
患者对话生成模块
生成患者与照护师的多轮对话
"""
from typing import Dict, Any, List, Optional
from .api_client import QwenAPIClient


class DialogueGenerator:
    """患者对话生成器"""
    
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
            dialogue_history: 对话历史，格式: [{"role": "user/assistant", "content": "..."}, ...]
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
            temperature=0.65,
            max_tokens=2000
        )
        
        # 解析结果
        return self._parse_response(result)
    
    def _build_dialogue_prompt(self,
                               persona: Dict[str, Any],
                               dialogue_topic: str,
                               background: str,
                               dialogue_history: List[Dict[str, str]],
                               story: Optional[str] = None) -> str:
        """构建对话生成的提示词"""
        
        prompt = """### 任务描述
你是一位血糖异常患者。请围绕对话主题，再结合患者用户画像的内容，来生成一个回合制的对话。

### 核心规则：该回合制的对话必有"开场→互动→聚焦→收束"的节奏，避免首轮就把对话主题直接1.阶段推进：对话分4个阶段，必须按序推进，不可跳级：
①开场铺垫：建立场景与动机，例如主诉、情绪、诉求或者打招呼
②互动或补充：补充自己的关键要素，或者回应照护师的追问，目的是进一步明确自己的诉求。
③聚焦结果：判断照护师的结论或建议是否聚焦对话主题，是否满足自己的要求，以及是否解答自己的疑问。
④收束对话：若已经完成对话主题的交流目的，交流问题已全覆盖，即可收束对话。
2.**超级重要收束规则（必须严格遵守，优先级最高！）**：
- 如果照护师已经连续2~3次给出安慰、建议或解答，且你的疑问本质上已解决（即使还有小细节），**本轮必须主动收束**。
- 收束方式：用自然结束语，如“谢谢，我明白了”“嗯，感觉好多了”“那我先试试看”“聊了这么多，心里有底了，谢谢～”“谢谢，我先去尝试一下”。
- **禁止无限追问**：如果本轮问题和上上轮问题本质相同（只是换了场景/说法），视为重复，必须收束而不是继续问。
- 当前对话已进行 {current_turn} 轮（替换为实际轮次）。如果轮次 >= 10，你有50%概率选择收束，而不是继续提问。
- 每回合只做1件事（陈述/回答/确认/提问四选一），最多1个问题。
- 长度约束：每回合8~30字为主；必要时可到40字，也可能短至1~5个字。但不得推倒多个话题。
2. 每回合动作上限：只做1件事（陈述/回答/确认/提问四选一），最多1个问题。
3. 每回合数据上限：最多只能提供1个新的数据。
4. 长度约束：每回合8~30字为主；必要时可到40字，也可能根据患者用户画像的具体特点，短至1~5个字的回复。但不得推倒多个话题。
5. 主题聚焦：只围绕对话主题推进；不得在第1~2回合主动提名/判断名/要求处方。
6. 承接对方：根据患者用户画像的特点，决定是否回应上一句照护师的回复。
7.收束触发条件：- 如果照护师已经连续2~3次给出你真正关心的答案/建议/安慰，且你内心觉得“差不多懂了/安心了”，必须立刻收束。
   - 收束方式：可以说“谢谢，我明白了”“嗯，感觉好多了”“那我先试试看”“我先消化一下，谢谢你”“今天聊得差不多了”等自然结束语。
   - 禁止无限追问：如果本轮问题和上上轮问题本质相同（只是换了场景/说法），视为重复，必须收束而不是继续问。
   - 轮次达到12~18轮时，如果还没收束，也要主动温和结束（例如：“聊了这么多，我心里有底了，谢谢你～”）。

### 任务要求
1. 回合制对话的内容，请围绕对话主题，不要跑题。
2. 你想把主题设计好对话的节奏，对话切入到主题应该是有铺垫的，循序渐进的，是由上下文发展而来的。请不要首轮对话就直入主题！！！首轮去铺垫一些与主诉有关的相关背景！！！
3. 语言的特点、类型、长度和互动的节奏，参照"语言表现层与互动干扰项"的内容来进行设计，也需要符合线上场景的口语化表达的特点。
4. 患者的对话主动性以及配合程度，参照"语言表现层与互动干扰项"的内容来进行设计。
5. 适度体现互动干扰节奏的内容，但不要过度放大干扰项。
6. 当照护师的结论已经满足你的需求，或者已经解决你的疑问，请及时收束对话。

### 回复生成流程

1. 理解输入与角色代入：
请你结合以上患者的性格、对话主题、患者用户画像、语言表现层与互动干扰项、你的24小时生活状态、当前对话内容，代入患者的情绪状态和思维模式。

2. 生成精准的患者语言以及设计对应的干扰语言：生成的语言的特点、类型和长度，需与"语言表现层"的内容相符，并根据"互动干扰项"的内容来设计互动节奏。

3. 生成内心独白【作为输出中的Thinking部分】：基于患者的用户画像以及上下文，来生成患者的内心活动。
- 贴合对话主题。
- 贴合患者用户的性格特点。
- 贴合语言表现与互动干扰项的内容。

4. 构建回复【作为输出中的Response部分】：基于患者用户画像中"语言表现层"和"互动干扰项"的内容，进一步改写为与患者前端表达特征相符的回复语言，并进行口语化改造。
- 分析患者的主动性、配合程度、主动提问的能力以及信任程度来改写回复类型：陈述句还是疑问句还是感叹句。
- 患者本轮对话的回复与上下文中的患者上轮回复不能过于相似，保证对话能够围绕主题发散开来
- 使用自然真实类似人类聊天的语言，避免机械感
- 单次的回复长度避免过长。
- 根据患者用户画像的特点，若患者非医学爱好者，或者医学专业性很强，患者的语言不应有医学腔和医学用语。
- 根据患者用户画像中的主动性、信任程度等来改写回复的长度
- 你不会在单次回复中罗列过多数据
- 检查回复长度是否符合

### 输出格式
Thinking:
[生成内心独白]

Response:
[构建回复]

### 对话主题
"""
        
        prompt += f"{dialogue_topic}\n\n"
        
        # 添加故事背景（如果有）
        if story:
            prompt += f"### 故事背景\n{story}\n\n"
        
        # 添加用户画像
        import json
        prompt += "### 患者用户画像\n"
        prompt += json.dumps(persona, ensure_ascii=False, indent=2)
        prompt += "\n\n"
        
        # 添加24小时生活状态
        prompt += f"### 患者24小时生活状态\n{background}\n\n"
        
        # 添加对话历史
        if dialogue_history:
            prompt += "### 对话上下文\n"
            for msg in dialogue_history:
                role_name = "患者" if msg["role"] == "user" else "照护师"
                prompt += f"{role_name}: {msg['content']}\n"
            prompt += "\n"
        else:
            prompt += "### 对话上下文\n对话开始，你是患者，请你先发起话题，用简短的回复开启倾听\n\n"
        
        prompt = prompt.replace("{current_turn}", str(len(dialogue_history) + 1))  # 在返回prompt前替换

        return prompt
    
    def _parse_response(self, response: str) -> Dict[str, str]:
        """
        解析API返回的响应，提取Thinking和Response
        
        Args:
            response: API返回的原始文本
            
        Returns:
            包含thinking和response的字典
        """
        result = {
            "thinking": "",
            "response": ""
        }
        
        # # 尝试解析格式化的输出
        # if "Thinking:" in response:
        #     parts = response.split("Thinking:", 1)
        #     if len(parts) > 1:
        #         thinking_part = parts[1]
        #         if "Response:" in thinking_part:
        #             thinking, response_part = thinking_part.split("Response:", 1)
        #             result["thinking"] = thinking.strip()
        #             result["response"] = response_part.strip()
        #         else:
        #             result["thinking"] = thinking_part.strip()
        # elif "Response:" in response:
        #     parts = response.split("Response:", 1)
        #     result["response"] = parts[1].strip()
        # else:
        #     # 如果没有明确格式，将整个响应作为response
        #     result["response"] = response.strip()
        
        # return result

        if "Response:" in response:
            parts = response.split("Response:", 1)
            result["response"] = parts[1].strip()
        else:
            result["response"] = response.strip()
    
        return result

