"""
简单对话数据生成脚本
从患者数据文件加载数据，为指定患者生成对话并保存
"""

import json
import os
import sys



from main import UserSimulator

def main():
    """主函数"""
    # 患者数据文件路径
    data_file = "/home/yjr/data/patient_structured_50_desensitize.json"
    
    # 选择要测试的患者索引（可以只选一个 [0] 或两个 [0, 1]）
    selected_indices = [0, 1]
    
    # 检查数据文件是否存在
    if not os.path.exists(data_file):
        print(f"错误：数据文件不存在: {data_file}")
        sys.exit(1)
    
    # 加载所有患者数据
    print(f"正在加载患者数据: {data_file}")
    with open(data_file, 'r', encoding='utf-8') as f:
        all_patients = json.load(f)
    
    print(f"成功加载 {len(all_patients)} 位患者数据\n")
    
    # 创建输出目录
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    
    # 处理选中的患者
    for idx in selected_indices:
        if idx >= len(all_patients):
            print(f"警告：索引 {idx} 超出患者数据范围 (0-{len(all_patients)-1})")
            continue
        
        raw_persona = all_patients[idx]
        
        print(f"\n{'='*60}")
        print(f"正在处理第 {idx+1} 个患者 (索引 {idx})")
        print(f"{'='*60}")
        
        # 显示患者基本信息
        basic_info = raw_persona.get('基本信息', {})
        gender = basic_info.get('性别', '未知')
        age = basic_info.get('年龄', '未知')
        persona_type = raw_persona.get('人物底色', '未知')
        
        print(f"基本信息: 性别={gender}, 年龄={age}")
        print(f"人物底色: {persona_type}")
        print()
        
        # 初始化模拟器
        print("初始化用户模拟器...")
        try:
            simulator = UserSimulator()
            print("用户模拟器初始化成功")
        except Exception as e:
            print(f"初始化用户模拟器失败: {e}")
            continue
        
        # 自定义测试主题
        topic = "今天中午在外就餐后血糖升高到15.8mmol/L，有点担心，想了解原因并确认是否需要调整方案。"
        print(f"对话主题: {topic}")
        
        # 运行完整对话模拟
        print(f"开始生成对话 (最多10轮)...")
        try:
            full_data = simulator.simulate_conversation(
                persona=raw_persona,
                dialogue_topic=topic,
                max_turns=10,
                return_full_data=True
            )
            print("对话生成成功")
        except Exception as e:
            print(f"生成对话失败: {e}")
            continue
        
        # 保存结果到JSON文件
        output_path = f"{output_dir}/patient_{idx:02d}_simulation.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(full_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 第 {idx+1} 个患者模拟完成！")
        print(f"结果已保存到: {output_path}")
        
        # 打印对话预览
        if full_data.get("dialogue_history"):
            print("\n对话预览:")
            for i, turn in enumerate(full_data["dialogue_history"][:3]):  # 只显示前3轮
                role = "患者" if turn.get("role") == "user" else "健康助手"
                content = turn.get("content", "")
                thinking = turn.get("thinking", "")
                
                # 限制显示长度
                if len(content) > 80:
                    content = content[:77] + "..."
                
                print(f"  第{i+1}轮 [{role}]: {content}")
                if thinking and i == 0:  # 只显示第一轮的内心独白
                    if len(thinking) > 80:
                        thinking = thinking[:77] + "..."
                    print(f"  [内心独白]: {thinking}")
            
            total_turns = len(full_data["dialogue_history"])
            if total_turns > 3:
                print(f"  ... (还有 {total_turns-3} 轮)")
        
        print()
    
    print(f"{'='*60}")
    print(f"处理完成！共处理了 {len(selected_indices)} 位患者")
    print(f"输出文件保存在: {output_dir}/")
    print("="*60)


if __name__ == "__main__":
    main()