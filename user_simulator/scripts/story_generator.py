"""
故事生成模块
根据主题和患者特点生成故事背景
"""
from typing import Dict, Any
from .api_client import QwenAPIClient


class StoryGenerator:
    """故事生成器"""
    
    def __init__(self, api_client: QwenAPIClient):
        """
        初始化故事生成器
        
        Args:
            api_client: API客户端实例
        """
        self.api_client = api_client
    
    def generate_story(self, persona: Dict[str, Any], topic: str) -> str:
        """
        生成故事背景
        
        Args:
            persona: 患者用户画像
            topic: 对话主题
            
        Returns:
            故事背景描述（不超过400字）
        """
        # 构建提示词
        prompt = self._build_story_prompt(persona, topic)
        
        # 调用API生成
        result = self.api_client.call(
            prompt=prompt,
            model="qwen-plus",
            temperature=0.8,
            max_tokens=800
        )
        
        return result
    
    def _build_story_prompt(self, persona: Dict[str, Any], topic: str) -> str:
        """构建故事生成的提示词"""
        
        prompt = """请根据主题，再结合下面患者的具体人物特点，扩写出一段话，里面需要包括主题的核心内容：背景和目的。并且这段话里要充分描写这个主题的背景，以及人物的特点。这段话不超过400个字。
注意：请不要预设对话内容和对话走向，仅产出故事背景，目的和人物在此场景里的特点。

### 患者用户画像
"""
        
        # 添加用户画像
        import json
        prompt += json.dumps(persona, ensure_ascii=False, indent=2)
        
        prompt += f"""

### 主题
{topic}
"""
        
        return prompt

