# 幻境传说：迷失大陆

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![Pygame](https://img.shields.io/badge/Pygame-2.x-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## 简介

「幻境传说：迷失大陆」是一款像素风格的开放世界RPG游戏。玩家扮演被选中的勇者，在广阔的大陆上冒险，收集水晶碎片，击败魔王拯救世界。

## 特性

- **开放世界探索** - 5个风格迥异的区域：新手村庄、迷雾草原、灼热沙漠、冰霜雪山、烈焰火山
- **回合制战斗** - 策略性战斗系统，支持物理攻击、技能、道具
- **角色养成** - 等级提升、装备强化、技能解锁
- **丰富任务** - 主线剧情任务 + 支线挑战任务
- **商店系统** - 买卖装备和道具
- **存档系统** - 3个存档位，支持即时存档/读档

## 游戏操作

| 按键 | 功能 |
|------|------|
| WASD / 方向键 | 移动 |
| Space / E | 交互 |
| I | 背包 |
| C | 角色信息 |
| Q | 任务日志 |
| ESC | 菜单 |
| F2 | 存档/读档 |
| F5 | 快速存档 |
| F9 | 快速读档 |

## 安装

### 环境要求

- Python 3.11+
- Windows / macOS / Linux

### 安装依赖

```bash
pip install -r requirements.txt
```

### 运行游戏

```bash
python game.py
```

## 构建版本

如需构建可执行文件：

```bash
pip install pyinstaller
pyinstaller FantasyTale.spec
```

构建完成后，可执行文件位于 `dist/FantasyTale` 目录。

## 存档位置

游戏存档位于 `saves/` 目录下，文件名格式为 `save_1.json`, `save_2.json`, `save_3.json`。

## 游戏版本

- v1.3 - 图鉴系统上线 + Bug修复 (当前版本)
  - 新增图鉴系统(按B键)：敌人/物品/技能图鉴
  - 修复敌人列表遍历时修改列表的bug
  - 修复防御buff无限叠加的bug
  - 修复遇敌冷却计数器逻辑错误
  - 战斗界面显示技能/道具详细信息
  - 物品发现自动记录到图鉴
- v1.2 - 数据外部化
- v1.1 - 初始版本

## 许可证

MIT License

## 作者

qingyingge