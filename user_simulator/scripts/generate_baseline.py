#!/usr/bin/env python3
"""
基线对话生成入口脚本
使用场景提示词驱动"病人模拟器"与"通用AI"进行对话生成
"""
import sys
import os
from pathlib import Path

# 获取项目根目录（user_simulator目录）
project_root = Path(__file__).parent.parent
# 添加项目根目录到路径，这样可以从scripts目录导入其他模块
sys.path.insert(0, str(project_root))

# 切换到项目根目录，确保相对路径正确
os.chdir(project_root)

# 现在可以导入scripts模块
from scripts.generate_baseline_dialogues import main

if __name__ == "__main__":
    main()

