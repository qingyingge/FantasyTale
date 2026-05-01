#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据模型 - 从 data_loader 获取游戏数据
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional

from src.data_loader import ItemType, SkillType, GameDatabase, Item, Skill, Enemy, Quest, QuestObjective, QuestObjective


@dataclass
class Player:
    pass


@dataclass
class GameState:
    pass