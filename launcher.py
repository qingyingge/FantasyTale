#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""游戏启动器"""

import os
import sys

os.chdir(os.path.dirname(os.path.abspath(__file__)))

def main():
    print("=" * 50)
    print("  幻境传说：迷失大陆 - 游戏启动器")
    print("=" * 50)
    print()

    # 找Python
    venv_python = os.path.join(os.getcwd(), "venv", "Scripts", "python.exe")
    if os.path.exists(venv_python):
        python = venv_python
    else:
        python = sys.executable

    print(f"  使用Python: {python}")
    print()

    # 检查依赖
    req_file = os.path.join(os.getcwd(), "requirements.txt")
    if os.path.exists(req_file):
        print("  检查依赖...")
        os.system(f'"{python}" -m pip list')
        print()

    # 启动游戏
    game_file = os.path.join(os.getcwd(), "game.py")
    print("  启动游戏...")
    print("-" * 40)
    print()
    os.system(f'""{python}" "{game_file}"')

    print()
    print("  游戏已退出")

if __name__ == "__main__":
    main()