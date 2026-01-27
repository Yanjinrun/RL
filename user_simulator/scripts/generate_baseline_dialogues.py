"""
基线对话生成脚本
使用场景提示词驱动"病人模拟器"与"通用AI"进行对话生成
"""
import json
import os
import argparse
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

from scripts import (
    QwenAPIClient,
    DialogueGenerator,
)
from scripts.generic_ai_generator import GenericAIGenerator
import config


class BaselineDialogueGenerator:
    """基线对话生成器"""
    
    def __init__(self, api_key: str = None):
        """
        初始化基线对话生成器
        
        Args:
            api_key: API密钥，如果不提供则使用配置文件中的
        """
        self.api_key = api_key or config.API_KEY
        if not self.api_key:
            raise ValueError("API密钥未设置，请设置环境变量 QWEN_API_KEY 或在config.py中配置")
        
        self.api_client = QwenAPIClient(self.api_key, config.API_BASE_URL)
        
        # 初始化生成器
        self.dialogue_generator = DialogueGenerator(self.api_client)
        self.generic_ai_generator = GenericAIGenerator(self.api_client)
    
    def load_scene_prompts(self, prompts_file: str) -> List[Dict[str, Any]]:
        """
        加载场景提示词
        
        Args:
            prompts_file: 场景提示词JSON文件路径
            
        Returns:
            场景提示词列表
        """
        with open(prompts_file, 'r', encoding='utf-8') as f:
            scenes = json.load(f)
        return scenes
    
    def generate_dialogue_for_scene(
        self,
        scene_prompt: Dict[str, Any],
        persona: Dict[str, Any],
        max_turns: int = 10
    ) -> Dict[str, Any]:
        """
        为单个场景生成对话
        
        Args:
            scene_prompt: 场景提示词字典
            persona: 患者画像
            max_turns: 最大对话轮数
            
        Returns:
            包含完整对话数据的字典
        """
        scene_name = scene_prompt.get("scene", "未知场景")
        scene_code = scene_prompt.get("scene_code", "")
        patient_instruction = scene_prompt.get("patient_simulator_instruction", "")
        
        print(f"\n{'='*60}")
        print(f"开始生成场景: {scene_name} ({scene_code})")
        print(f"{'='*60}")
        
        # 构建对话主题（从patient_simulator_instruction中提取）
        # 这里我们使用patient_simulator_instruction作为对话主题的一部分
        dialogue_topic = f"场景：{scene_name}\n\n{patient_instruction}"
        
        # 初始化对话历史
        dialogue_history = []
        
        # 生成多轮对话
        for turn in range(max_turns):
            print(f"\n--- 第 {turn + 1} 轮对话 ---")
            
            # 生成患者回复
            try:
                # 构建患者对话生成的提示词
                # 这里需要将patient_simulator_instruction整合到对话生成中
                patient_response = self._generate_patient_turn(
                    persona=persona,
                    scene_prompt=scene_prompt,
                    dialogue_history=dialogue_history,
                    turn_number=turn + 1
                )
                
                patient_content = patient_response.get("response", "")
                
                # 检查是否重复
                if self._is_repetitive(patient_content, dialogue_history):
                    print(f"警告: 检测到重复回复，跳过本轮")
                    print(f"重复内容: {patient_content[:50]}...")
                    # 可以选择跳过或重新生成，这里选择跳过
                    continue
                
                # 添加到历史（不包含thinking）
                dialogue_history.append({
                    "role": "user",
                    "content": patient_content
                })
                
                print(f"患者: {patient_content}")
                
                # 检查是否应该结束对话
                if self._should_end_dialogue(patient_content):
                    print("患者表示对话可以结束")
                    break
                
                # 生成通用AI回复
                generic_ai_reply = self.generic_ai_generator.generate_reply(
                    dialogue_history=dialogue_history
                )
                
                dialogue_history.append({
                    "role": "assistant",
                    "content": generic_ai_reply
                })
                
                print(f"通用AI: {generic_ai_reply}")
                
            except Exception as e:
                print(f"生成第 {turn + 1} 轮对话时出错: {str(e)}")
                break
        
        # 构建返回数据
        result = {
            "scene": scene_name,
            "scene_code": scene_code,
            "description": scene_prompt.get("description", ""),
            "dialogue_history": dialogue_history,
            "persona": persona,
            "scene_prompt": scene_prompt,
            "generated_at": datetime.now().isoformat(),
            "total_turns": len([msg for msg in dialogue_history if msg.get("role") == "user"])
        }
        
        return result
    
    def _generate_patient_turn(
        self,
        persona: Dict[str, Any],
        scene_prompt: Dict[str, Any],
        dialogue_history: List[Dict[str, str]],
        turn_number: int = 1
    ) -> Dict[str, str]:
        """
        生成患者的一轮对话
        
        Args:
            persona: 患者画像
            scene_prompt: 场景提示词
            dialogue_history: 对话历史
            
        Returns:
            包含response的字典
        """
        # 构建患者对话生成的提示词
        # 整合场景提示词中的patient_simulator_instruction
        patient_instruction = scene_prompt.get("patient_simulator_instruction", "")
        
        # 构建对话历史文本
        history_text = ""
        for msg in dialogue_history[-4:]:  # 只取最近4轮
            role = "患者" if msg.get("role") == "user" else "助手"
            content = msg.get("content", "")
            history_text += f"{role}: {content}\n"
        
        # 构建完整的提示词
        # 判断是否是第一轮
        is_first_turn = len(dialogue_history) == 0
        current_turn = turn_number
        
        prompt = f"""### 任务描述
你是一位血糖异常患者。请根据场景提示和患者用户画像，生成一轮对话回复。

### 当前对话轮次
这是第 {current_turn} 轮对话。{"这是对话的开始。" if is_first_turn else "请根据之前的对话内容，生成与之前不同的新回复。"}

### 场景提示
{patient_instruction}

### 患者用户画像
{json.dumps(persona, ensure_ascii=False, indent=2)}

### 对话历史
{history_text if history_text else "对话刚开始，这是第一轮。"}

### 核心规则
1. **对话连贯性**：必须根据对话历史生成回复，不能重复之前说过的话。如果助手已经回答了你的问题，你应该：
   - 要么确认理解并追问细节
   - 要么提出新的相关问题
   - 要么表达新的担忧或补充信息
   - 绝对不能重复完全相同的问题或陈述

2. **对话节奏**：遵循'开场铺垫→互动补充→聚焦结果→收束对话'的四阶段
   - 第一轮：开场铺垫，描述现状和核心问题
   - 后续轮次：根据助手的回复，进行确认、追问、补充或提出新问题

3. **每回合动作上限**：只做1件事（陈述/回答/确认/提问四选一），最多1个问题

4. **每回合数据上限**：最多只能提供1个新的数据

5. **长度约束**：每回合8~30字为主；必要时可到40字

6. **主题聚焦**：只围绕场景主题推进

7. **承接对方**：必须回应助手的最新回复，不能忽略助手的回答。如果助手给出了建议，你应该：
   - 确认是否理解（"所以我应该..."）
   - 追问具体步骤（"具体怎么做？"）
   - 表达担忧（"我担心..."）
   - 提供补充信息（"但是我..."）

### 重要提醒
- **禁止重复**：绝对不能重复之前轮次中已经说过的完全相同的话
- **必须变化**：每一轮的回复必须与之前不同，体现对话的推进
- **回应助手**：必须回应助手的最新回复，不能无视助手的回答

### 输出格式
请直接输出你的回复内容，不需要包含思考过程。

### 你的回复："""
        
        # 调用API生成（提高温度以增加多样性，避免重复）
        result = self.api_client.call(
            prompt=prompt,
            model="qwen-plus",
            temperature=0.9,  # 提高温度增加多样性
            max_tokens=500
        )
        
        # 解析结果
        return self._parse_patient_response(result)
    
    def _parse_patient_response(self, response: str) -> Dict[str, str]:
        """
        解析患者回复，只返回response（不包含thinking）
        
        Args:
            response: API返回的原始文本
            
        Returns:
            包含response的字典
        """
        response_text = ""
        
        # 如果包含Response:，提取Response之后的内容
        if "Response:" in response:
            response_text = response.split("Response:", 1)[1].strip()
        else:
            # 直接使用整个回复（去除可能的Thinking部分）
            # 如果包含Thinking:，只取Response之后的部分
            if "Thinking:" in response:
                # 尝试找到Response部分
                if "Response:" in response:
                    response_text = response.split("Response:", 1)[1].strip()
                else:
                    # 只有Thinking没有Response，跳过Thinking部分
                    response_text = response.split("Thinking:", 1)[1].strip() if "Thinking:" in response else response.strip()
            else:
                # 直接使用整个回复
                response_text = response.strip()
        
        return {
            "response": response_text
        }
    
    def _is_repetitive(self, response: str, dialogue_history: List[Dict[str, str]]) -> bool:
        """
        检查患者回复是否与历史回复重复
        
        Args:
            response: 当前患者回复
            dialogue_history: 对话历史
            
        Returns:
            是否重复
        """
        # 获取之前所有患者回复
        previous_responses = [
            msg.get("content", "") 
            for msg in dialogue_history 
            if msg.get("role") == "user"
        ]
        
        # 检查是否与之前的回复完全相同或高度相似
        response_clean = response.strip()
        for prev_response in previous_responses:
            prev_clean = prev_response.strip()
            # 完全相同
            if response_clean == prev_clean:
                return True
            # 高度相似（超过80%的字符相同）
            if len(response_clean) > 10 and len(prev_clean) > 10:
                similarity = len(set(response_clean) & set(prev_clean)) / max(len(set(response_clean)), len(set(prev_clean)))
                if similarity > 0.8:
                    return True
        
        return False
    
    def _should_end_dialogue(self, response: str) -> bool:
        """
        判断是否应该结束对话
        
        Args:
            response: 患者回复
            
        Returns:
            是否应该结束
        """
        # 简单的结束判断逻辑
        end_indicators = [
            "谢谢", "再见", "好的，明白了", "没问题了", 
            "清楚了", "知道了", "谢谢您", "好的，谢谢"
        ]
        response_lower = response.lower()
        return any(indicator in response_lower for indicator in end_indicators)
    
    def generate_all_scenes(
        self,
        prompts_file: str,
        persona_file: str = None,
        output_dir: str = "output/baseline_dialogues",
        max_turns: int = 10
    ):
        """
        为所有场景生成对话
        
        Args:
            prompts_file: 场景提示词JSON文件路径
            persona_file: 患者画像JSON文件路径（可选）
            output_dir: 输出目录
            max_turns: 每个场景的最大对话轮数
        """
        # 加载场景提示词
        scenes = self.load_scene_prompts(prompts_file)
        print(f"加载了 {len(scenes)} 个场景")
        
        # 加载患者画像
        if persona_file and os.path.exists(persona_file):
            with open(persona_file, 'r', encoding='utf-8') as f:
                persona_data = json.load(f)
                # 如果persona_data是列表，取第一个
                if isinstance(persona_data, list) and len(persona_data) > 0:
                    persona = persona_data[0]
                else:
                    persona = persona_data
        else:
            # 使用默认患者画像
            persona = self._get_default_persona()
        
        # 创建输出目录
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # 为每个场景生成对话
        all_results = []
        for i, scene_prompt in enumerate(scenes, 1):
            try:
                print(f"\n\n处理场景 {i}/{len(scenes)}: {scene_prompt.get('scene', '未知')}")
                result = self.generate_dialogue_for_scene(
                    scene_prompt=scene_prompt,
                    persona=persona,
                    max_turns=max_turns
                )
                all_results.append(result)
                
                # 保存单个场景的对话
                scene_code = scene_prompt.get("scene_code", f"scene_{i}")
                output_file = output_path / f"{scene_code}_dialogue.json"
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                print(f"已保存到: {output_file}")
                
            except Exception as e:
                print(f"生成场景 {scene_prompt.get('scene', '未知')} 的对话时出错: {str(e)}")
                import traceback
                traceback.print_exc()
                continue
        
        # 保存所有场景的汇总结果
        summary_file = output_path / "all_scenes_summary.json"
        summary = {
            "total_scenes": len(scenes),
            "generated_scenes": len(all_results),
            "generated_at": datetime.now().isoformat(),
            "scenes": all_results
        }
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        print(f"\n汇总结果已保存到: {summary_file}")
    
    def _get_default_persona(self) -> Dict[str, Any]:
        """获取默认患者画像"""
        return {
            "基本信息": {
                "性别": "女",
                "年龄": 45
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


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="基线对话生成脚本")
    parser.add_argument(
        "--prompts-file",
        type=str,
        default="data/scene_prompts.json",
        help="场景提示词JSON文件路径"
    )
    parser.add_argument(
        "--persona-file",
        type=str,
        default=None,
        help="患者画像JSON文件路径（可选）"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="output/baseline_dialogues",
        help="输出目录"
    )
    parser.add_argument(
        "--max-turns",
        type=int,
        default=10,
        help="每个场景的最大对话轮数"
    )
    parser.add_argument(
        "--api-key",
        type=str,
        default=None,
        help="API密钥（可选，默认从环境变量或config读取）"
    )
    parser.add_argument(
        "--scene",
        type=str,
        default=None,
        help="只生成指定场景的对话（场景代码，如HYPOGLYCEMIA）"
    )
    
    args = parser.parse_args()
    
    # 初始化生成器
    generator = BaselineDialogueGenerator(api_key=args.api_key)
    
    # 如果指定了单个场景，只生成该场景
    if args.scene:
        scenes = generator.load_scene_prompts(args.prompts_file)
        scene_prompt = None
        for s in scenes:
            if s.get("scene_code") == args.scene:
                scene_prompt = s
                break
        
        if not scene_prompt:
            print(f"未找到场景: {args.scene}")
            return
        
        persona = generator._get_default_persona()
        if args.persona_file and os.path.exists(args.persona_file):
            with open(args.persona_file, 'r', encoding='utf-8') as f:
                persona_data = json.load(f)
                if isinstance(persona_data, list) and len(persona_data) > 0:
                    persona = persona_data[0]
                else:
                    persona = persona_data
        
        result = generator.generate_dialogue_for_scene(
            scene_prompt=scene_prompt,
            persona=persona,
            max_turns=args.max_turns
        )
        
        # 保存结果
        output_path = Path(args.output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        output_file = output_path / f"{args.scene}_dialogue.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n对话已保存到: {output_file}")
    else:
        # 生成所有场景
        generator.generate_all_scenes(
            prompts_file=args.prompts_file,
            persona_file=args.persona_file,
            output_dir=args.output_dir,
            max_turns=args.max_turns
        )


if __name__ == "__main__":
    main()

