# -*- coding: utf-8 -*-
"""
战斗系统模块
"""

import random
import pygame
from src.data_loader import Config, SkillType, GameState, GameDatabase


class BattleSystem:
    """战斗系统管理器"""

    def __init__(self, game):
        self.game = game
        self.menu_options = ["攻击", "技能", "道具", "防御"]

    def handle_battle_input(self, event):
        """处理战斗状态输入"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.attempt_escape()
                return

            if self.game.battle_turn != "player":
                return

            if self.game.battle_selecting_skill:
                self.handle_skill_selection(event)
            elif self.game.battle_selecting_item:
                self.handle_item_selection(event)
            else:
                self.handle_battle_menu(event)

    def handle_battle_menu(self, event):
        """处理战斗菜单"""
        if event.key == pygame.K_UP:
            self.game.battle_menu_index = (self.game.battle_menu_index - 1) % len(self.menu_options)
        elif event.key == pygame.K_DOWN:
            self.game.battle_menu_index = (self.game.battle_menu_index + 1) % len(self.menu_options)
        elif event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
            if self.game.battle_menu_index == 0:
                self.player_attack()
            elif self.game.battle_menu_index == 1:
                self.game.battle_selecting_skill = True
                self.game.battle_submenu_index = 0
            elif self.game.battle_menu_index == 2:
                self.game.battle_selecting_item = True
                self.game.battle_submenu_index = 0
            elif self.game.battle_menu_index == 3:
                self.player_defend()

    def handle_skill_selection(self, event):
        """处理技能选择"""
        skills = [GameDatabase.SKILLS[sid] for sid in self.game.player.unlocked_skills]

        if len(skills) == 0:
            self.game.battle_log.append("没有已解锁的技能！")
            self.game.battle_selecting_skill = False
            return

        if event.key == pygame.K_ESCAPE:
            self.game.battle_selecting_skill = False
            return

        if event.key == pygame.K_UP:
            self.game.battle_submenu_index = (self.game.battle_submenu_index - 1) % len(skills)
        elif event.key == pygame.K_DOWN:
            self.game.battle_submenu_index = (self.game.battle_submenu_index + 1) % len(skills)
        elif event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
            skill = skills[self.game.battle_submenu_index]
            self.execute_skill(skill)

    def execute_skill(self, skill):
        """执行技能"""
        if self.game.player.mp < skill.mana_cost:
            self.game.battle_log.append("MP不足！")
            self.game.battle_selecting_skill = False
            return

        self.game.player.mp -= skill.mana_cost

        if skill.skill_type == SkillType.PHYSICAL or skill.skill_type == SkillType.MAGIC:
            total_damage = skill.damage
            if skill.skill_type == SkillType.PHYSICAL:
                total_damage += self.game.player.get_total_attack()
                total_damage -= self.game.battle_enemy.defense // 2
            else:
                total_damage += self.game.player.get_total_magic()
                total_damage -= self.game.battle_enemy.defense // 3

            total_damage = max(1, total_damage + random.randint(-5, 5))
            self.game.battle_enemy.hp -= total_damage
            self.game.battle_log.append(f"使用 {skill.name}！造成 {total_damage} 点伤害！")

        elif skill.skill_type == SkillType.HEAL:
            heal_amount = skill.heal_amount + self.game.player.get_total_magic() // 2
            self.game.player.hp = min(self.game.player.max_hp, self.game.player.hp + heal_amount)
            self.game.battle_log.append(f"使用 {skill.name}！恢复了 {heal_amount} 点HP！")

        elif skill.skill_type == SkillType.BUFF:
            self.game.player.buffs.append({
                "stat": skill.buff_stat,
                "amount": skill.buff_amount,
                "duration": skill.buff_duration
            })
            self.game.battle_log.append(f"使用 {skill.name}！{skill.buff_stat}提升了 {skill.buff_amount}！")

        elif skill.skill_type == SkillType.DEBUFF:
            self.game.battle_enemy.attack = max(1, self.game.battle_enemy.attack - 10)
            self.game.battle_log.append(f"使用 {skill.name}！敌人的攻击力降低了！")

        self.game.battle_selecting_skill = False
        self.check_battle_status()

    def handle_item_selection(self, event):
        """处理道具选择"""
        consumables = []
        for item_id, qty in self.game.player.inventory.items():
            if item_id in GameDatabase.ITEMS:
                item = GameDatabase.ITEMS[item_id]
                if item.item_type.value == "消耗品":
                    consumables.append((item, qty))

        if event.key == pygame.K_ESCAPE:
            self.game.battle_selecting_item = False
            return

        if len(consumables) == 0:
            self.game.battle_log.append("没有可用的道具！")
            self.game.battle_selecting_item = False
            return

        if event.key == pygame.K_UP:
            self.game.battle_submenu_index = (self.game.battle_submenu_index - 1) % len(consumables)
        elif event.key == pygame.K_DOWN:
            self.game.battle_submenu_index = (self.game.battle_submenu_index + 1) % len(consumables)
        elif event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
            item, qty = consumables[self.game.battle_submenu_index]
            self.use_item_in_battle(item)

    def use_item_in_battle(self, item):
        """在战斗中使用道具"""
        if item.heal_amount > 0:
            old_hp = self.game.player.hp
            self.game.player.hp = min(self.game.player.max_hp, self.game.player.hp + item.heal_amount)
            actual_heal = self.game.player.hp - old_hp
            self.game.battle_log.append(f"使用 {item.name}！恢复了 {actual_heal} 点HP！")

        if item.mana_amount > 0:
            old_mp = self.game.player.mp
            self.game.player.mp = min(self.game.player.max_mp, self.game.player.mp + item.mana_amount)
            actual_mana = self.game.player.mp - old_mp
            self.game.battle_log.append(f"使用 {item.name}！恢复了 {actual_mana} 点MP！")

        self.game.player.remove_item(item.id)
        self.game.battle_selecting_item = False
        self.check_battle_status()

    def player_attack(self):
        """玩家普通攻击"""
        damage = max(1, self.game.player.get_total_attack() - self.game.battle_enemy.defense // 2 + random.randint(-3, 3))
        self.game.battle_enemy.hp -= damage
        self.game.battle_log.append(f"造成 {damage} 点伤害！")
        self.check_battle_status()

    def player_defend(self):
        """玩家防御"""
        self.game.player.buffs.append({
            "stat": "defense",
            "amount": self.game.player.get_total_defense() // 2,
            "duration": 1
        })
        self.game.battle_log.append("采取防御姿态！")
        self.end_player_turn()

    def check_battle_status(self):
        """检查战斗状态"""
        if self.game.battle_enemy.hp <= 0:
            self.game.battle_enemy.hp = 0
            if self.game.battle_ended:
                return
            self.game.battle_ended = True
            self.win_battle()
        else:
            self.end_player_turn()

    def end_player_turn(self):
        """结束玩家回合"""
        self.game.player_turn_done = True
        self.game.battle_turn = "enemy"
        pygame.time.set_timer(pygame.USEREVENT + 1, 1000)

    def enemy_turn(self):
        """敌人回合"""
        if self.game.battle_enemy.hp <= 0:
            return

        damage = max(1, self.game.battle_enemy.attack - self.game.player.get_total_defense() // 2 + random.randint(-3, 3))
        self.game.player.hp -= damage
        self.game.battle_log.append(f"{self.game.battle_enemy.name} 造成了 {damage} 点伤害！")

        if self.game.player.hp <= 0:
            self.game.player.hp = 0
            self.game.state = GameState.GAME_OVER
        else:
            self.game.battle_turn = "player"
            self.game.player_turn_done = False
            pygame.time.set_timer(pygame.USEREVENT + 1, 0)

    def win_battle(self):
        """战斗胜利"""
        self.game.player.enemies_defeated += 1

        # 记录敌人到图鉴
        if self.game.battle_enemy.id not in self.game.player.known_enemies:
            self.game.player.known_enemies.add(self.game.battle_enemy.id)
            self.game.show_message(f"发现新敌人: {self.game.battle_enemy.name}!")

        exp_gained = self.game.battle_enemy.exp_reward
        gold_gained = self.game.battle_enemy.gold_reward

        self.game.player.gain_exp(exp_gained)
        self.game.player.gold += gold_gained

        self.game.battle_log.append("战斗胜利！")
        self.game.battle_log.append(f"获得 {exp_gained} 经验值，{gold_gained} 金币！")

        for drop_id in self.game.battle_enemy.drops:
            if random.random() < 0.3:
                self.game.player.add_item(drop_id)
                item = GameDatabase.ITEMS.get(drop_id)
                if item:
                    # 记录物品到图鉴
                    if drop_id not in self.game.player.known_items:
                        self.game.player.known_items.add(drop_id)
                    self.game.battle_log.append(f"获得 {item.name}！")

        if getattr(self.game, 'is_arena_battle', False):
            self.game.update_quest_objective("kill", "arena_enemy")
            self.game.is_arena_battle = False

        self.game.update_quest_objective("kill", self.game.battle_enemy.id)
        self.game.update_quest_objective("kill", "any")

        pygame.time.set_timer(pygame.USEREVENT + 2, 2000)

    def attempt_escape(self):
        """尝试逃跑"""
        if random.random() < 0.5:
            self.game.battle_log.append("成功逃跑！")
            self.reset_battle_state()
            self.game.state = GameState.EXPLORE
        else:
            self.game.battle_log.append("逃跑失败！")
            self.end_player_turn()

    def reset_battle_state(self):
        """重置战斗状态"""
        self.game.battle_enemy = None
        self.game.battle_log = []
        self.game.battle_turn = "player"
        self.game.battle_menu_index = 0
        self.game.battle_submenu_index = 0
        self.game.battle_selecting_skill = False
        self.game.battle_selecting_item = False
        self.game.player_turn_done = False
        self.game.battle_ended = False
        self.game.keys_pressed = {'up': False, 'down': False, 'left': False, 'right': False}
        self.game.move_cooldown = 0