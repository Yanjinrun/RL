"""
用户模拟器主程序
"""
import json
import os
import argparse
from pathlib import Path
from scripts import (
    QwenAPIClient,
    PersonaGenerator,
    BackgroundGenerator,
    StoryGenerator,
    DialogueGenerator
)
import config


class UserSimulator:
    """用户模拟器主类"""
    
    def __init__(self, api_key: str = None):
        """
        初始化用户模拟器
        
        Args:
            api_key: API密钥，如果不提供则使用配置文件中的
        """
        self.api_key = api_key or config.API_KEY
        self.api_client = QwenAPIClient(self.api_key, config.API_BASE_URL)
        
        # 初始化各个生成器
        self.persona_generator = PersonaGenerator(self.api_client)
        self.background_generator = BackgroundGenerator(self.api_client)
        self.story_generator = StoryGenerator(self.api_client)
        self.dialogue_generator = DialogueGenerator(self.api_client)
    
    def generate_persona(self, raw_persona: dict) -> dict:
        """
        生成患者画像
        
        Args:
            raw_persona: 原始患者画像（字典格式）
            
        Returns:
            生成的患者画像文本
        """
        print("正在生成患者画像...")
        persona_text = self.persona_generator.generate_persona(raw_persona)
        print("患者画像生成完成！")
        return persona_text
    
    def generate_background(self, persona: dict, dialogue_topic: str) -> str:
        """
        生成24小时生活状态
        
        Args:
            persona: 患者画像（字典格式）
            dialogue_topic: 对话主题
            
        Returns:
            24小时生活状态文本
        """
        print("正在生成24小时生活状态...")
        background = self.background_generator.generate_background(persona, dialogue_topic)
        print("24小时生活状态生成完成！")
        return background
    
    def generate_story(self, persona: dict, topic: str) -> str:
        """
        生成故事背景
        
        Args:
            persona: 患者画像（字典格式）
            topic: 对话主题
            
        Returns:
            故事背景文本
        """
        print("正在生成故事背景...")
        story = self.story_generator.generate_story(persona, topic)
        print("故事背景生成完成！")
        return story
    
    def generate_dialogue_turn(self,
                               persona: dict,
                               dialogue_topic: str,
                               background: str,
                               dialogue_history: list = None,
                               story: str = None) -> dict:
        """
        生成一轮患者对话
        
        Args:
            persona: 患者画像（字典格式）
            dialogue_topic: 对话主题
            background: 24小时生活状态
            dialogue_history: 对话历史
            story: 故事背景（可选）
            
        Returns:
            包含thinking和response的字典
        """
        print("正在生成患者对话...")
        result = self.dialogue_generator.generate_response(
            persona=persona,
            dialogue_topic=dialogue_topic,
            background=background,
            dialogue_history=dialogue_history or [],
            story=story
        )
        print("患者对话生成完成！")
        return result
    
    def simulate_conversation(self,
                             persona: dict,
                             dialogue_topic: str,
                             max_turns: int = 10,
                             return_full_data: bool = False) -> list:
        """
        模拟完整对话
        
        Args:
            persona: 患者画像（字典格式）
            dialogue_topic: 对话主题
            max_turns: 最大对话轮数
            return_full_data: 是否返回完整数据（包括metadata）
            
        Returns:
            如果return_full_data=True，返回包含metadata的字典；否则返回对话历史列表
        """
        # 生成背景和故事
        background = self.generate_background(persona, dialogue_topic)
        story = self.generate_story(persona, dialogue_topic)
        
        # 初始化对话历史
        dialogue_history = []
        
        # 生成多轮对话
        for turn in range(max_turns):
            print(f"\n=== 第 {turn + 1} 轮对话 ===")
            
            # 生成患者回复
            patient_response = self.generate_dialogue_turn(
                persona=persona,
                dialogue_topic=dialogue_topic,
                background=background,
                dialogue_history=dialogue_history,
                story=story
            )
            
            # 添加到历史
            dialogue_history.append({
                "role": "user",
                "content": patient_response["response"],
                "thinking": patient_response.get("thinking", "")
            })
            
            print(f"患者: {patient_response['response']}")
            if patient_response.get("thinking"):
                print(f"[思考]: {patient_response['thinking']}")
            
            # 这里可以添加照护师回复的逻辑
            # 目前只生成患者对话
        
        if return_full_data:
            return {
                "dialogue_history": dialogue_history,
                "persona": persona,
                "background": background,
                "story": story,
                "dialogue_topic": dialogue_topic
            }
        else:
            return dialogue_history


