#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
幻境传说：迷失大陆
A Fantasy Tale: The Lost Continent
开放世界冒险游戏
"""

import pygame
import sys
import random
import json
import os
from enum import Enum
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Tuple, Callable
import numpy as np

# 导入游戏模块
from src.data_loader import (
    load_game_data,
    GameDatabase,
    Config,
    PixelArt,
    ItemType,
    SkillType,
    TileType,
    GameState,
    get_sprite,
)
from src.constants import (
    SPRITE_PLAYER, SPRITE_NPC, SPRITE_ENEMY,
    SPRITE_TREE, SPRITE_HOUSE, SPRITE_CHEST, SPRITE_PORTAL,
    load_sprites,
)
from src.models import (
    Item, Skill, Enemy, Quest, QuestObjective,
)


# ============================================================================
# 玩家角色
# ============================================================================
@dataclass
class Player:
    """玩家角色数据"""
    name: str = "勇者"
    level: int = 1
    exp: int = 0
    exp_to_next: int = 100
    
    # 基础属性
    hp: int = 100
    max_hp: int = 100
    mp: int = 30
    max_mp: int = 30
    attack: int = 15
    defense: int = 10
    magic: int = 8
    speed: int = 12
    
    # 装备
    weapon: Optional[Item] = None
    armor: Optional[Item] = None
    accessory: Optional[Item] = None
    
    # 背包
    inventory: Dict[str, int] = field(default_factory=dict)  # item_id: quantity
    gold: int = 50
    
    # 技能
    unlocked_skills: List[str] = field(default_factory=list)
    
    # 位置
    x: int = 0
    y: int = 0
    current_map: str = "village"
    
    # 状态
    buffs: List[Dict] = field(default_factory=list)  # [{"stat": "attack", "amount": 10, "duration": 3}]
    
    # 任务
    active_quests: List[str] = field(default_factory=list)
    completed_quests: List[str] = field(default_factory=list)
    
    # 统计
    enemies_defeated: int = 0
    treasures_found: int = 0
    areas_explored: set = field(default_factory=set)

    # 图鉴
    known_enemies: set = field(default_factory=set)
    known_items: set = field(default_factory=set)
    discovered_locations: set = field(default_factory=set)
    
    def get_total_attack(self):
        total = self.attack
        if self.weapon: total += self.weapon.attack
        if self.armor: total += self.armor.attack
        if self.accessory: total += self.accessory.attack
        for buff in self.buffs:
            if buff["stat"] == "attack":
                total += buff["amount"]
        return total
    
    def get_total_defense(self):
        total = self.defense
        if self.weapon: total += self.weapon.defense
        if self.armor: total += self.armor.defense
        if self.accessory: total += self.accessory.defense
        for buff in self.buffs:
            if buff["stat"] == "defense":
                total += buff["amount"]
        return total
    
    def get_total_magic(self):
        total = self.magic
        if self.weapon: total += self.weapon.magic
        if self.armor: total += self.armor.magic
        if self.accessory: total += self.accessory.magic
        return total
    
    def get_total_speed(self):
        total = self.speed
        if self.weapon: total += self.weapon.speed
        if self.armor: total += self.armor.speed
        if self.accessory: total += self.accessory.speed
        return total
    
    def gain_exp(self, amount):
        self.exp += amount
        while self.exp >= self.exp_to_next:
            self.level_up()
    
    def level_up(self):
        self.exp -= self.exp_to_next
        self.level += 1
        self.exp_to_next = int(self.exp_to_next * 1.5)
        
        # 属性成长
        self.max_hp += 15
        self.hp = self.max_hp
        self.max_mp += 8
        self.mp = self.max_mp
        self.attack += 3
        self.defense += 2
        self.magic += 2
        self.speed += 1
        
        # 检查新技能解锁
        for skill_id, skill in GameDatabase.SKILLS.items():
            if skill.unlock_level <= self.level and skill_id not in self.unlocked_skills:
                self.unlocked_skills.append(skill_id)
    
    def add_item(self, item_id: str, quantity: int = 1):
        if item_id in self.inventory:
            self.inventory[item_id] += quantity
        else:
            self.inventory[item_id] = quantity
    
    def remove_item(self, item_id: str, quantity: int = 1) -> bool:
        if item_id in self.inventory and self.inventory[item_id] >= quantity:
            self.inventory[item_id] -= quantity
            if self.inventory[item_id] <= 0:
                del self.inventory[item_id]
            return True
        return False
    
    def has_item(self, item_id: str, quantity: int = 1) -> bool:
        return self.inventory.get(item_id, 0) >= quantity
    
    def equip_item(self, item_id: str) -> bool:
        if item_id not in GameDatabase.ITEMS:
            return False
        item = GameDatabase.ITEMS[item_id]
        if not self.has_item(item_id):
            return False

        # 卸下当前装备，添加回背包
        if item.item_type == ItemType.WEAPON:
            if self.weapon:
                self.add_item(self.weapon.id)
            self.weapon = item
        elif item.item_type == ItemType.ARMOR:
            if self.armor:
                self.add_item(self.armor.id)
            self.armor = item
        elif item.item_type == ItemType.ACCESSORY:
            if self.accessory:
                self.add_item(self.accessory.id)
            self.accessory = item

        # 从背包中移除已装备的物品（只移除1个）
        self.remove_item(item_id, 1)
        return True
    
    def use_item(self, item_id: str) -> bool:
        if item_id not in GameDatabase.ITEMS:
            return False
        item = GameDatabase.ITEMS[item_id]
        
        if item.item_type == ItemType.CONSUMABLE:
            if item.heal_amount > 0:
                self.hp = min(self.max_hp, self.hp + item.heal_amount)
            if item.mana_amount > 0:
                self.mp = min(self.max_mp, self.mp + item.mana_amount)
            self.remove_item(item_id)
            return True
        return False
    
    def update_buffs(self):
        """更新buff持续时间"""
        self.buffs = [b for b in self.buffs if b["duration"] > 0]
        for buff in self.buffs:
            buff["duration"] -= 1


# ============================================================================
# 地图生成
# ============================================================================
class GameMap:
    """游戏地图"""
    
    def __init__(self, name: str, width: int, height: int, tile_data: List[List[int]], 
                 enemies: List[Dict] = None, npcs: List[Dict] = None, 
                 chests: List[Dict] = None, portals: List[Dict] = None,
                 description: str = ""):
        self.name = name
        self.width = width
        self.height = height
        self.tiles = tile_data
        self.enemies = enemies or []  # [{"id": "slime", "x": 5, "y": 5}]
        self.npcs = npcs or []  # [{"id": "elder", "x": 10, "y": 8, "name": "村长", "dialogue": []}]
        self.chests = chests or []  # [{"x": 15, "y": 12, "items": ["health_potion"], "opened": False}]
        self.portals = portals or []  # [{"x": 20, "y": 0, "target_map": "desert", "target_x": 2, "target_y": 2}]
        self.description = description
        self.explored = [[False for _ in range(width)] for _ in range(height)]
        
    def get_tile(self, x: int, y: int) -> TileType:
        if 0 <= x < self.width and 0 <= y < self.height:
            return TileType(self.tiles[y][x])
        return TileType.MOUNTAIN
    
    def is_walkable(self, x: int, y: int) -> bool:
        tile = self.get_tile(x, y)
        return tile not in (TileType.WATER, TileType.LAVA, TileType.MOUNTAIN)
    
    def explore_area(self, cx: int, cy: int, radius: int = 3):
        """探索周围区域"""
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                nx, ny = cx + dx, cy + dy
                if 0 <= nx < self.width and 0 <= ny < self.height:
                    self.explored[ny][nx] = True


# ============================================================================
# 地图数据
# ============================================================================
def create_world_maps() -> Dict[str, GameMap]:
    """创建所有游戏地图"""
    maps = {}
    
    # 帮助函数：创建填充地图
    def create_filled_map(width, height, fill_tile):
        return [[fill_tile.value for _ in range(width)] for _ in range(height)]
    
    # 村庄地图 (起始点)
    village_tiles = create_filled_map(30, 25, TileType.GRASS)
    # 添加路径
    for x in range(5, 25):
        village_tiles[12][x] = TileType.PATH.value
    for y in range(5, 20):
        village_tiles[y][15] = TileType.PATH.value
    # 添加房屋
    for y in range(3, 8):
        for x in range(3, 8):
            village_tiles[y][x] = TileType.STONE.value
    for y in range(3, 8):
        for x in range(20, 25):
            village_tiles[y][x] = TileType.STONE.value
    # 添加水池
    for y in range(18, 22):
        for x in range(5, 10):
            village_tiles[y][x] = TileType.WATER.value
    
    maps["village"] = GameMap(
        "新手村庄", 30, 25, village_tiles,
        npcs=[
            {"id": "village_elder", "x": 5, "y": 5, "name": "村长", 
             "dialogue": [
                 "勇者啊，你终于醒来了。",
                 "我们的世界正面临着巨大的危机。",
                 "魔王的力量正在侵蚀这片大陆。",
                 "传说中，只有集齐四块水晶碎片的勇者才能击败魔王。",
                 "请先去草原上历练一番吧。",
                 "往东走可以到达草原，那里有一些弱小的怪物。"
             ],
             "quest_giver": "main_ch1"},
            {"id": "village_alchemist", "x": 22, "y": 5, "name": "药师",
             "dialogue": [
                 "你好啊，我是村庄的药师。",
                 "我正在研究新的药水，需要一些药草。",
                 "如果你能帮我采集5份药草，我会给你一些药水作为回报。"
             ],
             "quest_giver": "side_herbs"},
            {"id": "village_hunter", "x": 22, "y": 6, "name": "猎人",
             "dialogue": [
                 "最近狼群越来越猖獗了。",
                 "已经有好几只家畜被狼咬死了。",
                 "勇者大人，能帮帮我们吗？"
             ],
             "quest_giver": "side_wolf_hunt"},
            {"id": "village_mage", "x": 5, "y": 6, "name": "法师",
             "dialogue": [
                 "我对怪物的魔法抗性很感兴趣。",
                 "如果你能帮我研究一下，那就太好了。",
                 "击败一些怪物，记录它们的魔法抗性。"
             ],
             "quest_giver": "side_magic_study"},
            {"id": "village_guard", "x": 15, "y": 8, "name": "守卫",
             "dialogue": [
                 "草原上出现了强盗营地。",
                 "我们需要有人去清剿他们。",
                 "勇者大人，这个任务就拜托你了！"
             ],
             "quest_giver": "side_bandit_camp"},
            {"id": "treasure_map_npc", "x": 15, "y": 6, "name": "寻宝人",
             "dialogue": [
                 "嘿，朋友，你知道宝藏的事吗？",
                 "草原上藏着好多宝箱呢！",
                 "找到3个宝箱的话，我就给你好东西！"
             ],
             "quest_giver": "side_treasure"},
            {"id": "shopkeeper", "x": 15, "y": 10, "name": "商店老板",
             "dialogue": [
                 "欢迎光临！需要什么尽管说。"
             ],
             "is_shop": True,
             "shop_items": ["health_potion", "mana_potion", "wooden_sword", "cloth_armor", "antidote"]},
        ],
        chests=[
            {"x": 27, "y": 3, "items": ["health_potion", "health_potion"], "opened": False},
            {"x": 3, "y": 22, "items": ["mana_potion"], "opened": False},
        ],
        portals=[
            {"x": 28, "y": 12, "target_map": "grassland", "target_x": 2, "target_y": 12, "name": "→ 草原"}
        ],
        description="宁静的起点，勇者的出发之地。"
    )
    
    # 草原地图
    grassland_tiles = create_filled_map(50, 40, TileType.GRASS)
    # 添加道路
    for x in range(0, 50):
        grassland_tiles[20][x] = TileType.PATH.value
    for y in range(0, 40):
        grassland_tiles[y][25] = TileType.PATH.value
    # 添加树林
    for y in range(5, 15):
        for x in range(5, 15):
            if random.random() > 0.3:
                grassland_tiles[y][x] = TileType.FOREST.value
    # 添加水域
    for y in range(25, 30):
        for x in range(30, 38):
            grassland_tiles[y][x] = TileType.WATER.value
    # 添加花田
    for y in range(8, 12):
        for x in range(35, 42):
            grassland_tiles[y][x] = TileType.FLOWER.value
    
    maps["grassland"] = GameMap(
        "迷雾草原", 50, 40, grassland_tiles,
        enemies=[
            {"id": "slime", "x": 10, "y": 10},
            {"id": "slime", "x": 15, "y": 8},
            {"id": "slime", "x": 8, "y": 18},
            {"id": "goblin", "x": 20, "y": 15},
            {"id": "goblin", "x": 30, "y": 12},
            {"id": "wolf", "x": 35, "y": 20},
            {"id": "wolf", "x": 40, "y": 25},
            {"id": "bandit", "x": 42, "y": 8},
            {"id": "bandit", "x": 45, "y": 15},
            {"id": "forest_spirit", "x": 48, "y": 20},
        ],
        npcs=[
            {"id": "traveler", "x": 25, "y": 20, "name": "旅行者",
             "dialogue": [
                 "你好啊，旅行者。",
                 "前方就是沙漠了，那里很危险，要小心啊。"
             ]},
        ],
        chests=[
            {"x": 12, "y": 6, "items": ["health_potion", "gold_50"], "opened": False},
            {"x": 38, "y": 35, "items": ["iron_sword", "health_potion"], "opened": False},
            {"x": 45, "y": 5, "items": ["leather_armor"], "opened": False},
        ],
        portals=[
            {"x": 0, "y": 12, "target_map": "village", "target_x": 28, "target_y": 12, "name": "← 村庄"},
            {"x": 49, "y": 20, "target_map": "desert", "target_x": 2, "target_y": 18, "name": "→ 沙漠"},
        ],
        description="广阔的草原，偶尔出现一些弱小的怪物。"
    )
    
    # 沙漠地图
    desert_tiles = create_filled_map(50, 40, TileType.SAND)
    # 添加道路
    for x in range(0, 50):
        desert_tiles[18][x] = TileType.PATH.value
    # 添加流沙
    for y in range(10, 15):
        for x in range(10, 20):
            if random.random() > 0.5:
                desert_tiles[y][x] = TileType.WATER.value  # 流沙
    # 添加遗迹
    for y in range(20, 28):
        for x in range(25, 35):
            desert_tiles[y][x] = TileType.STONE.value
    
    maps["desert"] = GameMap(
        "灼热沙漠", 50, 40, desert_tiles,
        enemies=[
            {"id": "sand_worm", "x": 15, "y": 18},  # Bug #6 fix: 移动到PATH上
            {"id": "sand_worm", "x": 20, "y": 25},
            {"id": "desert_scorpion", "x": 30, "y": 15},
            {"id": "desert_scorpion", "x": 35, "y": 30},
            {"id": "tomb_guardian", "x": 28, "y": 22},
            {"id": "tomb_guardian", "x": 32, "y": 25},
            {"id": "sand_mage", "x": 40, "y": 20},
            {"id": "ancient_mummy", "x": 30, "y": 24},
        ],
        npcs=[
            {"id": "desert_sage", "x": 10, "y": 18, "name": "沙漠贤者",
             "dialogue": [
                 "你终于来了，勇者。",
                 "水晶碎片就在这片沙漠的遗迹中。",
                 "但要小心，那里有强大的守卫。"
             ],
             "quest_giver": "main_ch2"},
            {"id": "desert_trader", "x": 8, "y": 25, "name": "沙漠商人",
             "dialogue": [
                 "哟， rare customer!",
                 "我听说沙漠深处有一座遗迹。",
                 "如果你去探险，记得多带点药水。"
             ],
             "quest_giver": "side_sand_ruins"},
            {"id": "desert_shop", "x": 5, "y": 18, "name": "沙漠商人",
             "dialogue": ["沙漠里什么都可以买到，只要你出得起价。"],
             "is_shop": True,
             "shop_items": ["greater_health_potion", "greater_mana_potion", "iron_sword", "leather_armor", "chain_mail", "antidote"]},
        ],
        chests=[
            {"x": 27, "y": 21, "items": ["crystal_shard", "steel_blade"], "opened": False, "is_quest": True},
            {"x": 45, "y": 35, "items": ["greater_health_potion", "greater_health_potion"], "opened": False},
        ],
        portals=[
            {"x": 0, "y": 18, "target_map": "grassland", "target_x": 49, "target_y": 20, "name": "← 草原"},
            {"x": 49, "y": 18, "target_map": "snow_mountain", "target_x": 2, "target_y": 20, "name": "→ 雪山"},
        ],
        description="炎热的沙漠，隐藏着远古的秘密。"
    )
    
    # 雪山地图
    snow_tiles = create_filled_map(50, 40, TileType.SNOW)
    # 添加道路
    for x in range(0, 50):
        snow_tiles[20][x] = TileType.PATH.value
    # 添加冰川
    for y in range(5, 12):
        for x in range(10, 25):
            if random.random() > 0.4:
                snow_tiles[y][x] = TileType.STONE.value
    # 添加冰冻湖
    for y in range(30, 35):
        for x in range(20, 30):
            snow_tiles[y][x] = TileType.WATER.value
    
    maps["snow_mountain"] = GameMap(
        "冰霜雪山", 50, 40, snow_tiles,
        enemies=[
            {"id": "ice_golem", "x": 15, "y": 10},
            {"id": "ice_golem", "x": 25, "y": 8},
            {"id": "snow_witch", "x": 35, "y": 15},
            {"id": "yeti", "x": 40, "y": 25},
            {"id": "yeti", "x": 45, "y": 12},
            {"id": "frost_dragon", "x": 45, "y": 5},
            {"id": "avalanche_spirit", "x": 48, "y": 20},
        ],
        npcs=[
            {"id": "snow_hermit", "x": 10, "y": 20, "name": "雪山隐士",
             "dialogue": [
                 "山上的冰霜龙守护着第二块水晶碎片。",
                 "它是非常强大的存在。",
                 "但你有信念的话，一定能战胜它。"
             ],
             "quest_giver": "main_ch3"},
            {"id": "dragon_slayer_guild", "x": 15, "y": 25, "name": "屠龙公会",
             "dialogue": [
                 "我们是屠龙公会。",
                 "如果你能击败冰霜龙，我们承认你是真正的屠龙勇士！"
             ],
             "quest_giver": "side_dragon_slayer"},
        ],
        chests=[
            {"x": 43, "y": 7, "items": ["ancient_key", "greater_health_potion"], "opened": False},
            {"x": 35, "y": 35, "items": ["elixir", "wisdom_crown"], "opened": False},
        ],
        portals=[
            {"x": 0, "y": 20, "target_map": "desert", "target_x": 49, "target_y": 18, "name": "← 沙漠"},
            {"x": 49, "y": 20, "target_map": "volcano", "target_x": 2, "target_y": 20, "name": "→ 火山"},
        ],
        description="寒冷的雪山，栖息着强大的魔物。"
    )
    
    # 火山地图
    volcano_tiles = create_filled_map(50, 40, TileType.STONE)
    # 添加道路
    for x in range(0, 50):
        volcano_tiles[20][x] = TileType.PATH.value
    # 添加熔岩
    for y in range(5, 15):
        for x in range(5, 15):
            if random.random() > 0.3:
                volcano_tiles[y][x] = TileType.LAVA.value
    for y in range(30, 38):
        for x in range(35, 48):
            volcano_tiles[y][x] = TileType.LAVA.value
    # 添加魔王城
    for y in range(15, 25):
        for x in range(40, 48):
            volcano_tiles[y][x] = TileType.STONE.value
    
    maps["volcano"] = GameMap(
        "烈焰火山", 50, 40, volcano_tiles,
        enemies=[
            {"id": "fire_elemental", "x": 10, "y": 20},
            {"id": "fire_elemental", "x": 18, "y": 15},
            {"id": "lava_golem", "x": 25, "y": 10},
            {"id": "lava_golem", "x": 30, "y": 25},
            {"id": "flame_demon", "x": 35, "y": 18},
            {"id": "inferno_wyrm", "x": 42, "y": 10},
            {"id": "demon_lord", "x": 45, "y": 18},
        ],
        npcs=[
            {"id": "volcano_guide", "x": 10, "y": 20, "name": "火山向导",
             "dialogue": [
                 "魔王就在那座城堡里。",
                 "这是最后的战斗了。",
                 "勇者，祝你好运！"
             ],
             "quest_giver": "main_ch4"},
            {"id": "volcano_miner", "x": 20, "y": 25, "name": "火山矿工",
             "dialogue": [
                 "火山深处有很多珍贵的矿石。",
                 "但也布满了怪物。",
                 "如果你能帮我探路，那就太好了。"
             ],
             "quest_giver": "side_volcano_explore"},
            {"id": "arena_master", "x": 30, "y": 20, "name": "竞技场大师",
             "dialogue": [
                 "欢迎来到竞技场！",
                 "在这里证明你的实力吧！"
             ],
             "is_arena": True},
        ],
        chests=[
            {"x": 8, "y": 30, "items": ["elixir", "legendary_sword"], "opened": False},
            {"x": 38, "y": 8, "items": ["plate_armor", "greater_health_potion"], "opened": False},
        ],
        portals=[
            {"x": 0, "y": 20, "target_map": "snow_mountain", "target_x": 49, "target_y": 20, "name": "← 雪山"},
        ],
        description="灼热的火山，魔王的领地。"
    )
    
    return maps


# ============================================================================
# 渲染器
# ============================================================================
class Renderer:
    """游戏渲染器"""
    
    def __init__(self, screen):
        self.screen = screen
        self.tile_size = Config.TILE_SIZE
        self.scale = Config.PIXEL_SCALE
        
        # 预渲染精灵
        self.sprites = {}
        self._preload_sprites()
        
        # 字体
        self.font_small = pygame.font.SysFont(['microsoftyahei', 'simsun', 'arial'], 16)
        self.font_medium = pygame.font.SysFont(['microsoftyahei', 'simsun', 'arial'], 20)
        self.font_large = pygame.font.SysFont(['microsoftyahei', 'simsun', 'arial'], 28)
        self.font_title = pygame.font.SysFont(['microsoftyahei', 'simsun', 'arial'], 36)
    
    def _preload_sprites(self):
        """预渲染所有像素精灵"""
        self.sprites['player'] = get_sprite('player', self.scale)
        self.sprites['npc'] = get_sprite('npc', self.scale)
        self.sprites['enemy'] = get_sprite('enemy', self.scale)
        self.sprites['tree'] = get_sprite('tree', self.scale)
        self.sprites['house'] = get_sprite('house', self.scale)
        self.sprites['chest'] = get_sprite('chest', self.scale)
        self.sprites['portal'] = get_sprite('portal', self.scale)
    
    def draw_tile(self, x, y, tile_type: TileType, camera_x=0, camera_y=0):
        """绘制单个瓦片"""
        screen_x = x * self.tile_size - camera_x
        screen_y = y * self.tile_size - camera_y
        
        # 检查是否在屏幕范围内
        if screen_x < -self.tile_size or screen_x > Config.SCREEN_WIDTH or \
           screen_y < -self.tile_size or screen_y > Config.SCREEN_HEIGHT:
            return
        
        color = GameDatabase.TILE_COLORS.get(tile_type, Config.COLORS['black'])
        rect = pygame.Rect(screen_x, screen_y, self.tile_size, self.tile_size)
        pygame.draw.rect(self.screen, color, rect)
        
        # 添加瓦片纹理
        if tile_type == TileType.GRASS:
            # 草丛纹理
            for i in range(3):
                gx = screen_x + random.randint(5, self.tile_size - 8)
                gy = screen_y + random.randint(5, self.tile_size - 8)
                pygame.draw.rect(self.screen, Config.COLORS['dark_green'], (gx, gy, 3, 6))
        elif tile_type == TileType.FOREST:
            # 绘制树木
            if random.random() > 0.5 and self.sprites.get('tree'):
                self.screen.blit(self.sprites['tree'], (screen_x + 5, screen_y - 10))
        elif tile_type == TileType.FLOWER:
            # 花朵
            for i in range(2):
                fx = screen_x + random.randint(8, self.tile_size - 12)
                fy = screen_y + random.randint(8, self.tile_size - 12)
                pygame.draw.circle(self.screen, Config.COLORS['pink'], (fx, fy), 3)
                pygame.draw.circle(self.screen, Config.COLORS['yellow'], (fx, fy), 2)
    
    def draw_map(self, game_map: GameMap, camera_x, camera_y):
        """绘制整个地图"""
        # 将摄像机坐标转换为整数
        camera_x = int(camera_x)
        camera_y = int(camera_y)
        
        # 计算可见区域
        start_tile_x = max(0, camera_x // self.tile_size)
        start_tile_y = max(0, camera_y // self.tile_size)
        end_tile_x = min(game_map.width, (camera_x + Config.SCREEN_WIDTH) // self.tile_size + 2)
        end_tile_y = min(game_map.height, (camera_y + Config.SCREEN_HEIGHT) // self.tile_size + 2)
        
        for y in range(start_tile_y, end_tile_y):
            for x in range(start_tile_x, end_tile_x):
                tile_type = game_map.get_tile(x, y)
                
                # 战争迷雾效果 - 未探索的区域显示为黑色
                if not game_map.explored[y][x]:
                    screen_x = x * self.tile_size - camera_x
                    screen_y = y * self.tile_size - camera_y
                    rect = pygame.Rect(screen_x, screen_y, self.tile_size, self.tile_size)
                    pygame.draw.rect(self.screen, (20, 20, 30), rect)
                    continue
                
                self.draw_tile(x, y, tile_type, camera_x, camera_y)
    
    def draw_entity(self, sprite_name, x, y, camera_x, camera_y):
        """绘制实体"""
        screen_x = x * self.tile_size - camera_x
        screen_y = y * self.tile_size - camera_y
        
        sprite = self.sprites.get(sprite_name)
        if sprite:
            # 居中偏移
            offset_x = (self.tile_size - sprite.get_width()) // 2
            offset_y = (self.tile_size - sprite.get_height()) // 2
            self.screen.blit(sprite, (screen_x + offset_x, screen_y + offset_y))
    
    def draw_text(self, text, x, y, color=None, font=None, center=False):
        """绘制文本"""
        if color is None:
            color = (255, 255, 255)
        if font is None:
            font = self.font_medium
        
        # 处理中文文本
        if isinstance(text, str):
            text_surface = font.render(text, True, color)
        else:
            text_surface = font.render(str(text), True, color)
        
        if center:
            text_rect = text_surface.get_rect(center=(x, y))
            self.screen.blit(text_surface, text_rect)
        else:
            self.screen.blit(text_surface, (x, y))
    
    def draw_text_box(self, lines, title=None):
        """绘制文本框"""
        box_width = 700
        box_height = max(150, len(lines) * 30 + 60)
        box_x = (Config.SCREEN_WIDTH - box_width) // 2
        box_y = Config.SCREEN_HEIGHT - box_height - 20
        
        # 绘制背景
        bg_surface = pygame.Surface((box_width, box_height), pygame.SRCALPHA)
        bg_surface.fill((0, 0, 0, 200))
        pygame.draw.rect(bg_surface, Config.COLORS['gold'], bg_surface.get_rect(), 3)
        self.screen.blit(bg_surface, (box_x, box_y))
        
        # 绘制标题
        if title:
            self.draw_text(title, box_x + 20, box_y + 10, Config.COLORS['gold'], self.font_large)
            start_y = box_y + 45
        else:
            start_y = box_y + 15
        
        # 绘制文本行
        for i, line in enumerate(lines):
            self.draw_text(line, box_x + 20, start_y + i * 28, Config.COLORS['white'], self.font_medium)
    
    def draw_bar(self, x, y, width, height, current, maximum, color):
        """绘制进度条"""
        # 背景
        pygame.draw.rect(self.screen, Config.COLORS['dark_gray'], (x, y, width, height))
        # 前景
        fill_width = int(width * (current / maximum)) if maximum > 0 else 0
        pygame.draw.rect(self.screen, color, (x, y, fill_width, height))
        # 边框
        pygame.draw.rect(self.screen, Config.COLORS['white'], (x, y, width, height), 2)
    
    def draw_inventory_slot(self, x, y, width, height, item, quantity, selected=False):
        """绘制背包格子"""
        # 背景
        color = Config.COLORS['dark_gray'] if not selected else Config.COLORS['gold']
        pygame.draw.rect(self.screen, color, (x, y, width, height))
        pygame.draw.rect(self.screen, Config.COLORS['gray'], (x, y, width, height), 2)
        
        if item:
            # 物品图标
            self.draw_text(item.icon, x + 5, y + 5, Config.COLORS['white'], self.font_medium)
            # 物品名称
            self.draw_text(item.name, x + 30, y + 5, Config.COLORS['white'], self.font_small)
            # 数量
            if quantity > 1:
                self.draw_text(f"x{quantity}", x + width - 30, y + height - 18, Config.COLORS['yellow'], self.font_small)
    
    def draw_menu_background(self):
        """绘制菜单背景"""
        overlay = pygame.Surface((Config.SCREEN_WIDTH, Config.SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))


# ============================================================================
# 游戏状态管理
# ============================================================================
class Game:
    """主游戏类"""

    def __init__(self):
        load_game_data()
        load_sprites()

        pygame.init()
        self.screen = pygame.display.set_mode((Config.SCREEN_WIDTH, Config.SCREEN_HEIGHT))
        pygame.display.set_caption("幻境传说：迷失大陆")
        self.clock = pygame.time.Clock()
        self.running = True

        self.renderer = Renderer(self.screen)
        self.state = GameState.TITLE

        # 初始化瓦片颜色映射
        GameDatabase.TILE_COLORS = {
            TileType.GRASS: Config.COLORS['grass'],
            TileType.WATER: Config.COLORS['water'],
            TileType.SAND: Config.COLORS['sand'],
            TileType.STONE: Config.COLORS['stone'],
            TileType.FOREST: Config.COLORS['forest'],
            TileType.SNOW: Config.COLORS['snow'],
            TileType.LAVA: Config.COLORS['lava'],
            TileType.PATH: (180, 160, 120),
            TileType.BRIDGE: (140, 100, 60),
            TileType.FLOWER: (100, 180, 80),
            TileType.MOUNTAIN: (100, 100, 110),
        }

        # 游戏数据
        self.player = Player()
        self.maps = create_world_maps()
        self.current_map = self.maps["village"]
        self.camera_x = 0
        self.camera_y = 0
        
        # 对话系统
        self.dialogue_lines = []
        self.dialogue_index = 0
        self.current_npc = None
        
        # 战斗系统
        self.battle_enemy = None
        self.battle_log = []
        self.battle_turn = "player"  # "player" 或 "enemy"
        self.battle_menu_index = 0
        self.battle_submenu_index = 0
        self.battle_selecting_skill = False
        self.battle_selecting_item = False
        self.player_turn_done = False
        self.battle_ended = False  # 战斗结束标记，防止重复调用
        
        # 商店系统
        self.current_shop = None
        self.shop_menu_index = 0
        self.shop_buy_mode = True
        
        # 菜单系统
        self.inventory_menu_index = 0
        self.inventory_page = 0
        self.character_menu_index = 0
        self.quest_menu_index = 0

        # 图鉴系统
        self.bestiary_tab = 0  # 0:敌人 1:物品 2:技能
        self.bestiary_index = 0
        
        # 标题画面
        self.title_menu_index = 0
        
        # 游戏时间
        self.game_time = 0
        self.frame_count = 0
        
        # 消息提示
        self.message = ""
        self.message_timer = 0
        
        # 设置玩家初始位置
        self.player.x = 15
        self.player.y = 12
        self.player.current_map = "village"
        self.player.add_item("health_potion", 3)
        self.player.add_item("wooden_sword")
        self.player.add_item("cloth_armor")
        self.player.equip_item("wooden_sword")
        self.player.equip_item("cloth_armor")

        # 探索起始区域
        self.current_map.explore_area(self.player.x, self.player.y, 4)
        self.player.areas_explored.add("village")

        # 初始化摄像机位置
        self.update_camera()

        # 按键状态追踪
        self.keys_pressed = {}
        self.move_cooldown = 0  # 移动冷却时间（帧）
        self.move_delay = 8  # 每8帧移动一次（60FPS下约7.5次/秒）
        self.steps_since_encounter = 3  # 移动3步后才能遇敌
        
        # 输入防抖
        self.input_cooldown = 0
        self.input_delay = 8  # 8帧防抖（约133ms）
        
        # 存档系统
        self.save_dir = "saves"
        self.save_slots = 3  # 3个存档位
        self.save_menu_index = 0
        self.save_menu_active = False
        
        # 确保存档目录存在
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)

    def reset_game(self):
        """重置游戏数据（不重新初始化pygame）"""
        # 重置玩家
        self.player = Player()
        self.maps = create_world_maps()
        self.current_map = self.maps["village"]
        self.camera_x = 0
        self.camera_y = 0

        # 重置对话
        self.dialogue_lines = []
        self.dialogue_index = 0
        self.current_npc = None

        # 重置战斗
        self.battle_enemy = None
        self.battle_log = []
        self.battle_turn = "player"
        self.battle_menu_index = 0
        self.battle_submenu_index = 0
        self.battle_selecting_skill = False
        self.battle_selecting_item = False
        self.player_turn_done = False
        self.is_arena_battle = False
        self.battle_ended = False  # Bug #1 fix

        # 重置商店
        self.current_shop = None
        self.shop_menu_index = 0
        self.shop_buy_mode = True

        # 重置菜单
        self.inventory_menu_index = 0
        self.inventory_page = 0
        self.character_menu_index = 0
        self.quest_menu_index = 0

        # 重置标题
        self.title_menu_index = 0

        # 重置游戏时间和消息
        self.game_time = 0
        self.frame_count = 0
        self.message = ""
        self.message_timer = 0

        # 重置状态
        self.state = GameState.TITLE

        # 设置玩家初始位置
        self.player.x = 15
        self.player.y = 12
        self.player.current_map = "village"
        self.player.add_item("health_potion", 3)
        self.player.add_item("wooden_sword")
        self.player.add_item("cloth_armor")
        self.player.equip_item("wooden_sword")
        self.player.equip_item("cloth_armor")

        # 探索起始区域
        self.current_map.explore_area(self.player.x, self.player.y, 4)
        self.player.areas_explored.add("village")

        # 重置按键状态
        self.keys_pressed = {}
        self.move_cooldown = 0
        self.input_cooldown = 0
        
        # 重置存档菜单
        self.save_menu_index = 0
        self.save_menu_active = False
        
        # 初始化摄像机位置
        self.update_camera()
    
    def show_message(self, msg, duration=120):
        """显示短暂消息"""
        self.message = msg
        self.message_timer = duration
    
    def get_save_file(self, slot: int) -> str:
        """获取存档文件路径"""
        return os.path.join(self.save_dir, f"save_{slot}.json")
    
    def save_game(self, slot: int) -> bool:
        """保存游戏到指定存档位"""
        try:
            save_data = {
                "player": self._serialize_player(),
                "current_map": self.player.current_map,
                "game_time": self.game_time,
                "completed_quests": self.player.completed_quests,
                "active_quests": self.player.active_quests,
                "stats": {
                    "enemies_defeated": self.player.enemies_defeated,
                    "treasures_found": self.player.treasures_found,
                    "areas_explored": list(self.player.areas_explored)
                }
            }
            
            save_file = self.get_save_file(slot)
            with open(save_file, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2)
            
            self.show_message(f"游戏已保存到存档位 {slot}！")
            return True
        except Exception as e:
            self.show_message(f"保存失败：{str(e)}")
            return False
    
    def load_game(self, slot: int) -> bool:
        """从指定存档位加载游戏"""
        try:
            save_file = self.get_save_file(slot)
            if not os.path.exists(save_file):
                self.show_message(f"存档位 {slot} 没有存档！")
                return False
            
            with open(save_file, 'r', encoding='utf-8') as f:
                save_data = json.load(f)
            
            # 反序列化玩家数据
            self._deserialize_player(save_data["player"])
            
            # 恢复地图
            self.maps = create_world_maps()
            self.current_map = self.maps[save_data["current_map"]]
            self.player.current_map = save_data["current_map"]
            
            # 恢复游戏时间
            self.game_time = save_data.get("game_time", 0)
            
            # 恢复任务
            self.player.completed_quests = save_data.get("completed_quests", [])
            self.player.active_quests = save_data.get("active_quests", [])
            
# 恢复统计
            stats = save_data.get("stats", {})
            self.player.enemies_defeated = stats.get("enemies_defeated", 0)
            self.player.treasures_found = stats.get("treasures_found", 0)
            self.player.areas_explored = set(stats.get("areas_explored", []))
            
            # Bug #5 fix: 恢复所有探索过的地图迷雾
            for map_name in self.player.areas_explored:
                if map_name in self.maps:
                    for row in self.maps[map_name].explored:
                        for i in range(len(row)):
                            row[i] = True
            
            # 探索当前区域
            self.current_map.explore_area(self.player.x, self.player.y, 4)
            
            # 重置状态
            self.state = GameState.EXPLORE
            self.keys_pressed = {}
            self.move_cooldown = 0
            self.input_cooldown = 0
            
            # 更新摄像机
            self.update_camera()
            
            self.show_message(f"已从存档位 {slot} 加载游戏！")
            return True
        except Exception as e:
            self.show_message(f"加载失败：{str(e)}")
            return False
    
    def _serialize_player(self) -> dict:
        """序列化玩家数据为字典"""
        return {
            "name": self.player.name,
            "level": self.player.level,
            "exp": self.player.exp,
            "exp_to_next": self.player.exp_to_next,
            "hp": self.player.hp,
            "max_hp": self.player.max_hp,
            "mp": self.player.mp,
            "max_mp": self.player.max_mp,
            "attack": self.player.attack,
            "defense": self.player.defense,
            "magic": self.player.magic,
            "speed": self.player.speed,
            "weapon": self.player.weapon.id if self.player.weapon else None,
            "armor": self.player.armor.id if self.player.armor else None,
            "accessory": self.player.accessory.id if self.player.accessory else None,
            "inventory": self.player.inventory,
            "gold": self.player.gold,
            "unlocked_skills": self.player.unlocked_skills,
            "x": self.player.x,
            "y": self.player.y,
            "buffs": self.player.buffs
        }
    
    def _deserialize_player(self, data: dict):
        """从字典反序列化玩家数据"""
        self.player.name = data.get("name", "勇者")
        self.player.level = data.get("level", 1)
        self.player.exp = data.get("exp", 0)
        self.player.exp_to_next = data.get("exp_to_next", 100)
        self.player.hp = data.get("hp", 100)
        self.player.max_hp = data.get("max_hp", 100)
        self.player.mp = data.get("mp", 30)
        self.player.max_mp = data.get("max_mp", 30)
        self.player.attack = data.get("attack", 15)
        self.player.defense = data.get("defense", 10)
        self.player.magic = data.get("magic", 8)
        self.player.speed = data.get("speed", 12)
        
        # 恢复装备
        weapon_id = data.get("weapon")
        if weapon_id and weapon_id in GameDatabase.ITEMS:
            self.player.weapon = GameDatabase.ITEMS[weapon_id]
        
        armor_id = data.get("armor")
        if armor_id and armor_id in GameDatabase.ITEMS:
            self.player.armor = GameDatabase.ITEMS[armor_id]
        
        accessory_id = data.get("accessory")
        if accessory_id and accessory_id in GameDatabase.ITEMS:
            self.player.accessory = GameDatabase.ITEMS[accessory_id]
        
        # 恢复背包
        self.player.inventory = data.get("inventory", {})
        self.player.gold = data.get("gold", 50)
        self.player.unlocked_skills = data.get("unlocked_skills", [])
        
        # 恢复位置
        self.player.x = data.get("x", 15)
        self.player.y = data.get("y", 12)
        self.player.buffs = data.get("buffs", [])
    
    def update_camera(self):
        """更新摄像机位置"""
        target_x = self.player.x * Config.TILE_SIZE - Config.SCREEN_WIDTH // 2
        target_y = self.player.y * Config.TILE_SIZE - Config.SCREEN_HEIGHT // 2
        
        # 平滑移动
        self.camera_x += (target_x - self.camera_x) * 0.1
        self.camera_y += (target_y - self.camera_y) * 0.1
        
        # 边界限制
        max_x = self.current_map.width * Config.TILE_SIZE - Config.SCREEN_WIDTH
        max_y = self.current_map.height * Config.TILE_SIZE - Config.SCREEN_HEIGHT
        self.camera_x = max(0, min(self.camera_x, max_x))
        self.camera_y = max(0, min(self.camera_y, max_y))
    
    def update(self):
        """每帧更新"""
        self.frame_count += 1
        if self.frame_count % 60 == 0:
            self.game_time += 1

        # 更新消息计时器
        if self.message_timer > 0:
            self.message_timer -= 1
        
        # 更新输入防抖
        if self.input_cooldown > 0:
            self.input_cooldown -= 1

        # 更新玩家buff
        if self.state == GameState.EXPLORE or self.state == GameState.BATTLE:
            self.player.update_buffs()

        # 更新摄像机（跟随玩家）
        if self.state == GameState.EXPLORE:
            self.update_camera()

        # 持续移动处理（探索模式）
        if self.state == GameState.EXPLORE:
            if self.move_cooldown > 0:
                self.move_cooldown -= 1
            else:
                dx, dy = 0, 0
                if self.keys_pressed.get('up', False):
                    dy = -1
                elif self.keys_pressed.get('down', False):
                    dy = 1
                elif self.keys_pressed.get('left', False):
                    dx = -1
                elif self.keys_pressed.get('right', False):
                    dx = 1

                if dx != 0 or dy != 0:
                    self.move_player(dx, dy)
                    self.move_cooldown = self.move_delay  # 恢复到正常冷却时间
    
    def handle_explore_input(self, event):
        """处理探索状态输入"""
        if event.type == pygame.KEYDOWN:
            # 优先检查ESC键，可能在其他状态处理前切换状态
            if event.key == pygame.K_ESCAPE:
                self.toggle_menu()
                return
            
            # 状态检查应在处理任何输入之前
            if self.state != GameState.EXPLORE:
                return
            
            # 记录按键状态
            if event.key == pygame.K_UP or event.key == pygame.K_w:
                self.keys_pressed['up'] = True
                self.keys_pressed['down'] = False
                self.keys_pressed['left'] = False
                self.keys_pressed['right'] = False
            elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                self.keys_pressed['down'] = True
                self.keys_pressed['up'] = False
                self.keys_pressed['left'] = False
                self.keys_pressed['right'] = False
            elif event.key == pygame.K_LEFT or event.key == pygame.K_a:
                self.keys_pressed['left'] = True
                self.keys_pressed['up'] = False
                self.keys_pressed['down'] = False
                self.keys_pressed['right'] = False
            elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                self.keys_pressed['right'] = True
                self.keys_pressed['up'] = False
                self.keys_pressed['down'] = False
                self.keys_pressed['left'] = False

            # 记录按键状态，但不立即移动
            # 移动由update()中的持续移动逻辑处理
            # 这样可以避免一次按键走2格的问题

            # 交互
            if event.key == pygame.K_SPACE or event.key == pygame.K_e:
                self.interact()
                return

            # 菜单快捷键
            if event.key == pygame.K_i:
                self.state = GameState.INVENTORY
                self.inventory_menu_index = 0
                self.inventory_page = 0
                return

            if event.key == pygame.K_c:
                self.state = GameState.CHARACTER
                self.character_menu_index = 0
                return

            if event.key == pygame.K_q:
                self.state = GameState.QUEST_LOG
                self.quest_menu_index = 0
                return

            if event.key == pygame.K_b:
                self.state = GameState.BESTIARY
                self.bestiary_tab = 0
                self.bestiary_index = 0
                return
            
            # 存档快捷键
            if event.key == pygame.K_F5:
                # 快速保存到第一个有数据的存档位，或第一个空位
                saved = False
                for i in range(1, self.save_slots + 1):
                    save_file = self.get_save_file(i)
                    if os.path.exists(save_file):
                        if self.save_game(i):
                            saved = True
                            break
                if not saved:
                    # 所有存档位都为空，保存到第一个
                    self.save_game(1)
                return
            
            if event.key == pygame.K_F9:
                # 快速加载第一个有数据的存档位
                loaded = False
                for i in range(1, self.save_slots + 1):
                    save_file = self.get_save_file(i)
                    if os.path.exists(save_file):
                        if self.load_game(i):
                            loaded = True
                            break
                if not loaded:
                    self.show_message("没有找到可用的存档！")
                return
            
            # 打开存档菜单
            if event.key == pygame.K_F2:
                self.state = GameState.SAVE_LOAD
                self.save_menu_index = 0
                self.save_menu_active = True  # True=保存模式, False=加载模式
                return

        elif event.type == pygame.KEYUP:
            # 释放按键
            if event.key == pygame.K_UP or event.key == pygame.K_w:
                self.keys_pressed['up'] = False
            elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                self.keys_pressed['down'] = False
            elif event.key == pygame.K_LEFT or event.key == pygame.K_a:
                self.keys_pressed['left'] = False
            elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                self.keys_pressed['right'] = False
    
    def move_player(self, dx, dy):
        """移动玩家"""
        new_x = self.player.x + dx
        new_y = self.player.y + dy
        
        # 检查边界
        if new_x < 0 or new_x >= self.current_map.width or \
           new_y < 0 or new_y >= self.current_map.height:
            return
        
        # 检查是否可通行
        if not self.current_map.is_walkable(new_x, new_y):
            self.show_message("无法通行！")
            return
        
        # 检查NPC
        for npc in self.current_map.npcs:
            if npc["x"] == new_x and npc["y"] == new_y:
                self.show_message("按空格键对话")
                return
        
        # 检查敌人（随机遇敌）
        enemy_to_remove = None
        for enemy_data in self.current_map.enemies:
            if enemy_data["x"] == new_x and enemy_data["y"] == new_y:
                self.start_battle(enemy_data["id"])
                enemy_to_remove = enemy_data
                break
        if enemy_to_remove:
            self.current_map.enemies.remove(enemy_to_remove)
            return
        
        # 检查宝箱
        for chest in self.current_map.chests:
            if chest["x"] == new_x and chest["y"] == new_y and not chest["opened"]:
                self.open_chest(chest)
                return
        
        # 检查传送门
        for portal in self.current_map.portals:
            if portal["x"] == new_x and portal["y"] == new_y:
                self.use_portal(portal)
                return
        
        # 移动玩家
        self.player.x = new_x
        self.player.y = new_y
        
        # 更新探索区域
        self.current_map.explore_area(self.player.x, self.player.y, 3)
        self.current_map.explore_area(self.player.x, self.player.y, 4)
        
        # 检查区域探索
        self.check_area_exploration()
        
        # 随机遇敌
        self.check_random_encounter()
    
    def check_area_exploration(self):
        """检查是否探索了新区域"""
        map_name = self.player.current_map
        if map_name not in self.player.areas_explored:
            self.player.areas_explored.add(map_name)
            self.show_message(f"发现新区域：{self.current_map.name}！")
            
            # 更新任务进度
            self.update_quest_objective("explore", map_name)
    
    def check_random_encounter(self):
        """随机遇敌"""
        # 战斗后必须移动3步才可能遇敌
        if self.steps_since_encounter >= 0:
            self.steps_since_encounter -= 1
            return
        
        if random.random() < 0.08:  # 8% 遇敌率
            # 战斗后重置计数
            self.steps_since_encounter = 3
            
            # 根据地图选择合适的敌人
            map_name = self.player.current_map
            enemy_pool = []
            
            if map_name == "grassland":
                enemy_pool = ["slime", "goblin", "wolf", "bandit"]
            elif map_name == "desert":
                enemy_pool = ["sand_worm", "desert_scorpion", "tomb_guardian", "sand_mage"]
            elif map_name == "snow_mountain":
                enemy_pool = ["ice_golem", "snow_witch", "yeti"]
            elif map_name == "volcano":
                enemy_pool = ["fire_elemental", "lava_golem", "flame_demon"]
            
            if enemy_pool:
                enemy_id = random.choice(enemy_pool)
                self.start_battle(enemy_id)
    
    def interact(self):
        """与前方实体交互"""
        # 检查四个方向的NPC
        directions = [(0, -1), (0, 1), (-1, 0), (1, 0)]
        for dx, dy in directions:
            check_x = self.player.x + dx
            check_y = self.player.y + dy
            
            for npc in self.current_map.npcs:
                if npc["x"] == check_x and npc["y"] == check_y:
                    self.start_dialogue(npc)
                    return
    
    def start_dialogue(self, npc):
        """开始对话"""
        self.current_npc = npc
        self.dialogue_lines = npc["dialogue"]
        self.dialogue_index = 0
        self.state = GameState.DIALOGUE
        
        # 检查是否是任务给予者
        if "quest_giver" in npc and npc["quest_giver"]:
            quest_id = npc["quest_giver"]
            if quest_id not in self.player.completed_quests and quest_id not in self.player.active_quests:
                self.give_quest(quest_id)
    
    def give_quest(self, quest_id: str):
        """给予任务"""
        all_quests = GameDatabase.MAIN_QUESTS + GameDatabase.SIDE_QUESTS
        for quest in all_quests:
            if quest.id == quest_id:
                quest.is_active = True
                self.player.active_quests.append(quest_id)
                self.show_message(f"获得任务：{quest.name}")
                break
    
    def update_quest_objective(self, target_type: str, target_id: str, amount: int = 1):
        """更新任务目标"""
        for quest_id in self.player.active_quests:
            all_quests = GameDatabase.MAIN_QUESTS + GameDatabase.SIDE_QUESTS
            for quest in all_quests:
                if quest.id == quest_id:
                    for obj in quest.objectives:
                        if obj.target_type == target_type:
                            if target_id == obj.target_id or obj.target_id == "any":
                                if not obj.completed:
                                    obj.current = min(obj.current + amount, obj.required)
                                    if obj.current >= obj.required:
                                        obj.completed = True
                                        self.show_message(f"任务目标完成：{obj.description}")

                                    # 检查是否所有目标都完成
                                    if all(o.completed for o in quest.objectives):
                                        self.complete_quest(quest)
                                    return
    
    def complete_quest(self, quest):
        """完成任务"""
        quest.is_completed = True
        # 安全移除，避免ValueError
        if quest.id in self.player.active_quests:
            self.player.active_quests.remove(quest.id)
        if quest.id not in self.player.completed_quests:
            self.player.completed_quests.append(quest.id)

        # 发放奖励
        if "exp" in quest.rewards:
            self.player.gain_exp(quest.rewards["exp"])
        if "gold" in quest.rewards:
            self.player.gold += quest.rewards["gold"]
        if "items" in quest.rewards:
            for item_id in quest.rewards["items"]:
                self.player.add_item(item_id)

        self.show_message(f"任务完成：{quest.name}！")

        # 检查是否通关
        if quest.id == "main_ch4" and quest.is_completed:
            self.state = GameState.VICTORY
    
    def open_chest(self, chest):
        """打开宝箱"""
        chest["opened"] = True
        self.player.treasures_found += 1

        items_found = []
        for item_id in chest["items"]:
            if item_id.startswith("gold_"):
                gold_amount = int(item_id.split("_")[1])
                self.player.gold += gold_amount
                items_found.append(f"金币 x{gold_amount}")
            else:
                self.player.add_item(item_id)
                item = GameDatabase.ITEMS.get(item_id)
                if item:
                    # 记录物品到图鉴
                    if item_id not in self.player.known_items:
                        self.player.known_items.add(item_id)
                        self.show_message(f"发现新物品: {item.name}!")
                    items_found.append(item.name)

        self.show_message(f"获得：{', '.join(items_found)}！")

        # 更新任务进度
        self.update_quest_objective("collect", "treasure")
    
    def use_portal(self, portal):
        """使用传送门"""
        target_map_name = portal["target_map"]
        if target_map_name in self.maps:
            self.current_map = self.maps[target_map_name]
            self.player.current_map = target_map_name
            self.player.x = portal["target_x"]
            self.player.y = portal["target_y"]

            # 探索新区域
            self.current_map.explore_area(self.player.x, self.player.y, 4)

            # 重置摄像机到新位置
            self.update_camera()

            self.show_message(f"到达：{self.current_map.name}")

            # 更新任务进度 - 使用传送门名称或目标地图名称
            portal_name = portal.get("name", target_map_name)
            self.update_quest_objective("reach", target_map_name)
            self.update_quest_objective("reach", portal_name)
    
    def start_battle(self, enemy_id: str):
        """开始战斗"""
        if enemy_id in GameDatabase.ENEMIES:
            enemy_template = GameDatabase.ENEMIES[enemy_id]
            # 创建敌人实例
            self.battle_enemy = Enemy(
                id=enemy_template.id,
                name=enemy_template.name,
                level=enemy_template.level,
                hp=enemy_template.hp,
                max_hp=enemy_template.max_hp,
                mp=enemy_template.mp,
                max_mp=enemy_template.max_mp,
                attack=enemy_template.attack,
                defense=enemy_template.defense,
                magic=enemy_template.magic,
                speed=enemy_template.speed,
                exp_reward=enemy_template.exp_reward,
                gold_reward=enemy_template.gold_reward,
                drops=enemy_template.drops.copy(),
                skills=enemy_template.skills.copy(),
            )

            # 加载敌人精灵数据
            if enemy_template.sprite_data is None:
                from src.data_loader import PixelArt
                enemy_sprites = PixelArt.load_sprites()
                enemy_template.sprite_data = enemy_sprites.get('enemy')

            self.battle_log = [f"遭遇了 {self.battle_enemy.name}！"]
            self.battle_turn = "player" if self.player.get_total_speed() >= self.battle_enemy.speed else "enemy"
            self.battle_menu_index = 0
            self.battle_selecting_skill = False
            self.battle_selecting_item = False
            self.player_turn_done = False
            self.is_arena_battle = False  # 重置竞技场标志
            self.battle_ended = False  # 重置战斗结束标记

            self.state = GameState.BATTLE

            # 如果是敌人先手
            if self.battle_turn == "enemy":
                pygame.time.set_timer(pygame.USEREVENT + 1, 1000)
    
    def handle_battle_input(self, event):
        """处理战斗状态输入"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                # 尝试逃跑
                if random.random() < 0.5:
                    self.battle_log.append("成功逃跑！")
                    # 清理战斗状态
                    self.state = GameState.EXPLORE
                    self.battle_enemy = None
                    self.battle_log = []
                    self.battle_turn = "player"
                    self.battle_menu_index = 0
                    self.battle_submenu_index = 0
                    self.battle_selecting_skill = False
                    self.battle_selecting_item = False
                    self.is_arena_battle = False
                    self.battle_ended = False  # 重置战斗结束标记
                    # 清除所有按键状态
                    self.keys_pressed = {
                        'up': False,
                        'down': False,
                        'left': False,
                        'right': False
                    }
                    self.move_cooldown = 0
                else:
                    self.battle_log.append("逃跑失败！")
                    self.end_player_turn()
                return

            if self.battle_turn != "player":
                return

            if self.battle_selecting_skill:
                self.handle_skill_selection(event)
            elif self.battle_selecting_item:
                self.handle_item_selection(event)
            else:
                self.handle_battle_menu(event)
    
    def handle_battle_menu(self, event):
        """处理战斗菜单"""
        menu_options = ["攻击", "技能", "道具", "防御"]
        
        if event.key == pygame.K_UP:
            self.battle_menu_index = (self.battle_menu_index - 1) % len(menu_options)
        elif event.key == pygame.K_DOWN:
            self.battle_menu_index = (self.battle_menu_index + 1) % len(menu_options)
        elif event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
            if self.battle_menu_index == 0:  # 攻击
                self.player_attack()
            elif self.battle_menu_index == 1:  # 技能
                self.battle_selecting_skill = True
                self.battle_submenu_index = 0
            elif self.battle_menu_index == 2:  # 道具
                self.battle_selecting_item = True
                self.battle_submenu_index = 0
            elif self.battle_menu_index == 3:  # 防御
                self.player_defend()
    
    def handle_skill_selection(self, event):
        """处理技能选择"""
        skills = [GameDatabase.SKILLS[sid] for sid in self.player.unlocked_skills]
        
        if len(skills) == 0:
            self.battle_log.append("没有已解锁的技能！")
            self.battle_selecting_skill = False
            return

        if event.key == pygame.K_ESCAPE or event.key == pygame.K_LEFT:
            self.battle_selecting_skill = False
            return

        if event.key == pygame.K_UP:
            self.battle_submenu_index = (self.battle_submenu_index - 1) % len(skills)
        elif event.key == pygame.K_DOWN:
            self.battle_submenu_index = (self.battle_submenu_index + 1) % len(skills)
        elif event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
            skill = skills[self.battle_submenu_index]
            
            if self.player.mp < skill.mana_cost:
                self.battle_log.append("MP不足！")
                return
            
            self.player.mp -= skill.mana_cost
            
            if skill.skill_type == SkillType.PHYSICAL or skill.skill_type == SkillType.MAGIC:
                # 攻击技能
                total_damage = skill.damage
                if skill.skill_type == SkillType.PHYSICAL:
                    total_damage += self.player.get_total_attack()
                    total_damage -= self.battle_enemy.defense // 2
                else:
                    total_damage += self.player.get_total_magic()
                    total_damage -= self.battle_enemy.defense // 3
                
                total_damage = max(1, total_damage + random.randint(-5, 5))
                self.battle_enemy.hp -= total_damage
                self.battle_log.append(f"使用 {skill.name}！造成 {total_damage} 点伤害！")
                
            elif skill.skill_type == SkillType.HEAL:
                # 治疗技能
                heal_amount = skill.heal_amount + self.player.get_total_magic() // 2
                self.player.hp = min(self.player.max_hp, self.player.hp + heal_amount)
                self.battle_log.append(f"使用 {skill.name}！恢复了 {heal_amount} 点HP！")
            
            elif skill.skill_type == SkillType.BUFF:
                # 增益技能
                self.player.buffs.append({
                    "stat": skill.buff_stat,
                    "amount": skill.buff_amount,
                    "duration": skill.buff_duration
                })
                self.battle_log.append(f"使用 {skill.name}！{skill.buff_stat}提升了 {skill.buff_amount}！")
            
            elif skill.skill_type == SkillType.DEBUFF:
                # 减益技能
                self.battle_enemy.attack = max(1, self.battle_enemy.attack - 10)
                self.battle_log.append(f"使用 {skill.name}！敌人的攻击力降低了！")
            
            self.battle_selecting_skill = False
            self.check_battle_status()
    
    def handle_item_selection(self, event):
        """处理道具选择"""
        consumables = []
        for item_id, qty in self.player.inventory.items():
            if item_id in GameDatabase.ITEMS:
                item = GameDatabase.ITEMS[item_id]
                if item.item_type == ItemType.CONSUMABLE:
                    consumables.append((item, qty))
        
        if len(consumables) == 0:
            self.battle_log.append("没有可用的道具！")
            self.battle_selecting_item = False
            return
        
        if event.key == pygame.K_ESCAPE or event.key == pygame.K_LEFT:
            self.battle_selecting_item = False
            return

        if event.key == pygame.K_UP:
            self.battle_submenu_index = (self.battle_submenu_index - 1) % len(consumables)
        elif event.key == pygame.K_DOWN:
            self.battle_submenu_index = (self.battle_submenu_index + 1) % len(consumables)
        elif event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
            item, qty = consumables[self.battle_submenu_index]

            if item.heal_amount > 0:
                old_hp = self.player.hp
                self.player.hp = min(self.player.max_hp, self.player.hp + item.heal_amount)
                actual_heal = self.player.hp - old_hp
                self.battle_log.append(f"使用 {item.name}！恢复了 {actual_heal} 点HP！")

            if item.mana_amount > 0:
                old_mp = self.player.mp
                self.player.mp = min(self.player.max_mp, self.player.mp + item.mana_amount)
                actual_mana = self.player.mp - old_mp
                self.battle_log.append(f"使用 {item.name}！恢复了 {actual_mana} 点MP！")

            self.player.remove_item(item.id)
            self.battle_selecting_item = False
            self.check_battle_status()
    
    def player_attack(self):
        """玩家普通攻击"""
        damage = max(1, self.player.get_total_attack() - self.battle_enemy.defense // 2 + random.randint(-3, 3))
        self.battle_enemy.hp -= damage
        self.battle_log.append(f"造成 {damage} 点伤害！")
        self.check_battle_status()
    
    def player_defend(self):
        """玩家防御"""
        # 移除旧的同名buff，避免叠加
        self.player.buffs = [b for b in self.player.buffs if b["stat"] != "defense"]
        self.player.buffs.append({
            "stat": "defense",
            "amount": self.player.get_total_defense() // 2,
            "duration": 1
        })
        self.battle_log.append("采取防御姿态！")
        self.end_player_turn()
    
    def check_battle_status(self):
        """检查战斗状态"""
        if self.battle_enemy.hp <= 0:
            self.battle_enemy.hp = 0
            # 防止重复调用
            if self.battle_ended:
                return
            self.battle_ended = True
            self.win_battle()
        else:
            self.end_player_turn()
    
    def end_player_turn(self):
        """结束玩家回合"""
        self.player_turn_done = True
        self.battle_turn = "enemy"
        # 1秒后敌人行动
        pygame.time.set_timer(pygame.USEREVENT + 1, 1000)
    
    def enemy_turn(self):
        """敌人回合"""
        if not self.battle_enemy:
            return
        if self.battle_enemy.hp <= 0:
            return
        
        # 敌人攻击
        damage = max(1, self.battle_enemy.attack - self.player.get_total_defense() // 2 + random.randint(-3, 3))
        self.player.hp -= damage
        self.battle_log.append(f"{self.battle_enemy.name} 造成了 {damage} 点伤害！")
        
        if self.player.hp <= 0:
            self.player.hp = 0
            self.state = GameState.GAME_OVER
        else:
            # 回到玩家回合
            self.battle_turn = "player"
            self.player_turn_done = False
            pygame.time.set_timer(pygame.USEREVENT + 1, 0)
    
    def toggle_menu(self):
        """切换菜单"""
        if self.state == GameState.EXPLORE:
            # 显示小型菜单
            self.show_message("按 I: 背包 | C: 角色 | Q: 任务日志")
        else:
            self.state = GameState.EXPLORE
    
    def handle_dialogue_input(self, event):
        """处理对话状态输入"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
                self.dialogue_index += 1

                if self.dialogue_index >= len(self.dialogue_lines):
                    # 对话结束
                    self.state = GameState.EXPLORE
                    # 清除所有按键状态，防止返回探索后持续移动
                    self.keys_pressed = {
                        'up': False,
                        'down': False,
                        'left': False,
                        'right': False
                    }
                    self.move_cooldown = 0

                    # 检查商店
                    if self.current_npc and self.current_npc.get("is_shop"):
                        self.open_shop(self.current_npc)
                    elif self.current_npc and self.current_npc.get("is_arena"):
                        self.start_arena_battle()

                    self.current_npc = None
    
    def open_shop(self, npc):
        """打开商店"""
        self.current_shop = npc
        self.shop_menu_index = 0
        self.shop_buy_mode = True
        self.state = GameState.SHOP
    
    def start_arena_battle(self):
        """开始竞技场战斗"""
        arena_enemies = ["bandit", "tomb_guardian", "frost_dragon", "flame_demon"]
        enemy_id = random.choice(arena_enemies)
        self.start_battle(enemy_id)
        
        # 标记当前是竞技场战斗，避免monkey patch叠加
        self.is_arena_battle = True

    def win_battle(self):
        """战斗胜利"""
        self.player.enemies_defeated += 1

        exp_gained = self.battle_enemy.exp_reward
        gold_gained = self.battle_enemy.gold_reward

        self.player.gain_exp(exp_gained)
        self.player.gold += gold_gained

        self.battle_log.append(f"战斗胜利！")
        self.battle_log.append(f"获得 {exp_gained} 经验值，{gold_gained} 金币！")

        # 掉落物品
        for drop_id in self.battle_enemy.drops:
            if random.random() < 0.3:  # 30% 掉落率
                self.player.add_item(drop_id)
                item = GameDatabase.ITEMS.get(drop_id)
                if item:
                    self.battle_log.append(f"获得 {item.name}！")

        # 更新任务进度 - 如果是竞技场战斗，更新竞技场任务
        if hasattr(self, 'is_arena_battle') and self.is_arena_battle:
            self.update_quest_objective("kill", "arena_enemy")
            self.is_arena_battle = False
        
        self.update_quest_objective("kill", self.battle_enemy.id)
        self.update_quest_objective("kill", "any")

        # 重置遇敌冷却计数
        self.steps_since_encounter = 3

        # 2秒后返回探索
        pygame.time.set_timer(pygame.USEREVENT + 2, 2000)
    
    def handle_shop_input(self, event):
        """处理商店输入"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.state = GameState.EXPLORE
                # 清除所有按键状态，防止返回探索后持续移动
                self.keys_pressed = {
                    'up': False,
                    'down': False,
                    'left': False,
                    'right': False
                }
                self.move_cooldown = 0
                return
            
            shop_items = self.current_shop.get("shop_items", [])
            if len(shop_items) == 0:
                return

            if event.key == pygame.K_TAB:
                self.shop_buy_mode = not self.shop_buy_mode
                self.shop_menu_index = 0
                return

            if event.key == pygame.K_UP:
                self.shop_menu_index = (self.shop_menu_index - 1) % len(shop_items)
            elif event.key == pygame.K_DOWN:
                self.shop_menu_index = (self.shop_menu_index + 1) % len(shop_items)
            elif event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
                if shop_items and self.shop_menu_index < len(shop_items):
                    item_id = shop_items[self.shop_menu_index]
                    item = GameDatabase.ITEMS.get(item_id)

                    if item:
                        if self.shop_buy_mode:
                            if self.player.gold >= item.price:
                                self.player.gold -= item.price
                                self.player.add_item(item_id)
                                self.show_message(f"购买了 {item.name}！")
                            else:
                                self.show_message("金币不足！")
                        else:
                            # 卖出（半价）
                            # 检查是否是可卖出的类型（不能卖出任务物品）
                            if item.item_type == ItemType.QUEST:
                                self.show_message("任务物品无法出售！")
                            elif self.player.has_item(item_id):
                                sell_price = item.price // 2
                                self.player.gold += sell_price
                                self.player.remove_item(item_id)
                                self.show_message(f"卖出了 {item.name}，获得 {sell_price} 金币！")
                            else:
                                self.show_message("没有该物品可出售！")
                else:
                    self.show_message("没有可交易的物品")
    
    def handle_inventory_input(self, event):
        """处理背包输入"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.state = GameState.EXPLORE
                # 清除所有按键状态，防止返回探索后持续移动
                self.keys_pressed = {
                    'up': False,
                    'down': False,
                    'left': False,
                    'right': False
                }
                self.move_cooldown = 0
                return

            items = list(self.player.inventory.items())
            if len(items) == 0:
                return

            if event.key == pygame.K_UP:
                self.inventory_menu_index = (self.inventory_menu_index - 1) % len(items)
            elif event.key == pygame.K_DOWN:
                self.inventory_menu_index = (self.inventory_menu_index + 1) % len(items)
            elif event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
                if self.inventory_menu_index < len(items):
                    item_id, qty = items[self.inventory_menu_index]
                    item = GameDatabase.ITEMS.get(item_id)

                    if item:
                        if item.item_type == ItemType.CONSUMABLE:
                            self.player.use_item(item_id)
                            self.show_message(f"使用了 {item.name}")
                        elif item.item_type in (ItemType.WEAPON, ItemType.ARMOR, ItemType.ACCESSORY):
                            if self.player.equip_item(item_id):
                                self.show_message(f"装备了 {item.name}")
    
    def handle_character_input(self, event):
        """处理角色状态输入"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.state = GameState.EXPLORE
                # 清除所有按键状态，防止返回探索后持续移动
                self.keys_pressed = {
                    'up': False,
                    'down': False,
                    'left': False,
                    'right': False
                }
                self.move_cooldown = 0

    def handle_quest_log_input(self, event):
        """处理任务日志输入"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.state = GameState.EXPLORE
                # 清除所有按键状态，防止返回探索后持续移动
                self.keys_pressed = {
                    'up': False,
                    'down': False,
                    'left': False,
                    'right': False
                }
                self.move_cooldown = 0
                return

            active_quests = self.player.active_quests
            if len(active_quests) == 0:
                return

            if event.key == pygame.K_UP:
                self.quest_menu_index = (self.quest_menu_index - 1) % len(active_quests)
            elif event.key == pygame.K_DOWN:
                self.quest_menu_index = (self.quest_menu_index + 1) % len(active_quests)
    
    def handle_save_load_input(self, event):
        """处理存档/加载界面输入"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.state = GameState.EXPLORE
                self.keys_pressed = {
                    'up': False,
                    'down': False,
                    'left': False,
                    'right': False
                }
                self.move_cooldown = 0
                return
            
            # TAB键切换保存/加载模式
            if event.key == pygame.K_TAB:
                self.save_menu_active = not self.save_menu_active
                self.save_menu_index = 0
                return
            
            # 上下选择存档位
            if event.key == pygame.K_UP:
                self.save_menu_index = (self.save_menu_index - 1) % self.save_slots
            elif event.key == pygame.K_DOWN:
                self.save_menu_index = (self.save_menu_index + 1) % self.save_slots
            
            # 确认操作
            elif event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
                slot = self.save_menu_index + 1
                if self.save_menu_active:
                    # 保存模式
                    self.save_game(slot)
                else:
                    # 加载模式
                    self.load_game(slot)
    
    def handle_title_input(self, event):
        """处理标题画面输入"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.title_menu_index = (self.title_menu_index - 1) % 2
            elif event.key == pygame.K_DOWN:
                self.title_menu_index = (self.title_menu_index + 1) % 2
            elif event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
                if self.title_menu_index == 0:
                    self.state = GameState.EXPLORE
                else:
                    self.running = False
    
    def handle_input(self):
        """处理所有输入"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            # 特殊事件处理
            if event.type == pygame.USEREVENT + 1:
                pygame.time.set_timer(pygame.USEREVENT + 1, 0)
                if self.state == GameState.BATTLE and self.battle_turn == "enemy" and not self.battle_ended:
                    self.enemy_turn()
            
            if event.type == pygame.USEREVENT + 2:
                pygame.time.set_timer(pygame.USEREVENT + 2, 0)
                if self.state == GameState.BATTLE:
                    self.state = GameState.EXPLORE
                    # 清理战斗状态
                    self.battle_enemy = None
                    self.battle_log = []
                    self.battle_turn = "player"
                    self.battle_menu_index = 0
                    self.battle_submenu_index = 0
                    self.battle_selecting_skill = False
                    self.battle_selecting_item = False
                    self.player_turn_done = False
                    self.battle_ended = False
                    self.is_arena_battle = False
                    # 清除按键状态，防止切换状态后自动移动
                    self.keys_pressed = {
                        'up': False,
                        'down': False,
                        'left': False,
                        'right': False
                    }
                    self.move_cooldown = 0
            
            if self.state == GameState.TITLE:
                self.handle_title_input(event)
            elif self.state == GameState.EXPLORE:
                self.handle_explore_input(event)
            elif self.state == GameState.DIALOGUE:
                self.handle_dialogue_input(event)
            elif self.state == GameState.BATTLE:
                self.handle_battle_input(event)
            elif self.state == GameState.INVENTORY:
                self.handle_inventory_input(event)
            elif self.state == GameState.SHOP:
                self.handle_shop_input(event)
            elif self.state == GameState.CHARACTER:
                self.handle_character_input(event)
            elif self.state == GameState.QUEST_LOG:
                self.handle_quest_log_input(event)
            elif self.state == GameState.SAVE_LOAD:
                self.handle_save_load_input(event)
            elif self.state == GameState.BESTIARY:
                self.handle_bestiary_input(event)
            elif self.state in (GameState.GAME_OVER, GameState.VICTORY):
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
                        if self.state == GameState.GAME_OVER:
                            # 重新开始 - 重置游戏数据而非重新初始化pygame
                            self.reset_game()
                        else:
                            self.running = False
    
    def draw_title_screen(self):
        """绘制标题画面"""
        self.screen.fill(Config.COLORS['dark_blue'])
        
        # 标题
        self.renderer.draw_text("幻境传说：迷失大陆", Config.SCREEN_WIDTH // 2, 150, 
                               Config.COLORS['gold'], self.renderer.font_title, center=True)
        self.renderer.draw_text("A Fantasy Tale: The Lost Continent", Config.SCREEN_WIDTH // 2, 200,
                               Config.COLORS['cyan'], self.renderer.font_medium, center=True)
        
        # 装饰线
        pygame.draw.line(self.screen, Config.COLORS['gold'], 
                        (Config.SCREEN_WIDTH // 2 - 200, 230),
                        (Config.SCREEN_WIDTH // 2 + 200, 230), 3)
        
        # 菜单选项
        options = ["开始冒险", "退出游戏"]
        for i, option in enumerate(options):
            color = Config.COLORS['gold'] if i == self.title_menu_index else Config.COLORS['white']
            self.renderer.draw_text(option, Config.SCREEN_WIDTH // 2, 300 + i * 60,
                                   color, self.renderer.font_large, center=True)
        
        # 操作说明
        instructions = [
            "操作说明：",
            "WASD/方向键 - 移动",
            "空格/E - 交互/确认",
            "I - 背包 | C - 角色 | Q - 任务",
            "ESC - 菜单"
        ]
        for i, line in enumerate(instructions):
            self.renderer.draw_text(line, Config.SCREEN_WIDTH // 2, 500 + i * 30,
                                   Config.COLORS['light_gray'], self.renderer.font_small, center=True)
    
    def draw_explore_screen(self):
        """绘制探索画面"""
        # 绘制地图
        self.renderer.draw_map(self.current_map, self.camera_x, self.camera_y)
        
        # 绘制传送门
        for portal in self.current_map.portals:
            if self.current_map.explored[int(portal["y"])][int(portal["x"])]:
                self.renderer.draw_entity('portal', portal["x"], portal["y"], 
                                         self.camera_x, self.camera_y)
        
        # 绘制宝箱
        for chest in self.current_map.chests:
            if not chest["opened"] and self.current_map.explored[int(chest["y"])][int(chest["x"])]:
                self.renderer.draw_entity('chest', chest["x"], chest["y"],
                                         self.camera_x, self.camera_y)
        
        # 绘制NPC
        for npc in self.current_map.npcs:
            if self.current_map.explored[int(npc["y"])][int(npc["x"])]:
                self.renderer.draw_entity('npc', npc["x"], npc["y"],
                                         self.camera_x, self.camera_y)
        
        # 绘制敌人
        for enemy in self.current_map.enemies:
            if self.current_map.explored[int(enemy["y"])][int(enemy["x"])]:
                self.renderer.draw_entity('enemy', enemy["x"], enemy["y"],
                                         self.camera_x, self.camera_y)
        
        # 绘制玩家
        if self.current_map.explored[int(self.player.y)][int(self.player.x)]:
            self.renderer.draw_entity('player', self.player.x, self.player.y,
                                 self.camera_x, self.camera_y)
        
        # 绘制HUD
        self.draw_hud()
        
        # 绘制消息
        if self.message_timer > 0:
            self.renderer.draw_text_box([self.message])
    
    def draw_hud(self):
        """绘制HUD"""
        # 顶部状态栏
        hud_bg = pygame.Surface((Config.SCREEN_WIDTH, 50), pygame.SRCALPHA)
        hud_bg.fill((0, 0, 0, 150))
        self.screen.blit(hud_bg, (0, 0))
        
        # 角色信息
        self.renderer.draw_text(f"{self.player.name} Lv.{self.player.level}", 10, 5, Config.COLORS['gold'])
        
        # HP条
        self.renderer.draw_bar(10, 25, 150, 15, self.player.hp, self.player.max_hp, Config.COLORS['red'])
        self.renderer.draw_text(f"HP {self.player.hp}/{self.player.max_hp}", 10, 27, Config.COLORS['white'], self.renderer.font_small)
        
        # MP条
        self.renderer.draw_bar(170, 25, 120, 15, self.player.mp, self.player.max_mp, Config.COLORS['blue'])
        self.renderer.draw_text(f"MP {self.player.mp}/{self.player.max_mp}", 170, 27, Config.COLORS['white'], self.renderer.font_small)
        
        # 金币
        self.renderer.draw_text(f"G {self.player.gold}", 310, 10, Config.COLORS['gold'])
        
        # 地图名称
        self.renderer.draw_text(f"@ {self.current_map.name}", Config.SCREEN_WIDTH - 200, 10, 
                               Config.COLORS['cyan'])
        
        # 当前位置
        self.renderer.draw_text(f"({self.player.x}, {self.player.y})", Config.SCREEN_WIDTH - 200, 30,
                               Config.COLORS['light_gray'], self.renderer.font_small)
    
    def draw_dialogue_screen(self):
        """绘制对话画面"""
        # 保持探索画面作为背景
        self.draw_explore_screen()
        
        # 绘制对话框
        if self.dialogue_index < len(self.dialogue_lines):
            lines = [self.dialogue_lines[self.dialogue_index]]
            self.renderer.draw_text_box(lines, title=self.current_npc["name"])
            self.renderer.draw_text("按空格继续...", Config.SCREEN_WIDTH // 2, Config.SCREEN_HEIGHT - 35,
                                   Config.COLORS['light_gray'], self.renderer.font_small, center=True)
    
    def draw_battle_screen(self):
        """绘制战斗画面"""
        # 战斗背景
        self.screen.fill(Config.COLORS['dark_gray'])
        
        # 绘制敌人
        if self.battle_enemy:
            enemy_x = Config.SCREEN_WIDTH // 2
            enemy_y = 150
            # 正确绘制敌人在中央
            sprite = self.renderer.sprites.get('enemy')
            if sprite:
                self.screen.blit(sprite, (enemy_x - sprite.get_width() // 2, enemy_y))

            # 敌人信息
            self.renderer.draw_text(f"{self.battle_enemy.name} Lv.{self.battle_enemy.level}",
                                   enemy_x, enemy_y + 60, Config.COLORS['red'], self.renderer.font_large, center=True)

            # 敌人HP条
            self.renderer.draw_bar(enemy_x - 100, enemy_y + 80, 200, 20,
                                  self.battle_enemy.hp, self.battle_enemy.max_hp, Config.COLORS['red'])
            self.renderer.draw_text(f"HP {self.battle_enemy.hp}/{self.battle_enemy.max_hp}",
                                   enemy_x, enemy_y + 82, Config.COLORS['white'], self.renderer.font_small, center=True)
        
        # 分割线
        pygame.draw.line(self.screen, Config.COLORS['gold'], (50, 320), (Config.SCREEN_WIDTH - 50, 320), 2)
        
        # 玩家信息
        self.renderer.draw_text(f"{self.player.name} Lv.{self.player.level}", 80, 350, Config.COLORS['gold'])
        self.renderer.draw_bar(80, 375, 200, 20, self.player.hp, self.player.max_hp, Config.COLORS['red'])
        self.renderer.draw_text(f"HP {self.player.hp}/{self.player.max_hp}", 85, 377, Config.COLORS['white'], self.renderer.font_small)
        self.renderer.draw_bar(80, 400, 200, 20, self.player.mp, self.player.max_mp, Config.COLORS['blue'])
        self.renderer.draw_text(f"MP {self.player.mp}/{self.player.max_mp}", 85, 402, Config.COLORS['white'], self.renderer.font_small)
        
        # 战斗菜单
        if self.battle_turn == "player" and not self.battle_selecting_skill and not self.battle_selecting_item:
            menu_options = ["攻击", "技能", "道具", "防御"]
            for i, option in enumerate(menu_options):
                color = Config.COLORS['gold'] if i == self.battle_menu_index else Config.COLORS['white']
                marker = "▶ " if i == self.battle_menu_index else "  "
                self.renderer.draw_text(f"{marker}{option}", 650, 350 + i * 35, color)
        
        # 技能选择
        elif self.battle_selecting_skill:
            skills = [GameDatabase.SKILLS[sid] for sid in self.player.unlocked_skills]
            self.renderer.draw_text("选择技能 (ESC返回):", 600, 350, Config.COLORS['gold'])
            for i, skill in enumerate(skills):
                color = Config.COLORS['gold'] if i == self.battle_submenu_index else Config.COLORS['white']
                marker = "▶ " if i == self.battle_submenu_index else "  "
                self.renderer.draw_text(f"{marker}{skill.name} (MP {skill.mana_cost})", 600, 380 + i * 30, color)

            # 显示选中技能的详细信息
            if skills and self.battle_submenu_index < len(skills):
                skill = skills[self.battle_submenu_index]
                detail_y = 380 + len(skills) * 30 + 20
                self.renderer.draw_text(f"类型: {skill.skill_type.value}", 600, detail_y, Config.COLORS['cyan'], self.renderer.font_small)
                self.renderer.draw_text(f"效果: {skill.description}", 600, detail_y + 25, Config.COLORS['light_gray'], self.renderer.font_small)
        
        # 道具选择
        elif self.battle_selecting_item:
            consumables = [(GameDatabase.ITEMS[iid], qty) for iid, qty in self.player.inventory.items()
                          if iid in GameDatabase.ITEMS and GameDatabase.ITEMS[iid].item_type == ItemType.CONSUMABLE]
            self.renderer.draw_text("选择道具 (ESC返回):", 600, 350, Config.COLORS['gold'])
            if consumables:
                for i, (item, qty) in enumerate(consumables):
                    color = Config.COLORS['gold'] if i == self.battle_submenu_index else Config.COLORS['white']
                    marker = "▶ " if i == self.battle_submenu_index else "  "
                    self.renderer.draw_text(f"{marker}{item.name} x{qty}", 600, 380 + i * 30, color)

                # 显示选中道具的详细信息
                if consumables and self.battle_submenu_index < len(consumables):
                    item, qty = consumables[self.battle_submenu_index]
                    detail_y = 380 + len(consumables) * 30 + 20
                    if item.heal_amount > 0:
                        self.renderer.draw_text(f"回复HP: +{item.heal_amount}", 600, detail_y, Config.COLORS['green'], self.renderer.font_small)
                    if item.mana_amount > 0:
                        self.renderer.draw_text(f"回复MP: +{item.mana_amount}", 600, detail_y + 25, Config.COLORS['blue'], self.renderer.font_small)
                    self.renderer.draw_text(f"描述: {item.description}", 600, detail_y + 50, Config.COLORS['light_gray'], self.renderer.font_small)
            else:
                self.renderer.draw_text("没有可用道具", 600, 380, Config.COLORS['gray'])
        
        # 战斗日志
        log_y = 450
        log_lines = self.battle_log[-4:]  # 显示最后4条
        for line in log_lines:
            self.renderer.draw_text(line, 50, log_y, Config.COLORS['white'], self.renderer.font_small)
            log_y += 25
        
        # 回合指示
        turn_text = "你的回合" if self.battle_turn == "player" else "敌人回合"
        turn_color = Config.COLORS['green'] if self.battle_turn == "player" else Config.COLORS['red']
        self.renderer.draw_text(turn_text, Config.SCREEN_WIDTH // 2, 550, turn_color, self.renderer.font_large, center=True)
    
    def draw_shop_screen(self):
        """绘制商店画面"""
        self.renderer.draw_menu_background()
        
        shop_name = self.current_shop.get("name", "商店") if self.current_shop else "商店"
        mode_text = "购买" if self.shop_buy_mode else "卖出"
        
        # 标题
        self.renderer.draw_text(f"{shop_name} - {mode_text}", Config.SCREEN_WIDTH // 2, 40, Config.COLORS['gold'], 
                               self.renderer.font_title, center=True)
        
        # 玩家金币
        self.renderer.draw_text(f"拥有金币: {self.player.gold}", Config.SCREEN_WIDTH - 150, 40, Config.COLORS['gold'])
        
        # 物品列表
        shop_items = self.current_shop.get("shop_items", []) if self.current_shop else []
        
        if len(shop_items) == 0:
            self.renderer.draw_text("商店没有物品出售", Config.SCREEN_WIDTH // 2, 200,
                                  Config.COLORS['gray'], self.renderer.font_large, center=True)
        else:
            self.renderer.draw_text("商品列表", 50, 80, Config.COLORS['cyan'])
            
            for i, item_id in enumerate(shop_items):
                if item_id in GameDatabase.ITEMS:
                    item = GameDatabase.ITEMS[item_id]
                    color = Config.COLORS['gold'] if i == self.shop_menu_index else Config.COLORS['white']
                    marker = "▶ " if i == self.shop_menu_index else "  "
                    
                    if self.shop_buy_mode:
                        price_color = Config.COLORS['green'] if self.player.gold >= item.price else Config.COLORS['red']
                        self.renderer.draw_text(f"{marker}{item.icon} {item.name} - {item.price}G", 70, 100 + i * 30, color)
                        self.renderer.draw_text(f"     {item.description}", 70, 100 + i * 30 + 18, Config.COLORS['light_gray'], self.renderer.font_small)
                    else:
                        player_qty = self.player.inventory.get(item_id, 0)
                        qty_color = Config.COLORS['green'] if player_qty > 0 else Config.COLORS['red']
                        sell_price = item.price // 2
                        self.renderer.draw_text(f"{marker}{item.icon} {item.name} x{player_qty}", 70, 100 + i * 30, color)
                        self.renderer.draw_text(f"     卖出价: {sell_price}G", 70, 100 + i * 30 + 18, qty_color, self.renderer.font_small)
        
        # 操作提示
        self.renderer.draw_text("空格: 交易 | TAB: 切换买卖模式 | ESC: 离开", Config.SCREEN_WIDTH // 2, Config.SCREEN_HEIGHT - 40,
                               Config.COLORS['light_gray'], self.renderer.font_small, center=True)
    
    def draw_inventory_screen(self):
        """绘制背包画面"""
        self.renderer.draw_menu_background()
        
        # 标题
        self.renderer.draw_text("背 包", Config.SCREEN_WIDTH // 2, 40, Config.COLORS['gold'], 
                               self.renderer.font_title, center=True)
        
        # 装备栏
        self.renderer.draw_text("装备栏", 50, 80, Config.COLORS['cyan'])
        equip_y = 100
        
        # 武器
        weapon_name = self.player.weapon.name if self.player.weapon else "无"
        self.renderer.draw_text(f"武器: {weapon_name}", 70, equip_y, Config.COLORS['white'])
        # 护甲
        armor_name = self.player.armor.name if self.player.armor else "无"
        self.renderer.draw_text(f"护甲: {armor_name}", 70, equip_y + 25, Config.COLORS['white'])
        # 饰品
        acc_name = self.player.accessory.name if self.player.accessory else "无"
        self.renderer.draw_text(f"饰品: {acc_name}", 70, equip_y + 50, Config.COLORS['white'])
        
        # 物品列表
        self.renderer.draw_text("物品", 50, 180, Config.COLORS['cyan'])
        
        items = list(self.player.inventory.items())
        for i, (item_id, qty) in enumerate(items):
            if item_id in GameDatabase.ITEMS:
                item = GameDatabase.ITEMS[item_id]
                color = Config.COLORS['gold'] if i == self.inventory_menu_index else Config.COLORS['white']
                marker = "▶ " if i == self.inventory_menu_index else "  "
                self.renderer.draw_text(f"{marker}{item.icon} {item.name} x{qty}", 70, 200 + i * 30, color)
        
        # 操作提示
        self.renderer.draw_text("空格: 使用/装备 | ESC: 返回", Config.SCREEN_WIDTH // 2, Config.SCREEN_HEIGHT - 40,
                               Config.COLORS['light_gray'], self.renderer.font_small, center=True)
    
    def draw_character_screen(self):
        """绘制角色画面"""
        self.renderer.draw_menu_background()
        
        # 标题
        self.renderer.draw_text("角色状态", Config.SCREEN_WIDTH // 2, 40, Config.COLORS['gold'],
                               self.renderer.font_title, center=True)
        
        # 角色信息
        info_y = 100
        info_x = 100
        
        self.renderer.draw_text(f"名称: {self.player.name}", info_x, info_y, Config.COLORS['white'])
        self.renderer.draw_text(f"等级: {self.player.level}", info_x, info_y + 35, Config.COLORS['white'])
        self.renderer.draw_text(f"经验: {self.player.exp}/{self.player.exp_to_next}", info_x, info_y + 70, Config.COLORS['white'])
        
        # 属性
        self.renderer.draw_text("基础属性", info_x, info_y + 120, Config.COLORS['cyan'])
        self.renderer.draw_text(f"  HP: {self.player.hp}/{self.player.max_hp}", info_x, info_y + 150, Config.COLORS['white'])
        self.renderer.draw_text(f"  MP: {self.player.mp}/{self.player.max_mp}", info_x, info_y + 175, Config.COLORS['white'])
        self.renderer.draw_text(f"  攻击力: {self.player.get_total_attack()}", info_x, info_y + 200, Config.COLORS['white'])
        self.renderer.draw_text(f"  防御力: {self.player.get_total_defense()}", info_x, info_y + 225, Config.COLORS['white'])
        self.renderer.draw_text(f"  魔力: {self.player.get_total_magic()}", info_x, info_y + 250, Config.COLORS['white'])
        self.renderer.draw_text(f"  速度: {self.player.get_total_speed()}", info_x, info_y + 275, Config.COLORS['white'])
        
        # 技能
        self.renderer.draw_text("已解锁技能", info_x + 400, info_y, Config.COLORS['cyan'])
        for i, skill_id in enumerate(self.player.unlocked_skills):
            if skill_id in GameDatabase.SKILLS:
                skill = GameDatabase.SKILLS[skill_id]
                self.renderer.draw_text(f"  {skill.name} - {skill.description}", info_x + 400, info_y + 30 + i * 30, 
                                       Config.COLORS['white'], self.renderer.font_small)
        
        # 统计
        self.renderer.draw_text("游戏统计", info_x + 400, info_y + 200, Config.COLORS['cyan'])
        self.renderer.draw_text(f"  击败敌人: {self.player.enemies_defeated}", info_x + 400, info_y + 230, Config.COLORS['white'])
        self.renderer.draw_text(f"  发现宝箱: {self.player.treasures_found}", info_x + 400, info_y + 255, Config.COLORS['white'])
        self.renderer.draw_text(f"  探索区域: {len(self.player.areas_explored)}/{len(self.maps)}", info_x + 400, info_y + 280, Config.COLORS['white'])
        self.renderer.draw_text(f"  游戏时间: {self.game_time // 60}分{self.game_time % 60}秒", info_x + 400, info_y + 305, Config.COLORS['white'])
        
        self.renderer.draw_text("ESC: 返回", Config.SCREEN_WIDTH // 2, Config.SCREEN_HEIGHT - 40,
                               Config.COLORS['light_gray'], self.renderer.font_small, center=True)
    
    def draw_quest_log_screen(self):
        """绘制任务日志画面"""
        self.renderer.draw_menu_background()

        # 标题
        self.renderer.draw_text("任务日志", Config.SCREEN_WIDTH // 2, 40, Config.COLORS['gold'],
                               self.renderer.font_title, center=True)

        if not self.player.active_quests:
            self.renderer.draw_text("当前没有进行中的任务", Config.SCREEN_WIDTH // 2, 200,
                                   Config.COLORS['gray'], self.renderer.font_large, center=True)
        else:
            for i, quest_id in enumerate(self.player.active_quests):
                all_quests = GameDatabase.MAIN_QUESTS + GameDatabase.SIDE_QUESTS
                quest = next((q for q in all_quests if q.id == quest_id), None)

                if quest:
                    y = 100 + i * 180
                    color = Config.COLORS['gold'] if i == self.quest_menu_index else Config.COLORS['white']

                    quest_type_text = "[主线]" if quest.quest_type == "main" else "[支线]"
                    self.renderer.draw_text(f"{quest_type_text} {quest.name}", 80, y, color)
                    self.renderer.draw_text(quest.description, 100, y + 30, Config.COLORS['light_gray'],
                                           self.renderer.font_small)

                    # 目标
                    for j, obj in enumerate(quest.objectives):
                        status = "✓" if obj.completed else "○"
                        self.renderer.draw_text(f"  {status} {obj.description} ({obj.current}/{obj.required})",
                                               100, y + 60 + j * 25, Config.COLORS['white'], self.renderer.font_small)

        self.renderer.draw_text("ESC: 返回", Config.SCREEN_WIDTH // 2, Config.SCREEN_HEIGHT - 40,
                               Config.COLORS['light_gray'], self.renderer.font_small, center=True)
    
    def draw_save_load_screen(self):
        """绘制存档/加载界面"""
        self.renderer.draw_menu_background()
        
        # 标题
        mode_text = "保存游戏" if self.save_menu_active else "加载游戏"
        self.renderer.draw_text(mode_text, Config.SCREEN_WIDTH // 2, 40, Config.COLORS['gold'],
                               self.renderer.font_title, center=True)
        
        # 存档位列表
        for i in range(self.save_slots):
            slot = i + 1
            y = 120 + i * 180
            save_file = self.get_save_file(slot)
            
            # 判断是否有存档
            has_save = os.path.exists(save_file)
            
            # 背景框
            box_rect = pygame.Rect(100, y - 20, Config.SCREEN_WIDTH - 200, 150)
            if i == self.save_menu_index:
                pygame.draw.rect(self.screen, Config.COLORS['gold'], box_rect, 3)
                pygame.draw.rect(self.screen, (*Config.COLORS['gold'][:3], 30), box_rect)
            else:
                pygame.draw.rect(self.screen, Config.COLORS['gray'], box_rect, 2)
            
            if has_save:
                # 读取存档信息
                try:
                    with open(save_file, 'r', encoding='utf-8') as f:
                        save_data = json.load(f)
                    
                    player_data = save_data['player']
                    level = player_data['level']
                    map_name = save_data['current_map']
                    game_time = save_data.get('game_time', 0)
                    time_str = f"{game_time // 60}分{game_time % 60}秒"
                    
                    # 存档信息
                    self.renderer.draw_text(f"存档位 {slot}", 120, y, Config.COLORS['gold'],
                                           self.renderer.font_large)
                    self.renderer.draw_text(f"等级: {level}", 120, y + 35, Config.COLORS['white'])
                    self.renderer.draw_text(f"地图: {map_name}", 120, y + 70, Config.COLORS['white'])
                    self.renderer.draw_text(f"游戏时间: {time_str}", 120, y + 105, Config.COLORS['white'])
                    
                    action_color = Config.COLORS['green'] if self.save_menu_active else Config.COLORS['cyan']
                    action_text = "按空格覆盖保存" if self.save_menu_active else "按空格加载"
                    self.renderer.draw_text(action_text, Config.SCREEN_WIDTH - 300, y + 50,
                                           action_color, self.renderer.font_medium)
                except Exception as e:
                    self.renderer.draw_text(f"存档位 {slot}", 120, y, Config.COLORS['red'],
                                           self.renderer.font_large)
                    self.renderer.draw_text(f"损坏: {str(e)[:20]}", 120, y + 35, Config.COLORS['gray'])
            else:
                # 空存档位
                self.renderer.draw_text(f"存档位 {slot}", 120, y, Config.COLORS['gray'],
                                       self.renderer.font_large)
                self.renderer.draw_text("空存档", 120, y + 35, Config.COLORS['gray'],
                                       self.renderer.font_medium)
                
                if self.save_menu_active:
                    self.renderer.draw_text("按空格保存到此位置", Config.SCREEN_WIDTH - 350, y + 50,
                                           Config.COLORS['green'], self.renderer.font_medium)
        
        # 操作说明
        self.renderer.draw_text("TAB: 切换保存/加载模式  |  ↑↓: 选择存档位  |  空格/回车: 确认  |  ESC: 返回",
                               Config.SCREEN_WIDTH // 2, Config.SCREEN_HEIGHT - 40,
                               Config.COLORS['light_gray'], self.renderer.font_small, center=True)

    def handle_bestiary_input(self, event):
        """处理图鉴界面输入"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.state = GameState.EXPLORE
                return

            if event.key == pygame.K_TAB:
                self.bestiary_tab = (self.bestiary_tab + 1) % 3
                self.bestiary_index = 0
                return

            if event.key == pygame.K_UP:
                max_index = self._get_bestiary_count()
                if max_index > 0:
                    self.bestiary_index = (self.bestiary_index - 1) % max_index
            elif event.key == pygame.K_DOWN:
                max_index = self._get_bestiary_count()
                if max_index > 0:
                    self.bestiary_index = (self.bestiary_index + 1) % max_index

    def _get_bestiary_count(self):
        """获取当前图鉴标签的条目数量"""
        if self.bestiary_tab == 0:
            return len(self.player.known_enemies)
        elif self.bestiary_tab == 1:
            return len(self.player.known_items)
        else:
            return len(self.player.unlocked_skills)

    def draw_bestiary_screen(self):
        """绘制图鉴界面"""
        self.renderer.draw_menu_background()

        # 标题
        self.renderer.draw_text("图 鉴", Config.SCREEN_WIDTH // 2, 40, Config.COLORS['gold'],
                               self.renderer.font_title, center=True)

        # 页签
        tabs = ["敌人", "物品", "技能"]
        tab_colors = [Config.COLORS['gold'] if i == self.bestiary_tab else Config.COLORS['gray'] for i in range(3)]
        for i, tab in enumerate(tabs):
            self.renderer.draw_text(f"[{tab}]", 150 + i * 100, 80, tab_colors[i])

        # 显示内容
        content_x = 80
        content_y = 120

        if self.bestiary_tab == 0:
            # 敌人图鉴
            if not self.player.known_enemies:
                self.renderer.draw_text("尚未发现任何敌人", Config.SCREEN_WIDTH // 2, 200,
                                       Config.COLORS['gray'], self.renderer.font_large, center=True)
            else:
                known_list = list(self.player.known_enemies)
                for i, enemy_id in enumerate(known_list):
                    if enemy_id in GameDatabase.ENEMIES:
                        enemy = GameDatabase.ENEMIES[enemy_id]
                        color = Config.COLORS['gold'] if i == self.bestiary_index else Config.COLORS['white']
                        marker = "▶ " if i == self.bestiary_index else "  "
                        self.renderer.draw_text(f"{marker}{enemy.icon} {enemy.name} Lv.{enemy.level}",
                                               content_x, content_y + i * 35, color)

                        if i == self.bestiary_index:
                            detail_y = content_y + len(known_list) * 35 + 30
                            self.renderer.draw_text(f"HP: {enemy.hp}  MP: {enemy.mp}", content_x, detail_y, Config.COLORS['cyan'], self.renderer.font_small)
                            self.renderer.draw_text(f"攻击: {enemy.attack}  防御: {enemy.defense}  魔力: {enemy.magic}", content_x, detail_y + 25, Config.COLORS['cyan'], self.renderer.font_small)
                            self.renderer.draw_text(f"经验奖励: {enemy.exp_reward}  金币奖励: {enemy.gold_reward}", content_x, detail_y + 50, Config.COLORS['cyan'], self.renderer.font_small)
                            self.renderer.draw_text(f"掉落: {', '.join(enemy.drops) if enemy.drops else '无'}", content_x, detail_y + 75, Config.COLORS['light_gray'], self.renderer.font_small)

        elif self.bestiary_tab == 1:
            # 物品图鉴
            if not self.player.known_items:
                self.renderer.draw_text("尚未发现任何物品", Config.SCREEN_WIDTH // 2, 200,
                                       Config.COLORS['gray'], self.renderer.font_large, center=True)
            else:
                known_list = list(self.player.known_items)
                for i, item_id in enumerate(known_list):
                    if item_id in GameDatabase.ITEMS:
                        item = GameDatabase.ITEMS[item_id]
                        color = Config.COLORS['gold'] if i == self.bestiary_index else Config.COLORS['white']
                        marker = "▶ " if i == self.bestiary_index else "  "
                        self.renderer.draw_text(f"{marker}{item.icon} {item.name} ({item.item_type.value})",
                                               content_x, content_y + i * 35, color)

                        if i == self.bestiary_index:
                            detail_y = content_y + len(known_list) * 35 + 30
                            props = []
                            if item.attack: props.append(f"攻击+{item.attack}")
                            if item.defense: props.append(f"防御+{item.defense}")
                            if item.magic: props.append(f"魔力+{item.magic}")
                            if item.heal_amount: props.append(f"回复HP+{item.heal_amount}")
                            if item.mana_amount: props.append(f"回复MP+{item.mana_amount}")
                            if item.price: props.append(f"售价: {item.price}")
                            prop_text = " | ".join(props) if props else "无特殊属性"
                            self.renderer.draw_text(prop_text, content_x, detail_y, Config.COLORS['cyan'], self.renderer.font_small)
                            self.renderer.draw_text(f"描述: {item.description}", content_x, detail_y + 30, Config.COLORS['light_gray'], self.renderer.font_small)

        else:
            # 技能图鉴
            if not self.player.unlocked_skills:
                self.renderer.draw_text("尚未解锁任何技能", Config.SCREEN_WIDTH // 2, 200,
                                       Config.COLORS['gray'], self.renderer.font_large, center=True)
            else:
                for i, skill_id in enumerate(self.player.unlocked_skills):
                    if skill_id in GameDatabase.SKILLS:
                        skill = GameDatabase.SKILLS[skill_id]
                        color = Config.COLORS['gold'] if i == self.bestiary_index else Config.COLORS['white']
                        marker = "▶ " if i == self.bestiary_index else "  "
                        self.renderer.draw_text(f"{marker}{skill.name} (MP {skill.mana_cost})",
                                               content_x, content_y + i * 35, color)

                        if i == self.bestiary_index:
                            detail_y = content_y + len(self.player.unlocked_skills) * 35 + 30
                            self.renderer.draw_text(f"类型: {skill.skill_type.value}", content_x, detail_y, Config.COLORS['cyan'], self.renderer.font_small)
                            self.renderer.draw_text(f"效果: {skill.description}", content_x, detail_y + 25, Config.COLORS['light_gray'], self.renderer.font_small)

        # 操作说明
        self.renderer.draw_text("TAB: 切换分类  |  ↑↓: 选择  |  ESC: 返回",
                               Config.SCREEN_WIDTH // 2, Config.SCREEN_HEIGHT - 40,
                               Config.COLORS['light_gray'], self.renderer.font_small, center=True)
    
    def draw_game_over_screen(self):
        """绘制游戏结束画面"""
        self.screen.fill((0, 0, 0))
        
        self.renderer.draw_text("游 戏 结 束", Config.SCREEN_WIDTH // 2, 200, Config.COLORS['red'],
                               self.renderer.font_title, center=True)
        self.renderer.draw_text("你被打败了...", Config.SCREEN_WIDTH // 2, 280, Config.COLORS['gray'],
                               self.renderer.font_large, center=True)
        self.renderer.draw_text("按空格键重新开始", Config.SCREEN_WIDTH // 2, 400, Config.COLORS['white'],
                               self.renderer.font_medium, center=True)
    
    def draw_victory_screen(self):
        """绘制胜利画面"""
        self.screen.fill((20, 20, 60))
        
        # 烟花效果
        for _ in range(20):
            x = random.randint(100, Config.SCREEN_WIDTH - 100)
            y = random.randint(100, 400)
            color = random.choice([Config.COLORS['red'], Config.COLORS['gold'], Config.COLORS['cyan'],
                                  Config.COLORS['green'], Config.COLORS['pink']])
            pygame.draw.circle(self.screen, color, (x, y), random.randint(2, 5))
        
        self.renderer.draw_text("恭 喜 通 关 ！", Config.SCREEN_WIDTH // 2, 150, Config.COLORS['gold'],
                               self.renderer.font_title, center=True)
        self.renderer.draw_text("你成功击败了魔王，拯救了世界！", Config.SCREEN_WIDTH // 2, 230,
                               Config.COLORS['white'], self.renderer.font_large, center=True)
        
        # 统计信息
        self.renderer.draw_text(f"游戏时间: {self.game_time // 60}分{self.game_time % 60}秒",
                               Config.SCREEN_WIDTH // 2, 320, Config.COLORS['cyan'], center=True)
        self.renderer.draw_text(f"最终等级: {self.player.level}", Config.SCREEN_WIDTH // 2, 360,
                               Config.COLORS['cyan'], center=True)
        self.renderer.draw_text(f"击败敌人: {self.player.enemies_defeated}", Config.SCREEN_WIDTH // 2, 400,
                               Config.COLORS['cyan'], center=True)
        self.renderer.draw_text(f"完成任务: {len(self.player.completed_quests)}", Config.SCREEN_WIDTH // 2, 440,
                               Config.COLORS['cyan'], center=True)
        
        self.renderer.draw_text("按空格键退出", Config.SCREEN_WIDTH // 2, 550, Config.COLORS['white'],
                               self.renderer.font_medium, center=True)
    
    def draw(self):
        """绘制当前帧"""
        if self.state == GameState.TITLE:
            self.draw_title_screen()
        elif self.state == GameState.EXPLORE:
            self.draw_explore_screen()
        elif self.state == GameState.DIALOGUE:
            self.draw_dialogue_screen()
        elif self.state == GameState.BATTLE:
            self.draw_battle_screen()
        elif self.state == GameState.INVENTORY:
            self.draw_inventory_screen()
        elif self.state == GameState.SHOP:
            self.draw_shop_screen()
        elif self.state == GameState.CHARACTER:
            self.draw_character_screen()
        elif self.state == GameState.QUEST_LOG:
            self.draw_quest_log_screen()
        elif self.state == GameState.SAVE_LOAD:
            self.draw_save_load_screen()
        elif self.state == GameState.BESTIARY:
            self.draw_bestiary_screen()
        elif self.state == GameState.GAME_OVER:
            self.draw_game_over_screen()
        elif self.state == GameState.VICTORY:
            self.draw_victory_screen()
        
        pygame.display.flip()
    
    def run(self):
        """运行游戏主循环"""
        while self.running:
            self.handle_input()
            self.update()
            self.draw()
            self.clock.tick(Config.FPS)
        
        pygame.quit()
        sys.exit()


# ============================================================================
# 主程序入口
# ============================================================================
if __name__ == "__main__":
    print("正在启动 幻境传说：迷失大陆...")
    print("游戏加载中，请稍候...")
    
    game = Game()
    game.run()



