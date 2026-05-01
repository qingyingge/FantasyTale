#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""游戏启动器"""

import sys

def main():
    print("=" * 50)
    print("  幻境传说：迷失大陆 - 游戏启动器")
    print("=" * 50)
    print()
    print(f"  Python: {sys.version.split()[0]}")
    print()

    # 启动游戏
    print("  启动游戏...")
    print("-" * 40)
    print()
    import subprocess
    subprocess.run(["python", "game.py"])

    print()
    print("  游戏已退出")

if __name__ == "__main__":
    main()