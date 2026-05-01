#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据模型和游戏数据库
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from src.constants import ItemType, SkillType, SPRITE_ENEMY


@dataclass
class Item:
    id: str
    name: str
    description: str
    item_type: ItemType
    icon: str
    price: int = 0
    # 装备属性
    attack: int = 0
    defense: int = 0
    magic: int = 0
    speed: int = 0
    # 消耗品效果
    heal_amount: int = 0
    mana_amount: int = 0

    def __post_init__(self):
        if isinstance(self.item_type, str):
            self.item_type = ItemType(self.item_type)


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
    # 增益/减益效果
    buff_stat: str = ""
    buff_amount: int = 0
    buff_duration: int = 0

    def __post_init__(self):
        if isinstance(self.skill_type, str):
            self.skill_type = SkillType(self.skill_type)


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
    sprite_data: list = field(default_factory=lambda: SPRITE_ENEMY)


@dataclass
class QuestObjective:
    description: str
    target_type: str  # "kill", "collect", "talk", "explore", "reach"
    target_id: str = ""
    current: int = 0
    required: int = 1
    completed: bool = False


@dataclass
class Quest:
    id: str
    name: str
    description: str
    quest_type: str  # "main" 或 "side"
    chapter: int = 0  # 主线章节，支线为0
    objectives: List[QuestObjective] = field(default_factory=list)
    rewards: Dict = field(default_factory=dict)  # {"exp": 100, "gold": 50, "items": []}
    is_completed: bool = False
    is_active: bool = False
    giver_npc: str = ""


