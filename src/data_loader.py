#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据加载模块 - 从JSON文件加载游戏数据
"""

import json
import os
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")


def _load_json(filename: str) -> dict:
    """加载JSON文件"""
    filepath = os.path.join(DATA_DIR, filename)
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def _tuple_from_list(lst: List) -> tuple:
    """将列表转换为元组（用于颜色等）"""
    if isinstance(lst, list):
        return tuple(lst)
    return lst


class ItemType(Enum):
    WEAPON = "WEAPON"
    ARMOR = "ARMOR"
    ACCESSORY = "ACCESSORY"
    CONSUMABLE = "CONSUMABLE"
    MATERIAL = "MATERIAL"
    QUEST = "QUEST"


class SkillType(Enum):
    PHYSICAL = "PHYSICAL"
    MAGIC = "MAGIC"
    HEAL = "HEAL"
    BUFF = "BUFF"
    DEBUFF = "DEBUFF"


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
    BESTIARY = "bestiary"


@dataclass
class Item:
    id: str
    name: str
    description: str
    item_type: ItemType
    icon: str
    price: int = 0
    attack: int = 0
    defense: int = 0
    magic: int = 0
    speed: int = 0
    heal_amount: int = 0
    mana_amount: int = 0

    @staticmethod
    def from_dict(data: dict) -> "Item":
        item_type = ItemType(data.get("type", "CONSUMABLE")) if data.get("type") else ItemType.CONSUMABLE
        return Item(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            item_type=item_type,
            icon=data.get("icon", ""),
            price=data.get("price", 0),
            attack=data.get("attack", 0),
            defense=data.get("defense", 0),
            magic=data.get("magic", 0),
            speed=data.get("speed", 0),
            heal_amount=data.get("heal_amount", 0),
            mana_amount=data.get("mana_amount", 0),
        )


@dataclass
class Skill:
    id: str
    name: str
    description: str
    skill_type: SkillType
    damage: int = 0
    heal_amount: int = 0
    mana_cost: int = 0
    unlock_level: int = 1
    buff_stat: str = ""
    buff_amount: int = 0
    buff_duration: int = 0

    @staticmethod
    def from_dict(data: dict) -> "Skill":
        skill_type = SkillType(data.get("type", "PHYSICAL")) if data.get("type") else SkillType.PHYSICAL
        return Skill(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            skill_type=skill_type,
            damage=data.get("damage", 0),
            heal_amount=data.get("heal_amount", 0),
            mana_cost=data.get("mana_cost", 0),
            unlock_level=data.get("unlock_level", 1),
            buff_stat=data.get("buff_stat", ""),
            buff_amount=data.get("buff_amount", 0),
            buff_duration=data.get("buff_duration", 0),
        )


@dataclass
class Enemy:
    id: str
    name: str
    level: int
    hp: int
    max_hp: int
    mp: int
    max_mp: int
    attack: int
    defense: int
    magic: int
    speed: int
    exp_reward: int
    gold_reward: int
    drops: List[str] = field(default_factory=list)
    skills: List[str] = field(default_factory=list)
    sprite_data: Optional[list] = None

    @staticmethod
    def from_dict(data: dict) -> "Enemy":
        return Enemy(
            id=data["id"],
            name=data["name"],
            level=data["level"],
            hp=data["hp"],
            max_hp=data["max_hp"],
            mp=data["mp"],
            max_mp=data["max_mp"],
            attack=data["attack"],
            defense=data["defense"],
            magic=data["magic"],
            speed=data["speed"],
            exp_reward=data["exp_reward"],
            gold_reward=data["gold_reward"],
            drops=data.get("drops", []),
            skills=data.get("skills", []),
            sprite_data=None,
        )


@dataclass
class QuestObjective:
    description: str
    target_type: str
    target_id: str = ""
    current: int = 0
    required: int = 1
    completed: bool = False


@dataclass
class Quest:
    id: str
    name: str
    description: str
    quest_type: str
    chapter: int = 0
    objectives: List[QuestObjective] = field(default_factory=list)
    rewards: Dict = field(default_factory=dict)
    is_completed: bool = False
    is_active: bool = False
    giver_npc: str = ""

    @staticmethod
    def from_dict(data: dict) -> "Quest":
        objectives = []
        for obj in data.get("objectives", []):
            objectives.append(
                QuestObjective(
                    description=obj["description"],
                    target_type=obj["target_type"],
                    target_id=obj.get("target_id", ""),
                    required=obj.get("required", 1),
                )
            )
        return Quest(
            id=data["id"],
            name=data["name"],
            description=data["description"],
            quest_type=data.get("type", "side"),
            chapter=data.get("chapter", 0),
            objectives=objectives,
            rewards=data.get("rewards", {}),
            giver_npc=data.get("giver_npc", ""),
        )


class Config:
    SCREEN_WIDTH = 1024
    SCREEN_HEIGHT = 768
    FPS = 60
    TILE_SIZE = 48
    PIXEL_SCALE = 3
    COLORS = {}
    TILE_COLORS = {}


class PixelArt:
    """像素艺术绘制辅助类"""

    _sprites = None
    _sprite_images = {}
    ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "sprites")

    @classmethod
    def load_sprites(cls) -> dict:
        """加载精灵数据"""
        if cls._sprites is None:
            data = _load_json("sprites.json")
            cls._sprites = data.get("sprites", {})
        return cls._sprites

    @classmethod
    def _load_image(cls, sprite_name: str):
        """从PNG文件加载精灵图像"""
        import pygame
        if sprite_name in cls._sprite_images:
            return cls._sprite_images[sprite_name]
        
        filepath = os.path.join(cls.ASSETS_DIR, f"{sprite_name}.png")
        if os.path.exists(filepath):
            surface = pygame.image.load(filepath)
            cls._sprite_images[sprite_name] = surface
            return surface
        return None

    @staticmethod
    def draw_pixel_art(surface, x, y, pixel_data, scale=3, offset_x=0, offset_y=0):
        """根据像素数据绘制像素艺术"""
        import pygame

        for row_idx, row in enumerate(pixel_data):
            for col_idx, color in enumerate(row):
                if color:
                    rect = pygame.Rect(
                        x + col_idx * scale + offset_x,
                        y + row_idx * scale + offset_y,
                        scale, scale,
                    )
                    pygame.draw.rect(surface, _tuple_from_list(color), rect)

    @classmethod
    def create_sprite(cls, sprite_name: str, scale: int = 3):
        """从PNG文件创建Sprite表面"""
        import pygame
        surface = cls._load_image(sprite_name)
        if surface:
            if scale != 1:
                new_width = surface.get_width() * scale
                new_height = surface.get_height() * scale
                scaled = pygame.transform.scale(surface, (new_width, new_height))
                return scaled
            return surface.copy()
        return None


class GameDatabase:
    """游戏数据管理器"""

    ITEMS: Dict[str, Item] = {}
    SKILLS: Dict[str, Skill] = {}
    ENEMIES: Dict[str, Enemy] = {}
    MAIN_QUESTS: List[Quest] = []
    SIDE_QUESTS: List[Quest] = []
    TILE_COLORS: Dict = {}

    _loaded = False

    @classmethod
    def load_all(cls):
        """加载所有游戏数据"""
        if cls._loaded:
            return

        config_data = _load_json("config.json")
        cls._load_config(config_data)
        cls._load_items()
        cls._load_skills()
        cls._load_enemies()
        cls._load_quests()
        cls._loaded = True

    @classmethod
    def _load_config(cls, data: dict):
        game_cfg = data.get("game", {})
        Config.SCREEN_WIDTH = game_cfg.get("screen_width", 1024)
        Config.SCREEN_HEIGHT = game_cfg.get("screen_height", 768)
        Config.FPS = game_cfg.get("fps", 60)
        Config.TILE_SIZE = game_cfg.get("tile_size", 48)
        Config.PIXEL_SCALE = game_cfg.get("pixel_scale", 3)

        colors = data.get("colors", {})
        Config.COLORS = {k: _tuple_from_list(v) for k, v in colors.items()}

        tile_colors = data.get("tile_colors", {})
        Config.TILE_COLORS = {TileType[k.upper()]: _tuple_from_list(v) for k, v in tile_colors.items()}

    @classmethod
    def _load_items(cls):
        data = _load_json("items.json")
        items = data.get("items", {})
        for item_id, item_data in items.items():
            cls.ITEMS[item_id] = Item.from_dict(item_data)

    @classmethod
    def _load_skills(cls):
        data = _load_json("skills.json")
        skills = data.get("skills", {})
        for skill_id, skill_data in skills.items():
            cls.SKILLS[skill_id] = Skill.from_dict(skill_data)

    @classmethod
    def _load_enemies(cls):
        data = _load_json("enemies.json")
        enemies = data.get("enemies", {})
        for enemy_id, enemy_data in enemies.items():
            cls.ENEMIES[enemy_id] = Enemy.from_dict(enemy_data)

    @classmethod
    def _load_quests(cls):
        data = _load_json("quests.json")
        main_quests = data.get("main_quests", [])
        for quest_data in main_quests:
            cls.MAIN_QUESTS.append(Quest.from_dict(quest_data))
        side_quests = data.get("side_quests", [])
        for quest_data in side_quests:
            cls.SIDE_QUESTS.append(Quest.from_dict(quest_data))

    @classmethod
    def get_item(cls, item_id: str) -> Optional[Item]:
        """获取物品"""
        return cls.ITEMS.get(item_id)

    @classmethod
    def get_skill(cls, skill_id: str) -> Optional[Skill]:
        """获取技能"""
        return cls.SKILLS.get(skill_id)

    @classmethod
    def get_enemy(cls, enemy_id: str) -> Optional[Enemy]:
        """获取敌人"""
        return cls.ENEMIES.get(enemy_id)

    @classmethod
    def get_main_quest(cls, quest_id: str) -> Optional[Quest]:
        """获取主线任务"""
        for quest in cls.MAIN_QUESTS:
            if quest.id == quest_id:
                return quest
        return None

    @classmethod
    def get_side_quest(cls, quest_id: str) -> Optional[Quest]:
        """获取支线任务"""
        for quest in cls.SIDE_QUESTS:
            if quest.id == quest_id:
                return quest
        return None

    @classmethod
    def get_all_items(cls) -> Dict[str, Item]:
        """获取所有物品"""
        return cls.ITEMS

    @classmethod
    def get_all_skills(cls) -> Dict[str, Skill]:
        """获取所有技能"""
        return cls.SKILLS

    @classmethod
    def get_all_enemies(cls) -> Dict[str, Enemy]:
        """获取所有敌人"""
        return cls.ENEMIES


def load_game_data():
    """加载所有游戏数据（便捷函数）"""
    GameDatabase.load_all()


def get_sprite(sprite_name: str, scale: int = None, frame: int = None) -> Any:
    """获取精灵表面"""
    if scale is None:
        scale = Config.PIXEL_SCALE
    
    if frame is not None:
        sprite_name = f"{sprite_name}_{frame}"
    
    return PixelArt.create_sprite(sprite_name, scale)


class AnimationManager:
    """动画管理器"""

    _animations = None
    _frame_timers = {}
    _current_frames = {}

    @classmethod
    def load_animations(cls) -> dict:
        """加载动画配置"""
        if cls._animations is None:
            data = _load_json("animations.json")
            cls._animations = data.get("animations", {})
        return cls._animations

    @classmethod
    def get_animation(cls, name: str) -> Optional[dict]:
        """获取动画配置"""
        animations = cls.load_animations()
        return animations.get(name)

    @classmethod
    def get_frame(cls, name: str, dt: int = 0) -> str:
        """获取当前动画帧名称"""
        anim = cls.get_animation(name)
        if not anim:
            return name
        
        frames = anim.get("frames", [name])
        if len(frames) == 1:
            return frames[0]
        
        if name not in cls._current_frames:
            cls._current_frames[name] = 0
            cls._frame_timers[name] = 0
        
        fps = anim.get("fps", 3)
        frame_duration = 1000 // fps
        
        cls._frame_timers[name] += dt
        if cls._frame_timers[name] >= frame_duration:
            cls._frame_timers[name] = 0
            cls._current_frames[name] = (cls._current_frames[name] + 1) % len(frames)
        
        return frames[cls._current_frames[name]]

    @classmethod
    def reset(cls, name: str):
        """重置动画帧"""
        if name in cls._current_frames:
            cls._current_frames[name] = 0
            cls._frame_timers[name] = 0

    @classmethod
    def get_animated_sprite(cls, sprite_name: str, scale: int = None, dt: int = 0) -> Any:
        """获取带动画的精灵"""
        if scale is None:
            scale = Config.PIXEL_SCALE
        
        frame_name = cls.get_frame(sprite_name, dt)
        return PixelArt.create_sprite(frame_name, scale)