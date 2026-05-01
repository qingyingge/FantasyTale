#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
游戏配置和常量
"""

import pygame
from enum import Enum

# ============================================================================
# 游戏配置
# ============================================================================
class Config:
    SCREEN_WIDTH = 1024
    SCREEN_HEIGHT = 768
    FPS = 60
    TILE_SIZE = 48
    PIXEL_SCALE = 3  # 像素艺术缩放倍数

    # 颜色定义 (像素风格调色板)
    COLORS = {
        'black': (0, 0, 0),
        'white': (255, 255, 255),
        'dark_gray': (40, 40, 60),
        'gray': (100, 100, 120),
        'light_gray': (180, 180, 200),
        'red': (200, 50, 50),
        'dark_red': (120, 30, 30),
        'green': (50, 180, 80),
        'dark_green': (30, 100, 50),
        'blue': (60, 100, 200),
        'dark_blue': (30, 50, 120),
        'gold': (220, 180, 60),
        'brown': (120, 80, 50),
        'dark_brown': (70, 45, 25),
        'purple': (140, 60, 180),
        'cyan': (60, 200, 200),
        'orange': (220, 140, 40),
        'yellow': (240, 220, 60),
        'pink': (220, 120, 160),
        'grass': (80, 160, 60),
        'water': (50, 100, 200),
        'sand': (220, 200, 140),
        'stone': (140, 140, 150),
        'snow': (230, 240, 255),
        'forest': (40, 100, 40),
        'lava': (200, 60, 30),
    }


# ============================================================================
# 像素艺术工具
# ============================================================================
class PixelArt:
    """像素艺术绘制辅助类"""

    @staticmethod
    def draw_pixel_art(surface, x, y, pixel_data, scale=3, offset_x=0, offset_y=0):
        """根据像素数据绘制像素艺术"""
        for row_idx, row in enumerate(pixel_data):
            for col_idx, color in enumerate(row):
                if color:
                    rect = pygame.Rect(
                        x + col_idx * scale + offset_x,
                        y + row_idx * scale + offset_y,
                        scale, scale
                    )
                    pygame.draw.rect(surface, color, rect)

    @staticmethod
    def create_sprite(pixel_data, scale=3):
        """从像素数据创建Sprite表面"""
        if not pixel_data:
            return None
        height = len(pixel_data)
        width = len(pixel_data[0]) if pixel_data else 0
        surface = pygame.Surface((width * scale, height * scale), pygame.SRCALPHA)
        for row_idx, row in enumerate(pixel_data):
            for col_idx, color in enumerate(row):
                if color:
                    rect = pygame.Rect(col_idx * scale, row_idx * scale, scale, scale)
                    pygame.draw.rect(surface, color, rect)
        return surface


# ============================================================================
# 精灵数据定义 (16x16 像素艺术)
# ============================================================================
C = Config.COLORS

SPRITE_PLAYER = [
    [None, None, None, C['brown'], C['brown'], C['brown'], C['brown'], None, None, None],
    [None, None, C['brown'], C['brown'], C['brown'], C['brown'], C['brown'], C['brown'], None, None],
    [None, None, C['pink'], C['pink'], C['white'], C['pink'], C['pink'], C['white'], None, None],
    [None, None, C['black'], C['pink'], C['black'], C['black'], C['pink'], C['black'], None, None],
    [None, None, C['pink'], C['pink'], C['pink'], C['pink'], C['pink'], C['pink'], None, None],
    [None, C['blue'], C['blue'], C['blue'], C['blue'], C['blue'], C['blue'], C['blue'], C['blue'], None],
    [C['blue'], C['blue'], C['gold'], C['blue'], C['blue'], C['blue'], C['gold'], C['blue'], C['blue'], C['blue']],
    [C['blue'], C['blue'], C['blue'], C['blue'], C['blue'], C['blue'], C['blue'], C['blue'], C['blue'], C['blue']],
    [None, C['blue'], C['blue'], C['blue'], C['blue'], C['blue'], C['blue'], C['blue'], C['blue'], None],
    [None, None, C['brown'], C['brown'], C['brown'], C['brown'], C['brown'], C['brown'], None, None],
    [None, None, C['dark_brown'], C['dark_brown'], None, None, C['dark_brown'], C['dark_brown'], None, None],
]

SPRITE_NPC = [
    [None, None, None, C['gray'], C['gray'], C['gray'], C['gray'], None, None, None],
    [None, None, C['gray'], C['gray'], C['gray'], C['gray'], C['gray'], C['gray'], None, None],
    [None, None, C['pink'], C['pink'], C['white'], C['pink'], C['pink'], C['white'], None, None],
    [None, None, C['black'], C['pink'], C['black'], C['black'], C['pink'], C['black'], None, None],
    [None, None, C['pink'], C['pink'], C['pink'], C['pink'], C['pink'], C['pink'], None, None],
    [None, C['green'], C['green'], C['green'], C['green'], C['green'], C['green'], C['green'], C['green'], None],
    [C['green'], C['green'], C['gold'], C['green'], C['green'], C['green'], C['gold'], C['green'], C['green'], C['green']],
    [C['green'], C['green'], C['green'], C['green'], C['green'], C['green'], C['green'], C['green'], C['green'], C['green']],
    [None, C['green'], C['green'], C['green'], C['green'], C['green'], C['green'], C['green'], C['green'], None],
    [None, None, C['brown'], C['brown'], C['brown'], C['brown'], C['brown'], C['brown'], None, None],
    [None, None, C['dark_brown'], C['dark_brown'], None, None, C['dark_brown'], C['dark_brown'], None, None],
]

SPRITE_ENEMY = [
    [None, None, C['dark_red'], None, None, None, None, C['dark_red'], None, None],
    [None, C['dark_red'], C['red'], C['red'], None, None, C['red'], C['red'], C['dark_red'], None],
    [C['dark_red'], C['red'], C['yellow'], C['red'], C['red'], C['red'], C['red'], C['yellow'], C['red'], C['dark_red']],
    [C['dark_red'], C['red'], C['black'], C['red'], C['red'], C['red'], C['red'], C['black'], C['red'], C['dark_red']],
    [None, C['red'], C['red'], C['yellow'], C['yellow'], C['yellow'], C['yellow'], C['red'], C['red'], None],
    [None, None, C['red'], C['red'], C['red'], C['red'], C['red'], C['red'], None, None],
    [None, C['purple'], C['red'], C['red'], C['red'], C['red'], C['red'], C['red'], C['purple'], None],
    [C['purple'], C['purple'], C['red'], C['red'], C['red'], C['red'], C['red'], C['red'], C['purple'], C['purple']],
    [C['purple'], C['purple'], C['dark_red'], C['red'], C['red'], C['red'], C['red'], C['dark_red'], C['purple'], C['purple']],
    [None, None, C['dark_red'], C['dark_red'], None, None, C['dark_red'], C['dark_red'], None, None],
]

SPRITE_TREE = [
    [None, None, None, None, C['brown'], C['brown'], None, None, None, None],
    [None, None, None, C['brown'], C['brown'], C['brown'], C['brown'], None, None, None],
    [None, None, C['forest'], C['forest'], C['forest'], C['forest'], C['forest'], C['forest'], None, None],
    [None, C['forest'], C['grass'], C['forest'], C['forest'], C['forest'], C['forest'], C['grass'], C['forest'], None],
    [C['forest'], C['forest'], C['forest'], C['forest'], C['forest'], C['forest'], C['forest'], C['forest'], C['forest'], C['forest']],
    [C['forest'], C['forest'], C['forest'], C['forest'], C['forest'], C['forest'], C['forest'], C['forest'], C['forest'], C['forest']],
    [None, C['forest'], C['forest'], C['forest'], C['forest'], C['forest'], C['forest'], C['forest'], C['forest'], None],
    [None, None, C['forest'], C['forest'], C['forest'], C['forest'], C['forest'], C['forest'], None, None],
    [None, None, None, None, C['brown'], C['brown'], None, None, None, None],
    [None, None, None, None, C['brown'], C['brown'], None, None, None, None],
]

SPRITE_HOUSE = [
    [None, None, None, None, C['red'], C['red'], C['red'], None, None, None, None, None],
    [None, None, None, C['red'], C['red'], C['red'], C['red'], C['red'], None, None, None, None],
    [None, None, C['red'], C['red'], C['red'], C['red'], C['red'], C['red'], C['red'], None, None, None],
    [None, C['stone'], C['stone'], C['stone'], C['stone'], C['stone'], C['stone'], C['stone'], C['stone'], C['stone'], None, None],
    [None, C['stone'], C['stone'], C['stone'], C['brown'], C['stone'], C['brown'], C['stone'], C['stone'], C['stone'], None, None],
    [None, C['stone'], C['stone'], C['stone'], C['brown'], C['stone'], C['brown'], C['stone'], C['stone'], C['stone'], None, None],
    [None, C['stone'], C['stone'], C['stone'], C['brown'], C['brown'], C['brown'], C['stone'], C['stone'], C['stone'], None, None],
    [None, C['stone'], C['stone'], C['stone'], C['stone'], C['stone'], C['stone'], C['stone'], C['stone'], C['stone'], None, None],
    [None, C['stone'], C['stone'], C['stone'], C['stone'], C['stone'], C['stone'], C['stone'], C['stone'], C['stone'], None, None],
    [None, C['stone'], C['stone'], C['stone'], C['stone'], C['stone'], C['stone'], C['stone'], C['stone'], C['stone'], None, None],
]

SPRITE_CHEST = [
    [None, None, None, None, None, None, None, None],
    [None, C['brown'], C['brown'], C['brown'], C['brown'], C['brown'], C['brown'], None],
    [C['brown'], C['dark_brown'], C['dark_brown'], C['dark_brown'], C['dark_brown'], C['dark_brown'], C['dark_brown'], C['brown']],
    [C['brown'], C['dark_brown'], C['gold'], C['dark_brown'], C['dark_brown'], C['gold'], C['dark_brown'], C['brown']],
    [C['brown'], C['dark_brown'], C['dark_brown'], C['dark_brown'], C['dark_brown'], C['dark_brown'], C['dark_brown'], C['brown']],
    [C['brown'], C['brown'], C['brown'], C['brown'], C['brown'], C['brown'], C['brown'], C['brown']],
    [None, None, None, None, None, None, None, None],
]

SPRITE_PORTAL = [
    [None, None, C['purple'], C['cyan'], C['purple'], C['cyan'], C['purple'], None, None],
    [None, C['purple'], C['cyan'], C['purple'], C['cyan'], C['purple'], C['cyan'], C['purple'], None],
    [C['purple'], C['cyan'], C['purple'], C['white'], C['white'], C['white'], C['purple'], C['cyan'], C['purple']],
    [C['cyan'], C['purple'], C['white'], C['cyan'], C['purple'], C['cyan'], C['white'], C['purple'], C['cyan']],
    [C['purple'], C['cyan'], C['white'], C['purple'], C['cyan'], C['purple'], C['white'], C['cyan'], C['purple']],
    [C['cyan'], C['purple'], C['white'], C['cyan'], C['purple'], C['cyan'], C['white'], C['purple'], C['cyan']],
    [C['purple'], C['cyan'], C['purple'], C['white'], C['white'], C['white'], C['purple'], C['cyan'], C['purple']],
    [None, C['purple'], C['cyan'], C['purple'], C['cyan'], C['purple'], C['cyan'], C['purple'], None],
    [None, None, C['purple'], C['cyan'], C['purple'], C['cyan'], C['purple'], None, None],
]

# 清除颜色引用
del C


# ============================================================================
# 枚举类型
# ============================================================================
class ItemType(Enum):
    WEAPON = "武器"
    ARMOR = "护甲"
    ACCESSORY = "饰品"
    CONSUMABLE = "消耗品"
    MATERIAL = "材料"
    QUEST = "任务物品"

class SkillType(Enum):
    PHYSICAL = "物理"
    MAGIC = "魔法"
    HEAL = "治疗"
    BUFF = "增益"
    DEBUFF = "减益"

class TileType(Enum):
    GRASS = 0
    WATER = 1
    SAND = 2
    STONE = 3
    FOREST = 4
    SNOW = 5
    LAVA = 6
    PATH = 7
    BRIDGE = 8
    FLOWER = 9
    MOUNTAIN = 10

class GameState(Enum):
    TITLE = "title"
    EXPLORE = "explore"
    DIALOGUE = "dialogue"
    BATTLE = "battle"
    INVENTORY = "inventory"
    SHOP = "shop"
    QUEST_LOG = "quest_log"
    CHARACTER = "character"
    GAME_OVER = "game_over"
    VICTORY = "victory"
    ARENA = "arena"
    SAVE_LOAD = "save_load"