def load_persona_from_json(file_path: str) -> dict:
    """从JSON文件加载患者画像"""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="用户模拟器")
    parser.add_argument("--mode", type=str, choices=["persona", "background", "story", "dialogue", "conversation"],
                       default="conversation", help="运行模式")
    parser.add_argument("--persona-file", type=str, help="患者画像JSON文件路径")
    parser.add_argument("--topic", type=str, help="对话主题")
    parser.add_argument("--api-key", type=str, help="API密钥")
    parser.add_argument("--output", type=str, help="输出文件路径")
    parser.add_argument("--max-turns", type=int, default=10, help="最大对话轮数")
    
    args = parser.parse_args()
    
    # 初始化模拟器
    simulator = UserSimulator(api_key=args.api_key)
    
    # 加载患者画像
    if args.persona_file:
        persona = load_persona_from_json(args.persona_file)
    else:
        # 使用示例画像
        persona = {
            "基本信息": {
                "性别": "女",
                "年龄": 61
            },
            "信任程度": {
                "对系统的专业能力信任程度": "高度信任：可委托，遵从",
                "对系统的善意与动机的信任程度": "谨慎：谨慎接受建议",
                "隐私与数据控制的信任程度": "目的清晰可授权",
                "个性化贴合度的信任程度": "高度配合：认为系统很了解我，像私人教练"
            },
            "医学专业性": {
                "药物作用、剂量、用法、半衰期等基础认知": "无",
                "生活方式干预的正确认识": "正确理解",
                "药物禁忌、不耐受、不良反应、禁忌等认知": "有",
                "慢性病的长期风险的认知": "无",
                "筛查、诊断、检查结果、监测的基础认知": "无",
                "慢病数据的基础认知": "无"
            },
            "依从性": {
                "行动力依从性": "答应后有行动力",
                "药物依从性": "药物依从性",
                "沟通依从性": "沟通依从性",
                "反馈依从性": "反馈依从性差",
                "生活方式依从性": "生活方式依从性差",
                "多病共管/联合用药依从性": "多病共管/联合用药依从性好",
                "异常/风险处置依从性": "异常/风险处置依从性差"
            },
            "认知程度": {
                "语言/文化素养": "能用数字工具或图表作为自我管理的工具，自我整理与执行",
                "数据解读与趋势": "只看单次值，不能正确认识正常的波动",
                "风险认知": "对风险完全不敏感或者完全忽略",
                "认知偏差": "了解关键机制和长期风险，可解释简单因果链",
                "奖励敏感程度": "奖励成为目标或者兴趣，能持续被激励",
                "阴谋论、万能疗法、误导信息、谣言、错误信息的识别": "无法识别，盲目相信或转发"
            },
            "人物底色": "焦虑确认的守线者"
        }
    
    # 设置对话主题
    topic = args.topic or "患者上午带娃在游乐园玩，中午在外面的餐厅吃饭。血糖最高值达到了16.4mmol/L，刚刚补打了胰岛素，补打得有点晚了。患者想先像平常一样和照护师分享一下血糖测量数据，再让照护师分析分析今天的血糖值飙升到这么高的原因。"
    
    # 根据模式执行
    if args.mode == "persona":
        result = simulator.generate_persona(persona)
        print("\n=== 生成的患者画像 ===")
        print(result)
        
    elif args.mode == "background":
        result = simulator.generate_background(persona, topic)
        print("\n=== 生成的24小时生活状态 ===")
        print(result)
        
    elif args.mode == "story":
        result = simulator.generate_story(persona, topic)
        print("\n=== 生成的故事背景 ===")
        print(result)
        
    elif args.mode == "dialogue":
        # 需要先生成背景
        background = simulator.generate_background(persona, topic)
        result = simulator.generate_dialogue_turn(persona, topic, background)
        print("\n=== 生成的患者对话 ===")
        print(f"思考: {result.get('thinking', '')}")
        print(f"回复: {result.get('response', '')}")
        
    elif args.mode == "conversation":
        # 获取完整数据（包括metadata）
        full_data = simulator.simulate_conversation(persona, topic, args.max_turns, return_full_data=True)
        dialogue_history = full_data["dialogue_history"]
        
        print("\n=== 完整对话 ===")
        for i, turn in enumerate(dialogue_history):
            print(f"\n第 {i+1} 轮:")
            if turn.get("thinking"):
                print(f"  思考: {turn['thinking']}")
            print(f"  患者: {turn['content']}")
        
        # 保存原始结果
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(full_data, f, ensure_ascii=False, indent=2)
            print(f"\n对话已保存到: {output_path}")


if __name__ == "__main__":
    main()

