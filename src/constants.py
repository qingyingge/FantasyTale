#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
游戏配置和常量 - 从 data_loader 获取配置
"""

from src.data_loader import (
    Config as BaseConfig,
    PixelArt,
    ItemType,
    SkillType,
    TileType,
    GameState,
    GameDatabase,
    get_sprite,
)


class Config(BaseConfig):
    pass


SPRITE_PLAYER = None
SPRITE_NPC = None
SPRITE_ENEMY = None
SPRITE_TREE = None
SPRITE_HOUSE = None
SPRITE_CHEST = None
SPRITE_PORTAL = None


def load_sprites():
    global SPRITE_PLAYER, SPRITE_NPC, SPRITE_ENEMY
    global SPRITE_TREE, SPRITE_HOUSE, SPRITE_CHEST, SPRITE_PORTAL
    sprites = PixelArt.load_sprites()
    SPRITE_PLAYER = sprites.get("player")
    SPRITE_NPC = sprites.get("npc")
    SPRITE_ENEMY = sprites.get("enemy")
    SPRITE_TREE = sprites.get("tree")
    SPRITE_HOUSE = sprites.get("house")
    SPRITE_CHEST = sprites.get("chest")
    SPRITE_PORTAL = sprites.get("portal")