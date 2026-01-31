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
from scripts.health_assistant_generator_thinking import HealthAssistantGenerator_thinking

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
                 max_turns_per_convo: int = 25,
                 delay_between_calls: float = 1.0,
                 num_topics_to_generate: int = 300):
        self.output_file = Path(output_file)
        self.output_dir = self.output_file.parent
        self.progress_file = self.output_dir / progress_file
        self.max_turns = max_turns_per_convo
        self.delay = delay_between_calls
        
        self.output_dir.mkdir(exist_ok=True, parents=True)
        
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

        self.patient_generator = DialogueGenerator(self.api_client)
        self.assistant_generator = HealthAssistantGenerator_thinking(self.api_client)

    def _load_progress(self) -> Dict[str, Any]:
        if self.progress_file.exists():
            try:
                with open(self.progress_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"警告：无法加载进度文件，创建新进度: {e}")
        
        return {
            "start_time": datetime.now().isoformat(),
            "total_patients": 500,
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
        prompt = f"""
你是一位专业的糖尿病照护师，请生成 {num_topics} 个**完全不同**的、真实的患者咨询主题。
要求：
**必须遵守**
-每行一个主题，格式：数字+点+空格+主题内容
-不要加任何前言，结语，说明，标题
-必须用阿拉伯数字（1，2，3）
- 每个主题以患者第一人称写，像真实患者会说的话
- 必须包含具体场景、血糖数值、症状、情绪或担忧
- 主题长度控制在20~50字
- 覆盖多样化场景：饮食、运动、用药、副作用、监测频率、睡眠、压力、旅游、家庭、退休生活、年轻人职场等
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
                temperature=0.8,
                max_tokens=20000
            )
            print("\n=== qwen 原始返回开始（完整内容） ===")
            print(result)
            print("=== qwen 原始返回结束 ===\n")
            
            topics = []
            for line in result.split('\n'):
                line = line.strip()
                if not line:
                    continue
                cleaned = line.lstrip('0123456789. )]-*【】 \t').strip()
                if cleaned and len(cleaned) >= 20 and ('血糖' in cleaned or 'mmol' in cleaned or '糖尿病' in cleaned):
                    topics.append(cleaned)
            
            topics = list(dict.fromkeys(topics))
            print(f"解析后得到 {len(topics)} 个主题")
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
        self.patients = selected_patients
        return selected_patients

    def _select_topic(self, patient_index: int) -> str:
        patient_data = self.patients[patient_index]
        persona = self._extract_background_story(patient_data)
        
        basic = persona.get("基本信息", {})
        disease = persona.get("现病史", {})
        habit = persona.get("生活习惯", {})
        extra = persona.get("其他信息", {})
        
        age = int(basic.get("年龄", 50)) if isinstance(basic.get("年龄"), (int, float)) else 50
        gender = basic.get("性别", "未知")
        occupation = extra.get("职业类型", "未知")
        marital = extra.get("婚姻情况", "未知")
        diabetes_type = disease.get("糖尿病类型", "2型")
        diabetes_year = disease.get("糖尿病发现年份", "未知")
        regular_med = disease.get("是否规律用药", "是")
        monitor_freq = disease.get("每周测血糖次数", "未知")
        smoking = habit.get("是否吸烟", "否")
        exercise = habit.get("运动频率", "未知")
        diet = habit.get("饮食习惯", "均衡")
        
        emotion_options = [
            "有点困惑", "不太明白", "想了解一下", "最近有点奇怪", 
            "有点担心", "心里不踏实", "不太放心", "有点拿不准",
            "挺担心的", "心里没底", "有点焦虑"
        ]
        emotion = random.choice(emotion_options)
        
        scene_options = [
            "最近工作忙", "周末聚餐", "旅游饮食不规律", "睡眠不太好",
            "体重涨了点", "想开始运动", "饮食调整后", "用药有点不适应",
            "监测频率不知道", "餐后血糖高", "空腹偏高", "陪孩子熬夜",
            "退休后散步", "加班多", "聚会喝酒", "节假日吃多",
            "孩子高考陪读", "夜班工作", "怀孕期间", "出差在外"
        ]
        scene = random.choice(scene_options)
        
        if "低血糖" in scene or "凌晨" in scene:
            bg_value = f"{random.uniform(3.2, 4.5):.1f}mmol/L"
        elif "餐后" in scene or "聚餐" in scene:
            bg_value = f"{random.uniform(9.5, 13.5):.1f}mmol/L"
        else:
            bg_value = f"{random.uniform(6.5, 8.8):.1f}mmol/L"
        
        concern_options = [
            "想知道原因", "是不是饮食问题", "该怎么调整", "担心长期这样",
            "膝盖有点疼", "头有点晕", "口干舌燥", "夜里起夜多",
            "体重涨了", "视力有点模糊", "手脚有点麻", "牙龈出血",
            "用药后胃不舒服", "血糖波动大", "想开始运动"
        ]
        concern = random.choice(concern_options)
        
        if age > 65:
            style = "像老人说话，带点哎哟、咋办呢"
        elif "在职" in occupation or "加班" in occupation:
            style = "像上班族，自然口语化，带点无奈"
        elif gender == "女" and age < 40:
            style = "像年轻妈妈，温柔又有点担心"
        else:
            style = "自然口语化，带点自责或困惑"
        
        prompt = f"""
根据以下患者真实背景，生成一条最符合他当前情况的、第一人称咨询问题（query）。
患者画像：
- {age}岁，{gender}，{occupation}，{marital}，{diabetes_type}糖尿病{diabetes_year}年，{regular_med}用药，{monitor_freq}测血糖，{smoking}烟，{exercise}运动，饮食{diet}

要求：
- 第一人称，像真实糖尿病患者日常咨询的语气（自然、口语化）
- 语气日常、真实，避免使用“救命！”“吓死我了”“要截肢”等过度惊恐或急诊式表达
- 绝大多数情况下用平静/困惑/轻度担心表达
- 必须包含具体场景、血糖数值（{bg_value}）、症状或情绪
- 长度30~60字
- 场景：{scene}，情绪：{emotion}，担忧：{concern}
- 风格：{style}
- 只输出一条 query，不要任何多余文字
"""

        try:
            result = self.api_client.call(
                prompt=prompt,
                model="qwen-plus",
                temperature=0.8,
                max_tokens=150
            )
            query = result.strip()
            if 25 < len(query) < 80 and any(kw in query.lower() for kw in ["血糖", "mmol", "怎么办", "怎么", "担心", "原因", "调整"]):
                forbidden = ["救命", "吓死", "要命", "发毛", "截肢", "昏迷"]
                if not any(word in query for word in forbidden):
                    return query
            return f"最近{scene}，血糖{bg_value}，{emotion}，想知道怎么调整。"
        except Exception as e:
            print(f"生成个性化 query 失败：{e}")
            return f"最近血糖{bg_value}，有点{emotion}，想了解一下原因。"
    
    def _extract_background_story(self, patient_data: Dict) -> Dict:
        background = {
            "基本信息": {},
            "现病史": {},
            "生活习惯": {},
            "其他信息": {}
        }
        
        base_info = patient_data.get("基础信息", {})
        
        u_patient = base_info.get("u_patient", [])
        if u_patient and len(u_patient) > 0:
            pt = u_patient[0]
            background["基本信息"] = {
                "性别": pt.get("性别"),
                "年龄": pt.get("年龄"),
                "VIP状态": pt.get("VIP状态"),
                "VIP类型": pt.get("VIP类型")
            }
        
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

    def run(self, start_from: int = 0):
        """
        运行批量对话生成
        """
        print(f"\n{'='*80}")
        print(f"批量对话生成器 - JSONLines版")
        print(f"输出文件: {self.output_file}")
        print(f"目标患者数: {self.progress['total_patients']}")
        print(f"从索引 {start_from} 开始")
        print('='*80)
        
        # 加载患者数据
        patients = self.load_patients(self.progress["total_patients"])
        
        print("初始化生成器...")
        print("生成器初始化成功")
        
        start_index = max(self.progress.get("current_index", 0), start_from)
        
        # 检查现有对话，避免重复生成
        existing_count = len(self.all_dialogues) if self.all_dialogues else 0
        if existing_count > start_index:
            print(f"警告：已有 {existing_count} 个对话，将跳过前 {existing_count} 个患者")
            start_index = existing_count
        
        print(f"开始生成，从索引 {start_index} 开始...")
        
        # 遍历患者进行生成
        for i in range(start_index, len(patients)):
            patient = patients[i]
            
            print(f"\n--- 处理患者 {i+1}/{len(patients)} ---")
            
            patient_id = f"patient_{i:04d}"
            
            # 跳过已完成的患者
            if patient_id in self.progress["completed"]:
                print(f"  已跳过（已完成）")
                self.progress["current_index"] = i + 1
                continue
            
            start_time = time.time()
            
            # 生成对话
            result = self.generate_for_patient(patient, i, patient_id)
            
            self.progress["statistics"]["total_api_calls"] += 1
            
            if result["success"]:
                try:
                    # 保存对话
                    self._append_dialogue(result["data"])
                    self.all_dialogues.append(result["data"])
                    
                    # 更新进度
                    self.progress["completed"].append(patient_id)
                    self.progress["current_index"] = i + 1
                    self.progress["statistics"]["total_generated"] += 1
                    
                    elapsed = time.time() - start_time
                    turns = len(result["data"]["dialogue_history"])
                    
                    print(f"  ✅ 成功生成 {turns} 轮对话，耗时 {elapsed:.1f}秒")
                    print(f"     已追加到 {self.output_file.name}，当前对话数: {self.progress['statistics']['total_generated']}")
                    
                except Exception as e:
                    error_info = {
                        "patient_id": patient_id,
                        "patient_index": i,
                        "error": str(e),
                        "time": datetime.now().isoformat()
                    }
                    self.progress["failed"].append(error_info)
                    self.progress["statistics"]["total_errors"] += 1
                    print(f"  ❌ 保存失败: {e}")
            else:
                error_info = {
                    "patient_id": patient_id,
                    "patient_index": i,
                    "error": result["error"],
                    "time": datetime.now().isoformat()
                }
                self.progress["failed"].append(error_info)
                self.progress["statistics"]["total_errors"] += 1
                print(f"  ❌ 生成失败")
            
            # 定期保存进度
            if (i + 1) % 10 == 0 or i == len(patients) - 1:
                self._save_progress()
                print(f"  进度已保存")
            
            # 显示当前进度
            completed = len(self.progress["completed"])
            failed = len(self.progress["failed"])
            total = self.progress["total_patients"]
            print(f"  进度: {completed}/{total} 成功, {failed} 失败, {completed/total*100:.1f}%")
            
            # 延迟避免API限制
            if i < len(patients) - 1:
                print(f"  等待 {self.delay} 秒...")
                time.sleep(self.delay)
        
        # 生成最终报告
        self._generate_final_report()
        
        print(f"\n{'='*80}")
        print("批量生成完成！")
        print('='*80)

    def resume(self):
        """
        从断点继续生成
        """
        print("从断点继续生成...")
        self.run(start_from=self.progress.get("current_index", 0))

    def retry_failed(self, max_retries: int = 3):
        """
        重试失败的案例
        """
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
                    result = self.generate_for_patient(patient, patient_index, patient_id)
                    
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

    def _check_if_patient_wants_to_end(self, patient_response: str, current_turn: int) -> bool:
        """
        检查患者是否表达结束意图
        """
        if not patient_response:
            return False
        
        # 强烈结束信号
        strong_end_signals = [
            "行，先这样", "好的，谢谢", "谢谢，再见", "明白了，谢谢",
            "先不聊了", "结束", "今天就到这", "拜拜", "回头聊"
        ]
        
        # 温和结束信号
        mild_end_signals = [
            "先这样", "明白了", "先去", "去落实", "先睡", "晚安",
            "就这样", "先稳", "先观察", "先试试", "先这样吧",
            "心里有数", "踏实了", "放心了", "安心了", "可以了"
        ]
        
        content_lower = patient_response.lower()
        
        # 检查强烈结束信号
        for signal in strong_end_signals:
            if signal in content_lower:
                return True
        
        # 检查温和结束信号，且轮次足够
        if current_turn >= 8:
            for signal in mild_end_signals:
                if signal in content_lower:
                    return True
        
        # 检查是否表达了满意的状态
        satisfaction_signals = [
            "心里踏实", "放心多了", "安心了", "有底了", "清楚怎么做了",
            "没问题了", "知道了", "懂了", "明白了"
        ]
        
        if current_turn >= 10:
            for signal in satisfaction_signals:
                if signal in content_lower:
                    return True
        
        return False

    def _check_if_assistant_wants_to_end(self, assistant_response: str, current_turn: int) -> bool:
        """
        检查助手是否表达结束意图
        """
        if not assistant_response:
            return False
        
        end_signals = [
            "先观察", "有变化再聊", "先这样", "慢慢来", "先稳着",
            "先休息", "先这样吧", "下次见", "晚安", "再见",
            "咱们先这样", "先按这个来", "先试试看", "有情况再说",
            "先聊到这", "今天先这样", "你先试试", "回头联系"
        ]
        
        content_lower = assistant_response.lower()
        
        for signal in end_signals:
            if signal in content_lower:
                return True
        
        # 检查是否是很短的结束性回复
        if len(assistant_response) < 20 and current_turn >= 6:
            if any(word in content_lower for word in ["好", "行", "嗯", "可以"]):
                return True
        
        return False

    def _generate_final_response(self, dialogue_history: List[Dict], topic: str) -> str:
        """
        生成最终的结束性回复
        """
        # 从历史中提取一些信息
        patient_messages = [msg["content"] for msg in dialogue_history if msg["role"] == "user"]
        recent_patient = patient_messages[-1] if patient_messages else ""
        
        # 根据患者最后的消息选择合适的结束语
        if any(word in recent_patient.lower() for word in ["谢谢", "感谢"]):
            return "不客气，有问题随时联系。"
        elif any(word in recent_patient.lower() for word in ["晚安", "睡觉"]):
            return "晚安，好好休息。"
        elif any(word in recent_patient.lower() for word in ["明白", "知道", "懂了"]):
            return "好的，先这样，有问题随时说。"
        elif "血糖" in recent_patient:
            return "血糖的事先按这个观察几天，有变化再联系。"
        else:
            # 默认结束语
            return "好的，先这样，有问题随时联系。"
    def _check_conversation_should_end(self, 
                                  dialogue_history: List[Dict], 
                                  current_turn: int,
                                  max_turns: int = 25) -> bool:
        """
        检查对话是否应该结束
        返回: True 表示应该结束，False 表示继续
        """
        if not dialogue_history:
            return False
        
        # 1. 达到硬性上限
        if current_turn >= max_turns:
            return True
        
        # 2. 患者明确表达结束意图
        if len(dialogue_history) >= 1:
            last_message = dialogue_history[-1]
            if last_message["role"] == "user":
                patient_end_keywords = [
                    "先这样", "明白了", "先去", "去落实", "先睡", "晚安", 
                    "就这样", "先稳", "先观察", "先试试", "先这样吧", 
                    "行，先这样", "好的，谢谢", "谢谢，再见", "明白了，谢谢",
                    "先不聊了", "我先去忙", "结束", "差不多了", "可以了"
                ]
                content = last_message["content"].lower()
                if any(kw in content for kw in patient_end_keywords):
                    # 至少进行4轮才接受结束
                    if current_turn >= 8:
                        return True
        
        # 3. 连续两轮重复内容
        if len(dialogue_history) >= 2:
            last_two = dialogue_history[-2:]
            if (last_two[0]["role"] == "user" and last_two[1]["role"] == "user"):
                content1 = last_two[0]["content"].strip()
                content2 = last_two[1]["content"].strip()
                if content1 == content2 and len(content1) > 5:
                    return True
        
        # 4. 话题已充分讨论（简单判断）
        if current_turn >= 12:
            # 检查最近患者消息是否主要是确认
            recent_patient_msgs = [
                msg["content"] for msg in dialogue_history[-4:] 
                if msg["role"] == "user"
            ]
            if len(recent_patient_msgs) >= 2:
                confirm_keywords = ["好", "明白", "知道", "谢谢", "了解", "懂了", "行", "可以"]
                confirm_count = sum(1 for msg in recent_patient_msgs 
                                if any(kw in msg.lower() for kw in confirm_keywords))
                if confirm_count >= len(recent_patient_msgs) // 2:
                    return True
        
        return False
    
    def _fix_turn_sequence(self, dialogue_history):
        """修复轮次序列问题"""
        if len(dialogue_history) <= 1:
            return dialogue_history
        
        fixed = []
        for i, msg in enumerate(dialogue_history):
            if i == 0:
                fixed.append(msg)
                continue
            
            prev = fixed[-1]
            curr = msg
            
            # 删除连续相同角色的消息
            if prev["role"] == curr["role"]:
                print(f"修复: 删除第{i+1}条重复角色消息")
                continue
            
            # 修改重复内容
            if prev["content"] == curr["content"]:
                print(f"修复: 修改第{i+1}条重复内容")
                modified = curr.copy()
                if curr["role"] == "user":
                    modified["content"] = "嗯，我再补充一点..."
                else:
                    modified["content"] = "另外，我还想说的是..."
                fixed.append(modified)
            else:
                fixed.append(curr)
        
        return fixed

    def _validate_dialogue_quality(self, dialogue_history: List[Dict]) -> Dict[str, Any]:
        """
        检查生成的对话质量
        """
        if not dialogue_history:
            return {"valid": False, "reason": "对话历史为空"}
        
        # 检查轮次数量
        total_turns = len(dialogue_history)
        if total_turns < 4:
            return {"valid": False, "reason": f"对话轮次过少: {total_turns}"}
        
        # 检查内容质量
        empty_responses = 0
        error_responses = 0
        
        for msg in dialogue_history:
            content = msg.get("content", "").strip()
            if not content:
                empty_responses += 1
            elif "生成失败" in content or "跳过" in content:
                error_responses += 1
        
        quality_score = 1.0 - (empty_responses + error_responses) / total_turns
        
        return {
            "valid": quality_score >= 0.7,
            "quality_score": quality_score,
            "total_turns": total_turns,
            "empty_responses": empty_responses,
            "error_responses": error_responses,
            "reason": "通过" if quality_score >= 0.7 else f"质量分过低: {quality_score:.2f}"
        }


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
            max_safety_turns = 25

            turn = 0 
            patient_has_ended = False
            
            while turn < max_safety_turns and not patient_has_ended:
                response_text = ""
                thinking_text = ""
                
                # 1. 先检查对话是否应该结束
                if self._check_conversation_should_end(dialogue_history, turn, max_safety_turns):
                    print(f"     检查到对话应该结束（轮次: {turn+1}）")
                    break

                # 2. 确定当前轮次是谁发言（确保角色交替）
                if turn == 0 or (dialogue_history and dialogue_history[-1]["role"] == "assistant"):
                    # 患者轮：要么是第一轮，要么上一轮是助手
                    current_role = "user"
                else:
                    # 助手轮：上一轮是患者
                    current_role = "assistant"
                
                print(f"第 {turn+1} 轮：{('患者' if current_role == 'user' else '助手')}发言")

                if current_role == "user":  # 患者轮
                    # 生成患者回复
                    result = self.patient_generator.generate_response(
                        persona=background_story,
                        dialogue_topic=topic,
                        background=background_state,
                        dialogue_history=dialogue_history,
                        story=story
                    )
                    
                    if result is None or not isinstance(result, dict):
                        print(f"第 {turn+1} 轮患者生成失败，返回 None 或无效格式")
                        response_text = "（思考中...）"
                    else:
                        response_text = result.get("response", "").strip()
                    
                    # 避免空回复
                    if not response_text:
                        response_text = "我在想这个问题..."
                    
                    # 添加到对话历史
                    dialogue_history.append({
                        "role": "user",
                        "content": response_text
                    })
                    
                    print(f"患者回复: {response_text[:60]}...")
                    
                    # 检查患者是否表达结束意图
                    if self._check_if_patient_wants_to_end(response_text, turn):
                        print(f"     检测到患者结束意图（轮次: {turn+1}）")
                        patient_has_ended = True
                        
                        # 如果患者结束，给助手最后一次回复的机会
                        # 不要break，让循环继续到助手轮
                        continue
                    
                    # 软性上限检查：15轮后患者多次确认
                    if turn >= 15 and len(dialogue_history) >= 3:
                        recent_messages = dialogue_history[-3:]
                        confirm_count = 0
                        for msg in recent_messages:
                            if msg["role"] == "user":
                                content = msg["content"].lower()
                                if any(word in content for word in ["好", "明白", "知道", "谢谢", "了解", "懂了"]):
                                    confirm_count += 1
                        
                        if confirm_count >= 2:
                            print(f"     达到软性上限且患者多次确认，对话结束（轮次: {turn+1}）")
                            # 需要助手做结束性回复
                            patient_has_ended = True
                            continue

                else:  # 助手轮
                    # 如果患者已表达结束意图，生成结束性回复
                    if patient_has_ended:
                        print(f"     患者已表达结束意图，助手进行结束性回复")
                        response_text = self._generate_final_response(dialogue_history, topic)
                        thinking_text = "患者已表达结束意图，生成礼貌结束语"
                    else:
                        # 正常生成助手回复
                        result = self.assistant_generator.generate_reply(
                            persona=background_story,
                            dialogue_topic=topic,
                            background=background_state,
                            dialogue_history=dialogue_history,
                            story=story
                        )
                        
                        if result is None or not isinstance(result, dict):
                            print(f"第 {turn+1} 轮助手生成失败，返回 None 或无效格式")
                            response_text = "我理解您的担忧。"
                            thinking_text = ""
                        else:
                            response_text = result.get("response", "").strip()
                            thinking_text = result.get("thinking", "").strip()
                    
                    # 避免空回复
                    if not response_text:
                        response_text = "我理解您的担忧，我们可以继续讨论。"
                    
                    # 添加到对话历史
                    dialogue_history.append({
                        "role": "assistant",
                        "content": response_text,
                        "thinking": thinking_text
                    })
                    
                    print(f"助手回复: {response_text[:60]}...")
                    
                    # 如果助手做了结束性回复，结束对话
                    if patient_has_ended:
                        print(f"     助手完成结束性回复，对话结束")
                        break
                    
                    # 检查助手是否引导结束
                    if self._check_if_assistant_wants_to_end(response_text, turn) and turn >= 6:
                        print(f"     助手引导收束，对话结束（轮次: {turn+1}）")
                        break

                # 3. 更新背景状态
                if response_text:
                    last_user = next((m["content"] for m in reversed(dialogue_history) 
                                    if m["role"] == "user"), "")
                    background_state += f"\n最新：患者：{last_user[:50]}... 照护师：{response_text[:50]}..."
                    if len(background_state) > 400:
                        background_state = background_state[-400:]

                turn += 1
                time.sleep(self.delay)

            # 4. 达到安全上限时强制结束
            if turn >= max_safety_turns:
                print(f"     达到安全上限 {max_safety_turns} 轮，强制结束")
                # 如果最后一条是患者消息，添加助手结束语
                if dialogue_history and dialogue_history[-1]["role"] == "user":
                    final_response = self._generate_final_response(dialogue_history, topic)
                    dialogue_history.append({
                        "role": "assistant",
                        "content": final_response,
                        "thinking": "达到最大轮次，生成结束语"
                    })
            
            # 5. 验证和修复对话序列
            dialogue_history = self._fix_turn_sequence(dialogue_history)
            
            # 6. 质量检查
            quality_check = self._validate_dialogue_quality(dialogue_history)
            if not quality_check["valid"]:
                print(f"     对话质量检查未通过: {quality_check['reason']}")
            
            metadata = {
                "patient_index": patient_index,
                "patient_id": patient_id,
                "generation_time": datetime.now().isoformat(),
                "topic": topic,
                "turns": len(dialogue_history),
                "gender": gender,
                "age": age,
                "ended_naturally": patient_has_ended or turn < max_safety_turns,
                "quality_score": quality_check["quality_score"],
                "quality_reason": quality_check["reason"]
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
            return {"success": False, "error": error_msg, "patient_index": patient_index}
        
        

    def _format_dialogue_for_saving(self, 
                                    dialogue_history: List[Dict], 
                                    background_story: Dict,
                                    metadata: Dict) -> Dict:
        return {
            "dialogue_id": metadata.get("patient_id", f"dialogue_{metadata.get('patient_index', 0)}"),
            "background_story": background_story,
            "dialogue_history": dialogue_history,
            "metadata": {
                "generation_time": metadata.get("generation_time"),
                "topic": metadata.get("topic"),
                "turns": metadata.get("turns", 0),
                "patient_gender": metadata.get("gender", "未知"),
                "patient_age": metadata.get("age", "未知"),
                "topic_length": metadata.get("topic_length", 0)
            }
        }

    
    
    
    
    

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="批量生成助手带Thinking的对话数据集")
    parser.add_argument("--output-file", type=str, default="dialogues/all_dialogues_assistant_thinking.jsonl")
    parser.add_argument("--max-turns", type=int, default=25)
    parser.add_argument("--delay", type=float, default=1.0)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--retry-failed", action="store_true")
    parser.add_argument("--num-patients", type=int, default=3)
    parser.add_argument("--num-topics", type=int, default=10)
    parser.add_argument("--start-from", type=int, default=0)

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
        generator.run(start_from=args.start_from)


if __name__ == "__main__":
    main()