# ============================================================================
# 游戏数据库
# ============================================================================
class GameDatabase:
    """游戏数据管理器"""

    ITEMS = {
        # 武器
        "wooden_sword": Item("wooden_sword", "木剑", "训练用的木制短剑", ItemType.WEAPON, "🗡️", 20, attack=5),
        "iron_sword": Item("iron_sword", "铁剑", "坚固的铁制长剑", ItemType.WEAPON, "⚔️", 100, attack=12),
        "steel_blade": Item("steel_blade", "钢刃剑", "精炼钢打造的利剑", ItemType.WEAPON, "⚔️", 300, attack=22),
        "magic_staff": Item("magic_staff", "魔法杖", "蕴含魔力的法杖", ItemType.WEAPON, "🔮", 250, magic=25),
        "legendary_sword": Item("legendary_sword", "传说之剑", "传说中的勇者之剑", ItemType.WEAPON, "👑", 1000, attack=50, magic=20),
        "shadow_dagger": Item("shadow_dagger", "暗影匕首", "暗影铸成的匕首", ItemType.WEAPON, "🗡️", 400, attack=28, speed=15),

        # 护甲
        "cloth_armor": Item("cloth_armor", "布甲", "基本的布制护甲", ItemType.ARMOR, "👕", 30, defense=5),
        "leather_armor": Item("leather_armor", "皮甲", "轻便的皮革护甲", ItemType.ARMOR, "🦺", 120, defense=12),
        "chain_mail": Item("chain_mail", "锁子甲", "铁环编织的护甲", ItemType.ARMOR, "🛡️", 350, defense=22),
        "plate_armor": Item("plate_armor", "板甲", "重型钢板护甲", ItemType.ARMOR, "🛡️", 800, defense=38),
        "magic_robe": Item("magic_robe", "魔法长袍", "增强魔力的长袍", ItemType.ARMOR, "👘", 400, defense=10, magic=20),

        # 饰品
        "power_ring": Item("power_ring", "力量戒指", "增强攻击力的戒指", ItemType.ACCESSORY, "💍", 200, attack=8),
        "shield_amulet": Item("shield_amulet", "守护护符", "提升防御力的护符", ItemType.ACCESSORY, "📿", 200, defense=8),
        "speed_boots": Item("speed_boots", "疾风之靴", "提升速度的靴子", ItemType.ACCESSORY, "👢", 250, speed=15),
        "wisdom_crown": Item("wisdom_crown", "智慧王冠", "提升魔法的王冠", ItemType.ACCESSORY, "👑", 350, magic=18),
        "lucky_charm": Item("lucky_charm", "幸运护身符", "提升运气的护身符", ItemType.ACCESSORY, "🍀", 500, attack=5, defense=5, magic=5, speed=5),

        # 消耗品
        "health_potion": Item("health_potion", "生命药水", "恢复50点HP", ItemType.CONSUMABLE, "❤️", 30, heal_amount=50),
        "greater_health_potion": Item("greater_health_potion", "高级生命药水", "恢复150点HP", ItemType.CONSUMABLE, "❤️", 80, heal_amount=150),
        "mana_potion": Item("mana_potion", "魔力药水", "恢复30点MP", ItemType.CONSUMABLE, "💙", 40, mana_amount=30),
        "greater_mana_potion": Item("greater_mana_potion", "高级魔力药水", "恢复100点MP", ItemType.CONSUMABLE, "💙", 100, mana_amount=100),
        "elixir": Item("elixir", "灵药", "完全恢复HP和MP", ItemType.CONSUMABLE, "✨", 500, heal_amount=999, mana_amount=999),
        "antidote": Item("antidote", "解毒剂", "解除异常状态", ItemType.CONSUMABLE, "💚", 20),

        # 任务物品
        "ancient_key": Item("ancient_key", "远古钥匙", "打开远古遗迹的神秘钥匙", ItemType.QUEST, "🗝️"),
        "crystal_shard": Item("crystal_shard", "水晶碎片", "散发着微光的水晶碎片", ItemType.QUEST, "💎"),
        "elder_scroll": Item("elder_scroll", "长老卷轴", "记载着远古知识的卷轴", ItemType.QUEST, "📜"),
        "dragon_scale": Item("dragon_scale", "龙鳞", "传说中的龙之鳞片", ItemType.QUEST, "🐉"),
    }

    SKILLS = {
        # 物理技能
        "slash": Skill("slash", "斩击", "基本的物理攻击", SkillType.PHYSICAL, damage=15, mana_cost=0, unlock_level=1),
        "power_strike": Skill("power_strike", "猛击", "强力的物理攻击", SkillType.PHYSICAL, damage=35, mana_cost=10, unlock_level=3),
        "double_attack": Skill("double_attack", "二连击", "连续两次攻击", SkillType.PHYSICAL, damage=25, mana_cost=15, unlock_level=6),
        "whirlwind": Skill("whirlwind", "旋风斩", "范围物理攻击", SkillType.PHYSICAL, damage=50, mana_cost=25, unlock_level=10),
        "critical_hit": Skill("critical_hit", "暴击", "造成2.5倍伤害", SkillType.PHYSICAL, damage=80, mana_cost=35, unlock_level=15),

        # 魔法技能
        "fireball": Skill("fireball", "火球术", "发射火球攻击敌人", SkillType.MAGIC, damage=25, mana_cost=12, unlock_level=4),
        "ice_shard": Skill("ice_shard", "冰锥术", "用冰锥攻击并减速", SkillType.MAGIC, damage=30, mana_cost=15, unlock_level=7),
        "lightning": Skill("lightning", "闪电链", "释放闪电链攻击", SkillType.MAGIC, damage=55, mana_cost=28, unlock_level=11),
        "meteor": Skill("meteor", "陨石术", "召唤陨石攻击", SkillType.MAGIC, damage=90, mana_cost=45, unlock_level=16),

        # 治疗技能
        "heal": Skill("heal", "治疗术", "恢复HP", SkillType.HEAL, heal_amount=40, mana_cost=10, unlock_level=2),
        "greater_heal": Skill("greater_heal", "强效治疗", "大量恢复HP", SkillType.HEAL, heal_amount=120, mana_cost=25, unlock_level=9),
        "full_heal": Skill("full_heal", "完全恢复", "完全恢复HP", SkillType.HEAL, heal_amount=999, mana_cost=60, unlock_level=18),

        # 增益技能
        "attack_up": Skill("attack_up", "攻击强化", "3回合内提升攻击力", SkillType.BUFF, mana_cost=20, unlock_level=5, buff_stat="attack", buff_amount=15, buff_duration=3),
        "defense_up": Skill("defense_up", "防御强化", "3回合内提升防御力", SkillType.BUFF, mana_cost=20, unlock_level=8, buff_stat="defense", buff_amount=15, buff_duration=3),

        # 减益技能
        "weakness": Skill("weakness", "虚弱诅咒", "3回合内降低敌人攻击力", SkillType.DEBUFF, mana_cost=18, unlock_level=12),
    }

    ENEMIES = {
        # 草原区域 (等级 1-5)
        "slime": Enemy("slime", "史莱姆", 1, 30, 30, 5, 5, 8, 3, 2, 3, 15, 10, ["health_potion"]),
        "goblin": Enemy("goblin", "哥布林", 2, 45, 45, 10, 10, 12, 6, 5, 5, 25, 18, ["health_potion", "wooden_sword"]),
        "wolf": Enemy("wolf", "野狼", 3, 60, 60, 15, 15, 15, 8, 8, 8, 35, 25, ["health_potion", "leather_armor"]),
        "bandit": Enemy("bandit", "强盗", 4, 80, 80, 20, 20, 18, 10, 10, 10, 50, 35, ["iron_sword", "health_potion"]),
        "forest_spirit": Enemy("forest_spirit", "森林精灵", 5, 100, 100, 30, 30, 20, 12, 15, 12, 65, 45, ["mana_potion", "magic_staff"]),

        # 沙漠区域 (等级 6-10)
        "sand_worm": Enemy("sand_worm", "沙虫", 6, 130, 130, 25, 25, 25, 15, 18, 15, 80, 55, ["health_potion", "greater_health_potion"]),
        "desert_scorpion": Enemy("desert_scorpion", "沙漠蝎子", 7, 150, 150, 30, 30, 28, 18, 20, 18, 95, 65, ["antidote", "chain_mail"]),
        "tomb_guardian": Enemy("tomb_guardian", "墓穴守卫", 8, 180, 180, 35, 35, 32, 22, 25, 20, 115, 80, ["steel_blade", "greater_health_potion"]),
        "sand_mage": Enemy("sand_mage", "沙漠法师", 9, 160, 160, 60, 60, 28, 15, 35, 22, 130, 90, ["mana_potion", "magic_robe"]),
        "ancient_mummy": Enemy("ancient_mummy", "远古木乃伊", 10, 250, 250, 40, 40, 35, 28, 28, 25, 160, 120, ["elder_scroll", "greater_health_potion"]),

        # 雪山区域 (等级 11-15)
        "ice_golem": Enemy("ice_golem", "冰霜傀儡", 11, 280, 280, 50, 50, 40, 35, 30, 28, 180, 140, ["greater_health_potion", "plate_armor"]),
        "snow_witch": Enemy("snow_witch", "冰雪女巫", 12, 250, 250, 80, 80, 35, 25, 45, 30, 200, 160, ["greater_mana_potion", "wisdom_crown"]),
        "frost_dragon": Enemy("frost_dragon", "冰霜龙", 13, 350, 350, 70, 70, 50, 38, 40, 35, 250, 200, ["dragon_scale", "elixir"]),
        "yeti": Enemy("yeti", "雪怪", 14, 320, 320, 60, 60, 55, 40, 35, 32, 230, 180, ["greater_health_potion", "power_ring"]),
        "avalanche_spirit": Enemy("avalanche_spirit", "雪崩精灵", 15, 400, 400, 80, 80, 48, 42, 42, 40, 300, 250, ["elixir", "speed_boots"]),

        # 火山区域 (等级 16-20)
        "fire_elemental": Enemy("fire_elemental", "火元素", 16, 380, 380, 100, 100, 55, 35, 50, 42, 350, 280, ["greater_health_potion", "greater_mana_potion"]),
        "lava_golem": Enemy("lava_golem", "熔岩傀儡", 17, 450, 450, 80, 80, 65, 50, 40, 45, 400, 320, ["plate_armor", "elixir"]),
        "flame_demon": Enemy("flame_demon", "烈焰恶魔", 18, 420, 420, 120, 120, 70, 40, 55, 48, 450, 360, ["lucky_charm", "elixir"]),
        "inferno_wyrm": Enemy("inferno_wyrm", "地狱飞龙", 19, 500, 500, 140, 140, 75, 45, 60, 50, 500, 420, ["legendary_sword", "elixir"]),
        "demon_lord": Enemy("demon_lord", "魔王", 20, 800, 800, 200, 200, 90, 55, 70, 60, 1000, 1000, ["legendary_sword", "elixir"]),
    }

    TILE_COLORS = {}

    # 主线任务
    MAIN_QUESTS = [
        Quest(
            id="main_ch1", name="觉醒的勇者", description="你从睡梦中醒来，发现自己身处一个陌生的村庄。长老告诉你，你是被选中的勇者，需要去寻找失落的水晶碎片来拯救这个濒临毁灭的世界。",
            quest_type="main", chapter=1,
            objectives=[
                QuestObjective("与村长对话", "talk", "village_elder", required=1),
                QuestObjective("探索草原区域", "explore", "grassland", required=1),
                QuestObjective("击败3只怪物", "kill", "any", required=3),
                QuestObjective("到达沙漠入口", "reach", "desert_entrance", required=1),
            ],
            rewards={"exp": 200, "gold": 100, "items": ["iron_sword", "cloth_armor"]},
            giver_npc="village_elder"
        ),
        Quest(
            id="main_ch2", name="沙漠的秘密", description="在沙漠深处的远古遗迹中，隐藏着着一块水晶碎片。穿越危险的沙漠，击败守卫的怪物，获取水晶碎片。",
            quest_type="main", chapter=2,
            objectives=[
                QuestObjective("穿越沙漠", "explore", "desert", required=1),
                QuestObjective("击败远古木乃伊", "kill", "ancient_mummy", required=1),
                QuestObjective("获得水晶碎片", "collect", "crystal_shard", required=1),
                QuestObjective("到达雪山脚下", "reach", "snow_mountain", required=1),
            ],
            rewards={"exp": 500, "gold": 300, "items": ["chain_mail", "steel_blade"]},
            giver_npc="desert_sage"
        ),
        Quest(
            id="main_ch3", name="冰雪的试炼", description="雪山之巅隐藏着第二块水晶碎片，但那里被冰雪女巫和她的仆从们守护着。你必须通过冰雪的试炼。",
            quest_type="main", chapter=3,
            objectives=[
                QuestObjective("攀登雪山", "explore", "snow_mountain", required=1),
                QuestObjective("击败冰霜龙", "kill", "frost_dragon", required=1),
                QuestObjective("获得远古钥匙", "collect", "ancient_key", required=1),
                QuestObjective("到达火山入口", "reach", "volcano_entrance", required=1),
            ],
            rewards={"exp": 800, "gold": 500, "items": ["magic_robe", "magic_staff"]},
            giver_npc="snow_hermit"
        ),
        Quest(
            id="main_ch4", name="最终决战", description="魔王在火山深处的城堡中等待着最终决战。收集所有力量，击败魔王，拯救世界！",
            quest_type="main", chapter=4,
            objectives=[
                QuestObjective("穿越火山", "explore", "volcano", required=1),
                QuestObjective("击败地狱飞龙", "kill", "inferno_wyrm", required=1),
                QuestObjective("获得龙鳞", "collect", "dragon_scale", required=1),
                QuestObjective("击败魔王", "kill", "demon_lord", required=1),
            ],
            rewards={"exp": 2000, "gold": 1000, "items": ["legendary_sword", "elixir"]},
            giver_npc="volcano_guide"
        ),
    ]

    # 支线任务
    SIDE_QUESTS = [
        Quest(
            id="side_herbs", name="采集药草", description="村庄的药师需要一些药草来制作药水。",
            quest_type="side", chapter=0,
            objectives=[
                QuestObjective("采集5份药草", "collect", "herb", required=5),
            ],
            rewards={"exp": 50, "gold": 30, "items": ["health_potion", "health_potion", "health_potion"]},
            giver_npc="village_alchemist"
        ),
        Quest(
            id="side_wolf_hunt", name="狼群威胁", description="村庄附近的狼群越来越猖獗，需要有人去解决这个威胁。",
            quest_type="side", chapter=0,
            objectives=[
                QuestObjective("击败5只野狼", "kill", "wolf", required=5),
            ],
            rewards={"exp": 100, "gold": 60, "items": ["leather_armor"]},
            giver_npc="village_hunter"
        ),
        Quest(
            id="side_treasure", name="宝藏猎人", description="据说草原上隐藏着一些宝箱，找到它们！",
            quest_type="side", chapter=0,
            objectives=[
                QuestObjective("找到3个宝箱", "collect", "treasure", required=3),
            ],
            rewards={"exp": 150, "gold": 200, "items": ["power_ring", "shield_amulet"]},
            giver_npc="treasure_map_npc"
        ),
        Quest(
            id="side_sand_ruins", name="沙漠遗迹", description="沙漠深处有一座远古遗迹，探索它并获得宝藏。",
            quest_type="side", chapter=0,
            objectives=[
                QuestObjective("探索沙漠遗迹", "explore", "desert_ruins", required=1),
                QuestObjective("击败墓穴守卫", "kill", "tomb_guardian", required=2),
            ],
            rewards={"exp": 300, "gold": 250, "items": ["steel_blade", "greater_health_potion"]},
            giver_npc="desert_trader"
        ),
        Quest(
            id="side_snow_herbs", name="雪山灵药", description="雪山上生长着稀有的灵药，为长老采集一些回来。",
            quest_type="side", chapter=0,
            objectives=[
                QuestObjective("采集3份雪山灵药", "collect", "snow_herb", required=3),
            ],
            rewards={"exp": 200, "gold": 150, "items": ["elixir", "greater_mana_potion"]},
            giver_npc="village_elder"
        ),
        Quest(
            id="side_dragon_slayer", name="屠龙勇士", description="击败雪山上的冰霜龙，成为真正的屠龙勇士！",
            quest_type="side", chapter=0,
            objectives=[
                QuestObjective("击败冰霜龙", "kill", "frost_dragon", required=1),
            ],
            rewards={"exp": 500, "gold": 400, "items": ["wisdom_crown", "lucky_charm"]},
            giver_npc="dragon_slayer_guild"
        ),
        Quest(
            id="side_volcano_explore", name="火山探险", description="火山深处据说有珍贵的材料，去收集一些吧。",
            quest_type="side", chapter=0,
            objectives=[
                QuestObjective("探索火山深处", "explore", "volcano_deep", required=1),
                QuestObjective("击败3只火元素", "kill", "fire_elemental", required=3),
            ],
            rewards={"exp": 600, "gold": 500, "items": ["plate_armor", "greater_health_potion"]},
            giver_npc="volcano_miner"
        ),
        Quest(
            id="side_bandit_camp", name="清剿强盗", description="草原上有一个强盗营地，去摧毁它！",
            quest_type="side", chapter=0,
            objectives=[
                QuestObjective("击败强盗", "kill", "bandit", required=5),
            ],
            rewards={"exp": 120, "gold": 100, "items": ["iron_sword", "greater_health_potion"]},
            giver_npc="village_guard"
        ),
        Quest(
            id="side_magic_study", name="魔法研究", description="帮助法师研究怪物的魔法抗性。",
            quest_type="side", chapter=0,
            objectives=[
                QuestObjective("击败10只任意怪物", "kill", "any", required=10),
            ],
            rewards={"exp": 250, "gold": 200, "items": ["magic_staff", "greater_mana_potion"]},
            giver_npc="village_mage"
        ),
        Quest(
            id="side_arena", name="竞技场挑战", description="在竞技场中证明自己的实力！",
            quest_type="side", chapter=0,
            objectives=[
                QuestObjective("在竞技场获胜3次", "kill", "arena_enemy", required=3),
            ],
            rewards={"exp": 400, "gold": 350, "items": ["legendary_sword", "elixir"]},
            giver_npc="arena_master"
        ),
    ]


# 初始化TILE_COLORS（需要导入Config）
def init_tile_colors(Config):
    from src.constants import TileType
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
