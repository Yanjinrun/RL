# batch_generate_500_consolidated.py
"""
批量对话生成器 - 生成带助手 Thinking 的多轮对话（患者无 thinking，助手带 thinking）
每个对话包含 background_story 和带 thinking 的 dialogue_history
"""
import json
import os
import sys
import time
import random
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# 添加路径
sys.path.append('/home/yjr/rl-health-dialogue/user_simulator')

# 导入 API 客户端
from scripts.api_client import QwenAPIClient

# 导入患者生成器（带 thinking）
from scripts.dialogue_generator import DialogueGenerator

# 导入助手生成器（带 thinking）
from scripts.health_assistant_generator_thinking import HealthAssistantGenerator_thinking  # 请确保文件名正确


# API Key
QWEN_API_KEY = os.getenv("QWEN_API_KEY")
if not QWEN_API_KEY:
    print("错误：请设置环境变量 QWEN_API_KEY")
    sys.exit(1)

class ConsolidatedDialogueGenerator:
    """批量对话生成器 - 患者无 Thinking 版本"""
    
    def __init__(self, 
                 output_file: str = "dialogues/all_dialogues_assistant_thinking.jsonl",
                 progress_file: str = "progress_assistant_thinking.json",
                 max_turns_per_convo: int = 20,
                 delay_between_calls: float = 1.0,
                 num_topics_to_generate: int=400):
        self.output_file = Path(output_file)
        self.output_dir = self.output_file.parent
        self.progress_file = self.output_dir / progress_file
        self.max_turns = max_turns_per_convo  # 最大消息条数
        self.delay = delay_between_calls
        
        self.output_dir.mkdir(exist_ok=True, parents=True)
        
        # 主题池（您的50个主题）
        # self.topics = [
        #     "今天中午在外就餐后血糖升高到15.8mmol/L，有点担心，想了解原因并确认是否需要调整方案。",
        #     "最近工作压力大，连续加班，空腹血糖从平时的6.5mmol/L上升到8.7mmol/L，想了解原因。",
        #     "开始尝试低碳水饮食，但经常感到头晕乏力，担心饮食调整是否正确。",
        #     "忘记带胰岛素笔，午餐后没有按时注射胰岛素，两小时后测血糖18.7mmol/L。",
        #     "最近脚部出现麻木感，担心是糖尿病并发症，想咨询是否需要就医检查。",
        #     "昨天运动后出现低血糖症状，测血糖只有3.9mmol/L，想知道如何安全运动。",
        #     "最近体重增加了2公斤，血糖控制也不理想，想知道是否需要调整治疗方案。",
        #     "外出旅游期间饮食不规律，测餐后血糖14.2mmol/L，想了解如何调整。",
        #     "最近睡眠不好，早上空腹血糖偏高，想了解睡眠与血糖的关系。",
        #     "服用新药后出现副作用，想咨询是否需要换药。",
        #     "最近视力有些模糊，担心是糖尿病引起的视网膜病变。",
        #     "聚餐后血糖飙升到18mmol/L，需要紧急处理建议。",
        #     "想开始运动锻炼，但不确定哪种运动适合糖尿病患者。",
        #     "监测血糖的频率应该是多少，不同时间点血糖代表什么意义？",
        #     "胰岛素注射部位出现硬结，应该如何处理？",
        #     "为什么我无法控制血糖水平，想了解可能原因和改善方法。",
        #     "高血糖或低血糖是什么感觉？如果出现该怎么办？",
        #     "血糖水平为什么有多个目标值，想知道不同时间点的标准。",
        #     "我的症状或并发症可能是由什么引起的？",
        #     "症状持续多久需要通知医生？",
        #     "当前治疗方案的费用是多少？有哪些替代治疗方法？",
        #     "作为糖尿病患者，关于COVID-19我需要知道什么？可以正常接种疫苗吗？",
        #     "参加生日派对时，能吃蛋糕和巧克力吗？如何控制？",
        #     "什么是'隐藏糖分'？果汁算含糖饮料吗？",
        #     "偶尔喝可乐可以吗？'轻型或饮食'产品如何影响血糖？",
        #     "能吃薯片或水果吗？如果可以，吃多少合适？",
        #     "下周我想斋戒，可以吗？如何调整饮食？",
        #     "能喝酒吗？如果可以，喝多少合适？什么酒最适合糖尿病患者？",
        #     "可以有'作弊日'吗？偶尔放纵饮食会怎样？",
        #     "糖尿病会影响我的性生活吗？如何应对？",
        #     "需要担心脚部问题吗？糖尿病对脚部有什么后果？",
        #     "糖尿病会影响牙齿吗？需要担心眼睛吗？身体其他部位呢？",
        #     "处方药物的副作用有哪些？",
        #     "如果几天不吃药会怎样？",
        #     "吸烟对糖尿病患者特别危险吗？为什么？",
        #     "我的目标血糖范围是多少？餐前和餐后如何？",
        #     "我的血红蛋白A1C值是多少？目标值是什么？",
        #     "A1C测试频率应该是多少？如何降低A1C？",
        #     "哪种血糖监测仪适合我？",
        #     "手指采血时如何防止感染？",
        #     "应该使用连续血糖监测仪（CGM）吗？如何解读数据？",
        #     "使用CGM时的目标时间范围是多少？",
        #     "我需要服用哪些糖尿病药物？优缺点是什么？",
        #     "药物如何服用？有副作用吗？",
        #     "低血糖时该怎么办？药物会与其他药互动吗？",
        #     "开始服药后需要做哪些实验室检查？",
        #     "药物对血糖的影响是什么？需要服用多久？",
        #     "如果停药会怎样？是口服还是注射？",
        #     "如何注射？需要冷藏吗？旅行时注意什么？",
        #     "手术前需要停药吗？保险覆盖吗？",
        #     "药物替代方案有哪些？",
        #     "胰岛素注射频率和类型是什么？",
        #     "如何知道胰岛素剂量够不够？",
        #     "不计划吃饭时如何调整胰岛素？",
        #     "注射部位如何防止感染？",
        #     "推荐哪种胰岛素输送设备？",
        #     "糖尿病如何影响我的生活方式？",
        #     "糖尿病会影响其他健康问题吗？",
        #     "如何测试糖尿病？我是哪种类型风险？",
        #     "糖尿病可能引起什么健康问题？如何预防？",
        #     "如何管理体重或安全减重？",
        #     "感觉疲惫、压力大，如何保持动力管理糖尿病？",
        #     "如何记住服药和保持血糖目标？",
        #     "担心眼部、高血压、心血管、肾脏并发症，需要注意什么？",
        #     "糖尿病和抑郁的关系？如何处理？"
        # ]
        self.api_client = QwenAPIClient(api_key=QWEN_API_KEY)
        self.topics = self._generate_topics(num_topics_to_generate)
        print(f"已使用qwen生成 {len(self.topics)} 个动态主题。实际得到{len(self.topics)}个。")
        if self.topics:
            print("前3个示例：")
            for i in range(min(3, len(self.topics))):
                print(f"  {i+1}. {self.topics[i][:80]}...")
        else:
            print("警告：主题生成失败，使用默认主题兜底。")
            
        self.progress = self._load_progress()
        self.data_file = "/home/yjr/data/patient_structured_all_desensitize.json"
        self.all_dialogues = self._load_existing_dialogues()

        # 初始化 API 客户端和生成器
        self.api_client = QwenAPIClient(api_key=QWEN_API_KEY)
        self.patient_generator = DialogueGenerator(self.api_client)
        self.assistant_generator = HealthAssistantGenerator_thinking(self.api_client)

    # 以下方法与您原代码完全相同（_load_progress 到 _extract_background_story）
    # 请直接复制您原来的实现
    def _load_progress(self) -> Dict[str, Any]:
        if self.progress_file.exists():
            try:
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"警告：无法加载进度文件，创建新进度: {e}")
        
        return {
            "start_time": datetime.now().isoformat(),
            "total_patients": 400,
            "completed": [],
            "failed": [],
            "current_index": 0,
            "statistics": {
                "total_generated": 0,
                "total_errors": 0,
                "total_api_calls": 0,
                "total_turns_generated": 0
            }
        }

    def _generate_topics(self, num_topics: int) -> List[str]:
        """调用qwen生成大量独特的糖尿病患者咨询主题"""
        prompt = f"""
你是一位专业的糖尿病照护师，请生成 {num_topics} 个**完全不同**的、真实的患者咨询主题。
要求：
**必须遵守**
-每行一个主题，格式：数字+点+空格+主题内容
-不要加任何前言，结语，说明，标题
-必须用阿拉伯数字（1，2，3）
- 每个主题以患者第一人称写，像真实患者会说的话
- 必须包含具体场景、血糖数值、症状、情绪或担忧（例如：血糖值如X.Xmmol/L、头晕、担心并发症、工作压力、聚餐后高血糖等）
- 主题长度控制在20~50字
- 覆盖多样化场景：饮食、运动、用药、副作用、监测频率、并发症恐惧、睡眠、压力、旅游、家庭、退休生活、年轻人职场等
- 避免重复、模板化，确保每个主题独特
- 输出格式严格为纯编号列表，每行一个主题，例如：
1. 最近连续加班，空腹血糖从6.5升到8.7mmol/L，心里很慌，想知道原因。
2. 周末聚餐吃了蛋糕，餐后血糖飙到16.2mmol/L，现在头晕，该怎么办？
...

严格只输出列表
"""
    
        try:
            result = self.api_client.call(
            prompt=prompt,
            model="qwen-plus",
            temperature=0.85,      # 稍高一些增加多样性
            max_tokens=10000
        )

        # ↓↓↓ 必须加这两行，打印原始输出 ↓↓↓
            print("\n=== qwen 原始返回开始（完整内容） ===")
            print(result)
            print("=== qwen 原始返回结束 ===\n")
        
        # 解析输出为列表
            topics = []
            for line in result.split('\n'):
                line = line.strip()
                if not line:
                    continue
                # 去掉常见前缀：1.  1）  -  *  【1】
                cleaned = line.lstrip('0123456789. )]-*【】 \t').strip()
                if cleaned and len(cleaned) >= 20 and ('血糖' in cleaned or 'mmol' in cleaned or '糖尿病' in cleaned):
                    topics.append(cleaned)
            
            topics = list(dict.fromkeys(topics))  # 去重
            print(f"解析后得到 {len(topics)} 个主题")
            
            if len(topics) < num_topics // 2:
                print("警告：主题太少，考虑降低过滤条件或检查API返回")
            
            return topics if topics else ["默认主题：最近血糖有点高，想了解原因。"]
    
        except Exception as e:
            print(f"生成主题失败：{str(e)}")
            return ["默认主题：血糖控制不好，想知道原因。"] * num_topics
    
    def _save_progress(self):
        self.progress["last_update"] = datetime.now().isoformat()
        try:
            with open(self.progress_file, 'w', encoding='utf-8') as f:
                json.dump(self.progress, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"警告：无法保存进度文件: {e}")
    
    def _load_existing_dialogues(self) -> List[Dict]:
        if self.output_file.exists():
            try:
                dialogues = []
                with open(self.output_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            dialogues.append(json.loads(line))
                return dialogues
            except Exception as e:
                print(f"警告：无法加载现有对话文件，创建新文件: {e}")
        return []
    
    def _append_dialogue(self, dialogue: Dict):
        try:
            with open(self.output_file, 'a', encoding='utf-8') as f:
                json.dump(dialogue, f, ensure_ascii=False)
                f.write('\n')
        except Exception as e:
            print(f"错误：无法追加对话到文件: {e}")
            raise
    
    def load_patients(self, num_patients: int = 1200) -> List[Dict]:
        print(f"加载患者数据: {self.data_file}")
        
        if not os.path.exists(self.data_file):
            raise FileNotFoundError(f"数据文件不存在: {self.data_file}")
        
        with open(self.data_file, 'r', encoding='utf-8') as f:
            all_patients = json.load(f)
        
        print(f"总患者数: {len(all_patients)}")
        
        selected_patients = all_patients[:min(num_patients, len(all_patients))]
        
        print(f"选择 {len(selected_patients)} 位患者进行生成")
        
        self.progress["total_patients"] = len(selected_patients)
        
        return selected_patients
    
    # def _select_topic(self, patient_index: int) -> str:
    #     return random.choice(self.topics)
    def _select_topic(self, patient_index: int) -> str:
        if not self.topics:
            return "默认主题：最近血糖控制不太好，想了解原因。"
        return random.choice(self.topics)  # 随机选
    # 或者顺序选：return self.topics[patient_index % len(self.topics)]
    
    def _extract_background_story(self, patient_data: Dict) -> Dict:
        """从患者数据中提取背景故事（适配实际数据结构）"""
        background = {
            "基本信息": {},
            "现病史": {},
            "生活习惯": {},
            "其他信息": {}
        }
        
        base_info = patient_data.get("基础信息", {})
        
        # 基本信息
        u_patient = base_info.get("u_patient", [])
        if u_patient and len(u_patient) > 0:
            pt = u_patient[0]
            background["基本信息"] = {
                "性别": pt.get("性别"),
                "年龄": pt.get("年龄"),
                "VIP状态": pt.get("VIP状态"),
                "VIP类型": pt.get("VIP类型")
            }
        
        # 现病史
        disease = base_info.get("u_patient_base_disease", [])
        if disease and len(disease) > 0:
            dis = disease[0]
            background["现病史"] = {
                "是否有糖尿病史": dis.get("是否有糖尿病史"),
                "糖尿病类型": dis.get("糖尿病类型"),
                "糖尿病发现年份": dis.get("糖尿病发现年份"),
                "是否定期看诊": dis.get("是否定期看诊"),
                "是否规律用药": dis.get("是否规律用药"),
                "是否监测血糖": dis.get("是否监测血糖"),
                "每周测血糖次数": dis.get("每周测血糖次数")
            }
        
        # 生活习惯
        habit = base_info.get("u_patient_base_habit", [])
        if habit and len(habit) > 0:
            hb = habit[0]
            background["生活习惯"] = {
                "运动频率": hb.get("运动频率"),
                "饮食习惯": hb.get("饮食习惯"),
                "是否吸烟": hb.get("是否吸烟"),
                "每日吸烟数量": hb.get("每日吸烟数量"),
                "是否饮酒": hb.get("是否饮酒")
            }
        
        # 其他信息
        base_extra = base_info.get("u_patient_base_info", [])
        if base_extra and len(base_extra) > 0:
            extra = base_extra[0]
            background["其他信息"] = {
                "民族": extra.get("民族"),
                "婚姻情况": extra.get("婚姻情况"),
                "职业类型": extra.get("职业类型")
            }
        
        if "主诉" in patient_data:
            background["其他信息"]["主诉"] = patient_data["主诉"]
        if "就诊目的" in patient_data:
            background["其他信息"]["就诊目的"] = patient_data["就诊目的"]
        
        return background

    def _format_dialogue_for_saving(self, 
                                  dialogue_history: List[Dict], 
                                  background_story: Dict,
                                  metadata: Dict) -> Dict:
        return {
            "dialogue_id": metadata.get("patient_id", f"dialogue_{metadata.get('patient_index', 0)}"),
            "background_story": background_story,
            "dialogue_history": dialogue_history,  # assistant 消息会带 thinking
            "metadata": {
                "generation_time": metadata.get("generation_time"),
                "topic": metadata.get("topic"),
                "turns": metadata.get("turns", 0),
                "patient_gender": metadata.get("gender", "未知"),
                "patient_age": metadata.get("age", "未知"),
                "topic_length": metadata.get("topic_length", 0)
            }
        }

    def should_end_dialogue(self, history: List[Dict[str, Any]], topic: str) -> bool:
        if len(history) < 7:  # 至少4轮（患者-助手-患者-助手）才考虑结束
            return False
        
        last_msg = history[-1]["content"].lower()  # 最后一条消息
        
        # 条件1: 显式收束关键词（扩展你的列表）
        end_keywords = ["再见", "谢谢", "明白了", "清楚了", "好的", "嗯嗯", "保重", "不客气", "可以了", "结束了", "没什么了"]
        if any(kw in last_msg for kw in end_keywords):
            return True
        
        # 条件2: 连续两轮回复很短（≤15字），表示无新内容
        if len(history) >= 2 and all(len(m["content"]) <= 15 for m in history[-2:]):
            return True
        
        # 条件3: 重复回复检测（简单相似度，患者上轮和本轮类似）
        if len(history) >= 3 and history[-1]["content"].strip() == history[-3]["content"].strip():
            return True
        
        # 条件4: 主题覆盖检查（粗糙版：检查历史中是否出现topic关键词≥3次）
        topic_words = set(topic.lower().split())  # 主题拆词
        mention_count = sum(1 for msg in history if any(w in msg["content"].lower() for w in topic_words))
        if mention_count >= 3 and "建议" in last_msg or "解答" in last_msg:  # 假设覆盖3次且有建议词
            return True
        
        return False

    def generate_for_patient(self, patient: Dict, patient_index: int, patient_id: str) -> Dict[str, Any]:
        topic = self._select_topic(patient_index)
        background_story = self._extract_background_story(patient)

        gender = background_story["基本信息"].get("性别", "未知")
        age = background_story["基本信息"].get("年龄", "未知")

        print(f"  [{patient_index+1}] 患者: {gender}, {age}岁")
        print(f"     主题: {topic[:50]}...")

        try:
            background_state = ""
            story = None
            dialogue_history: List[Dict[str, Any]] = []
            max_safety_turns = 20

            turn = 0 
            while turn < max_safety_turns:
                if turn %2 ==0:
                    result = self.patient_generator.generate_response(
                        persona=background_story,
                        dialogue_topic=topic,
                        background=background_state,
                        dialogue_history=dialogue_history,
                        story=story
                    )
                    response_text = result.get("response", "").strip()
                    # thinking_text = result.get("thinking", "").strip()

                    dialogue_history.append({
                        "role": "user",
                        "content": response_text,
                        # "thinking": thinking_text  # 患者无 thinking
                    })

                else:
                    result = self.assistant_generator.generate_reply(
                        persona=background_story,
                        dialogue_topic=topic,
                        background=background_state,
                        dialogue_history=dialogue_history,
                        story=story
                    )
                    response_text = result.get("response", "").strip()
                    thinking_text = result.get("thinking", "").strip()

                    dialogue_history.append({
                        "role": "assistant",
                        "content": response_text,
                        "thinking": thinking_text  # 保存助手的 thinking
                    })

                if response_text:
                    last_user = next((m["content"] for m in reversed(dialogue_history) if m["role"] == "user"), "")
                    background_state += f"\n最新：患者：{last_user[:50]}... 照护师：{response_text[:50]}..."
                    if len(background_state)>400:
                        background_state = background_state[-400:]
                if not response_text:
                    print(f"第{turn+1}轮生成内容为空，提前结束")
                    break

                if self.should_end_dialogue(dialogue_history,topic):
                    if dialogue_history and dialogue_history[-1]["role"] == "assistant":
                    # 强制追加患者收束回复（随机或固定兜底）
                        closure_options = [
                        "嗯，谢谢你，我明白了，先试试看～",
                        "聊了这么多，心里有底了，谢谢！",
                        "好的，我先消化一下，保重～",
                        "感觉好多了，谢谢你的建议！"
                    ]
                        closure_text = random.choice(closure_options)  # 需要 import random
                        dialogue_history.append({
                        "role": "user",
                        "content": closure_text
                    })
                        print(f"     检测到应结束，但以助手结尾，强制追加患者收束: {closure_text}")
                    print(f"     对话自然收束，结束（轮次: {len(dialogue_history)}）")
                    
                    break

                turn += 1
                time.sleep(self.delay)

            if turn >= max_safety_turns:
                if dialogue_history and dialogue_history[-1]["role"] == "assistant":
                    closure_text = "嗯……聊够了，谢谢你，我去试试～"
                    dialogue_history.append({"role": "user", "content": closure_text})
                print(f"     达到安全上限，强制收束")
                


            # for turn in range(self.max_turns):
            #     if turn % 2 == 0:  # 患者轮
            #         result = self.patient_generator.generate_response(
            #             persona=background_story,
            #             dialogue_topic=topic,
            #             background=background_state,
            #             dialogue_history=dialogue_history,
            #             story=story
            #         )
            #         response_text = result.get("response", "").strip()
            #         # thinking_text = result.get("thinking", "").strip()

            #         dialogue_history.append({
            #             "role": "user",
            #             "content": response_text,
            #             # "thinking": thinking_text  # 患者无 thinking
            #         })

            #     else:  # 助手轮
            #         result = self.assistant_generator.generate_reply(
            #             persona=background_story,
            #             dialogue_topic=topic,
            #             background=background_state,
            #             dialogue_history=dialogue_history,
            #             story=story
            #         )
            #         response_text = result.get("response", "").strip()
            #         thinking_text = result.get("thinking", "").strip()

            #         dialogue_history.append({
            #             "role": "assistant",
            #             "content": response_text,
            #             "thinking": thinking_text  # 保存助手的 thinking
            #         })

            #     if not response_text:
            #         print(f"     第 {turn+1} 轮生成内容为空，提前结束")
            #         break

            #     if any(kw in response_text for kw in ["再见", "谢谢", "明白了", "保重"]):
            #         print(f"     检测到对话收束，结束")
            #         break

            #     time.sleep(self.delay)

            metadata = {
                "patient_index": patient_index,
                "patient_id": patient_id,
                "generation_time": datetime.now().isoformat(),
                "topic": topic,
                "topic_length": len(topic),
                "turns": len(dialogue_history),
                "gender": gender,
                "age": age
            }

            formatted_dialogue = self._format_dialogue_for_saving(
                dialogue_history=dialogue_history,
                background_story=background_story,
                metadata=metadata
            )

            self.progress["statistics"]["total_turns_generated"] += len(dialogue_history)

            return {"success": True, "data": formatted_dialogue}

        except Exception as e:
            error_msg = str(e)
            print(f"     错误: {error_msg[:200]}...")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    detail = e.response.json()
                    print(f"     API详细错误: {json.dumps(detail, ensure_ascii=False, indent=2)}")
                except:
                    print(f"     API响应文本: {e.response.text}")
            return {"success": False, "error": error_msg, "patient_index": patient_index}


    def run(self, start_from: int = 0):
        print(f"\n{'='*80}")
        print(f"批量对话生成器 - JSONLines版")
        print(f"输出文件: {self.output_file}")
        print(f"目标患者数: {self.progress['total_patients']}")
        print(f"从索引 {start_from} 开始")
        print('='*80)
        
        patients = self.load_patients(self.progress["total_patients"])
        
        print("初始化用户模拟器...")
        print("模拟器初始化成功")
        
        start_index = max(self.progress.get("current_index", 0), start_from)
        
        existing_count = len(self.all_dialogues) if self.all_dialogues else 0
        if existing_count > start_index:
            print(f"警告：已有 {existing_count} 个对话，将跳过前 {existing_count} 个患者")
            start_index = existing_count
        
        print(f"开始生成，从索引 {start_index} 开始...")
        
        for i in range(start_index, len(patients)):
            patient = patients[i]
            
            print(f"\n--- 处理患者 {i+1}/{len(patients)} ---")
            
            patient_id = f"patient_{i:04d}"
            
            if patient_id in self.progress["completed"]:
                print(f"  已跳过（已完成）")
                self.progress["current_index"] = i + 1
                continue
            
            start_time = time.time()
            result = self.generate_for_patient( patient, i, patient_id)
            
            self.progress["statistics"]["total_api_calls"] += 1
            
            if result["success"]:
                try:
                    self._append_dialogue(result["data"])
                    self.all_dialogues.append(result["data"])
                    
                    self.progress["completed"].append(patient_id)
                    self.progress["current_index"] = i + 1
                    self.progress["statistics"]["total_generated"] += 1
                    
                    elapsed = time.time() - start_time
                    turns = len(result["data"]["dialogue_history"])
                    
                    print(f"  ✅ 成功生成 {turns} 轮对话，耗时 {elapsed:.1f}秒")
                    print(f"     已追加到 {self.output_file.name}，当前对话数: {self.progress['statistics']['total_generated']}")
                    
                except Exception as e:
                    error_info = {"patient_id": patient_id, "patient_index": i, "error": str(e), "time": datetime.now().isoformat()}
                    self.progress["failed"].append(error_info)
                    self.progress["statistics"]["total_errors"] += 1
                    print(f"  ❌ 保存失败: {e}")
            else:
                error_info = {"patient_id": patient_id, "patient_index": i, "error": result["error"], "time": datetime.now().isoformat()}
                self.progress["failed"].append(error_info)
                self.progress["statistics"]["total_errors"] += 1
                print(f"  ❌ 生成失败")
            
            if (i + 1) % 10 == 0 or i == len(patients) - 1:
                self._save_progress()
                print(f"  进度已保存")
            
            completed = len(self.progress["completed"])
            failed = len(self.progress["failed"])
            total = self.progress["total_patients"]
            print(f"  进度: {completed}/{total} 成功, {failed} 失败, {completed/total*100:.1f}%")
            
            if i < len(patients) - 1:
                print(f"  等待 {self.delay} 秒...")
                time.sleep(self.delay)
        
        self._generate_final_report()
        
        print(f"\n{'='*80}")
        print("批量生成完成！")
        print('='*80)
    
    def _generate_final_report(self):
        dialogues_count = 0
        if self.output_file.exists():
            with open(self.output_file, 'r', encoding='utf-8') as f:
                dialogues_count = sum(1 for line in f if line.strip())
        
        report = {
            "generation_summary": {
                "start_time": self.progress.get("start_time"),
                "end_time": datetime.now().isoformat(),
                "total_patients": self.progress["total_patients"],
                "successfully_generated": len(self.progress["completed"]),
                "failed": len(self.progress["failed"]),
                "success_rate": len(self.progress["completed"]) / self.progress["total_patients"] * 100 if self.progress["total_patients"] > 0 else 0,
                "statistics": self.progress["statistics"],
                "output_file": str(self.output_file.absolute()),
                "output_file_size_mb": os.path.getsize(self.output_file) / (1024 * 1024) if self.output_file.exists() else 0,
                "dialogues_count": dialogues_count,
                "average_turns_per_dialogue": self.progress["statistics"]["total_turns_generated"] / dialogues_count if dialogues_count > 0 else 0
            },
            "failed_cases": self.progress["failed"],
            "dialogues_sample": self.all_dialogues[:3] if len(self.all_dialogues) >= 3 else self.all_dialogues,
            "topics_used": list(set([d["metadata"]["topic"] for d in self.all_dialogues]))[:10]
        }
        
        report_file = self.output_dir / "generation_report_consolidated.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n详细报告已保存到: {report_file}")
        
        stats = self.progress["statistics"]
        print(f"\n生成统计:")
        print(f"  总对话数: {dialogues_count}")
        print(f"  失败数: {len(self.progress['failed'])}")
        print(f"  总API调用: {stats['total_api_calls']}")
        print(f"  总生成轮数: {stats['total_turns_generated']}")
        print(f"  平均轮数/对话: {stats['total_turns_generated']/dialogues_count:.1f}" if dialogues_count > 0 else "  平均轮数/对话: N/A")
        print(f"  成功率: {len(self.progress['completed'])/self.progress['total_patients']*100:.1f}%")
        
        if self.output_file.exists():
            file_size = os.path.getsize(self.output_file)
            print(f"\n输出文件: {self.output_file}")
            print(f"文件大小: {file_size/1024/1024:.2f} MB")
        
        if self.all_dialogues:
            print(f"\n对话数据结构示例:")
            first = self.all_dialogues[0]
            print(f"  1. 对话ID: {first.get('dialogue_id', 'N/A')}")
            print(f"     背景故事字段: {list(first.get('background_story', {}).keys())}")
            print(f"     对话轮数: {len(first.get('dialogue_history', []))}")
            print(f"     主题: {first.get('metadata', {}).get('topic', 'N/A')[:30]}...")
    
    def resume(self):
        print("从断点继续生成...")
        self.run(start_from=self.progress.get("current_index", 0))
    
    def retry_failed(self, max_retries: int = 3):
        if not self.progress["failed"]:
            print("没有失败的案例需要重试")
            return
        
        print(f"重试 {len(self.progress['failed'])} 个失败的案例...")
        
        patients = self.load_patients(self.progress["total_patients"])
    
        
        retry_list = self.progress["failed"].copy()
        self.progress["failed"] = []
        
        for retry_item in retry_list:
            patient_index = retry_item["patient_index"]
            patient_id = retry_item["patient_id"]
            
            if patient_index >= len(patients):
                print(f"  跳过无效索引 {patient_index}")
                continue
            
            print(f"\n重试患者 {patient_index+1}: {patient_id}")
            print(f"  上次错误: {retry_item['error'][:100]}...")
            
            patient = patients[patient_index]
            
            for attempt in range(max_retries):
                print(f"  重试尝试 {attempt+1}/{max_retries}...")
                
                try:
                    result = self.generate_for_patient( patient, patient_index, patient_id)
                    
                    if result["success"]:
                        self._append_dialogue(result["data"])
                        self.all_dialogues.append(result["data"])
                        
                        self.progress["completed"].append(patient_id)
                        self.progress["statistics"]["total_generated"] += 1
                        
                        print(f"  ✅ 重试成功，已追加")
                        break
                    else:
                        print(f"  ❌ 重试失败: {result.get('error', '未知错误')}")
                        
                except Exception as e:
                    print(f"  ❌ 重试异常: {e}")
                
                if attempt < max_retries - 1:
                    print(f"  等待 {self.delay*2} 秒后重试...")
                    time.sleep(self.delay * 2)
            else:
                self.progress["failed"].append(retry_item)
                print(f"  ❌ 所有重试都失败，保留在失败列表")
        
        self._save_progress()
        self._generate_final_report()

    # ... 其余方法直接复制您原来的

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="批量生成助手带Thinking的对话数据集")
    parser.add_argument("--output-file", type=str, default="dialogues/all_dialogues_assistant_thinking.jsonl")
    parser.add_argument("--max-turns", type=int, default=10)
    parser.add_argument("--delay", type=float, default=1.0)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--retry-failed", action="store_true")
    parser.add_argument("--num-patients", type=int, default=400)
    parser.add_argument("--num-topics", type=int, default=400,
                        help="使用qwen生成多少个动态主题（默认500，与患者数匹配）")

    args = parser.parse_args()
    
    generator = ConsolidatedDialogueGenerator(
        output_file=args.output_file,
        max_turns_per_convo=args.max_turns,
        delay_between_calls=args.delay,
        num_topics_to_generate=args.num_topics
    )
    
    if args.retry_failed:
        generator.retry_failed()
    elif args.resume:
        generator.resume()
    else:
        generator.run()


if __name__ == "__main__":
    main()