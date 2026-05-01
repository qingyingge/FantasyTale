#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
打包脚本 - 创建独立可执行文件
"""

import os
import sys
import subprocess
import shutil

def log(msg):
    print(f"  [*] {msg}")

def main():
    # 检查venv
    venv_python = os.path.join(os.getcwd(), "venv", "Scripts", "python.exe")
    if not os.path.exists(venv_python):
        print("[X] 请先确保venv存在，运行: venv\\Scripts\\python.exe -m pip install pyinstaller")
        return

    print("=" * 50)
    print("  游戏打包工具")
    print("=" * 50)
    print()

    # 安装pyinstaller
    log("安装pyinstaller...")
    subprocess.run([venv_python, "-m", "pip", "install", "pyinstaller", "-i", "https://pypi.tuna.tsinghua.edu.cn/simple"],
        capture_output=True)

    # 清理旧文件
    log("清理旧构建...")
    for folder in ["build", "dist"]:
        if os.path.exists(folder):
            shutil.rmtree(folder)

    # 创建spec配置
    spec_content = f'''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['game.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('requirements.txt', '.'),
    ],
    hiddenimports=['pygame', 'numpy'],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=['tkinter', 'test'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='FantasyTale',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='FantasyTale',
)
'''

    log("创建配置...")
    with open("build.spec", "w", encoding="utf-8") as f:
        f.write(spec_content)

    # 打包
    log("开始打包（可能需要几分钟）...")
    result = subprocess.run(
        [venv_python, "-m", "PyInstaller", "build.spec", "--clean"],
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        log("打包成功!")
        log(f"输出目录: dist\\FantasyTale")
    else:
        log(f"打包失败: {result.stderr[:500] if result.stderr else '未知错误'}")

if __name__ == "__main__":
    main()