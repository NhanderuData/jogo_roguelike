import math
import os
import unittest
from pathlib import Path
from types import SimpleNamespace
import pygame

from core import config
from core.content import ContentCatalog
from core.context import GameContext
from core.input_manager import InputManager
from entities.actor import Entidade
from components.weapons import WeaponComponent
from components import combat_system
from graphics import recursos
from graphics import efeitos
from map.tile import Tile


class FakeMap:
    def __init__(self, largura=40, altura=40):
        self.largura = largura
        self.altura = altura
        self.grid = [[Tile("grass") for _ in range(largura)] for _ in range(altura)]
        self.entidades = []
        self.projeteis = []
        self.efeitos = []
        self.textos = []
        self.particulas = SimpleNamespace(emit=lambda *a, **k: None)
        self.context = SimpleNamespace(
            audio=SimpleNamespace(play=lambda *a, **k: None),
        )
        self.camera = SimpleNamespace(add_trauma=lambda *a, **k: None)

    def obter_tile(self, x, y):
        if 0 <= x < self.largura and 0 <= y < self.altura:
            return self.grid[y][x]
        return None

    def is_blocked_terrain(self, x, y):
        t = self.obter_tile(x, y)
        return not t or t.bloqueado

    def get_tile_hitbox(self, x, y):
        return None

    def criar_texto_dano(self, x, y, dmg, cor=None):
        pass


class WeaponBehaviorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        try:
            pygame.display.set_mode((1, 1))
        except Exception:
            pass
        recursos.carregar_tudo()

    def setUp(self):
        self.content = ContentCatalog.load_default()
        self.context = SimpleNamespace(
            content=self.content,
            audio=SimpleNamespace(play=lambda *a, **k: None, play_ambient=lambda *a, **k: None, stop_ambient=lambda: None),
            input=InputManager(),
            debug_enabled=False,
            settings=None,
        )

    def test_core_weapons_catalog_integrity(self):
        # Assegura que as 3 armas clássicas feias foram removidas
        self.assertNotIn("pistol", self.content.weapons)
        self.assertNotIn("shotgun", self.content.weapons)
        self.assertNotIn("smg", self.content.weapons)

        # Assegura que as armas do pacote + lança-chamas e RPG estão presentes
        self.assertIn("pistol_glock17", self.content.weapons)
        self.assertIn("shotgun_remington870", self.content.weapons)
        self.assertIn("smg_mp5", self.content.weapons)
        self.assertIn("machete", self.content.weapons)
        self.assertIn("flamethrower", self.content.weapons)
        self.assertIn("rpg", self.content.weapons)

        # Assegura que não há sabres de luz nem armas laser
        for wid in self.content.weapons:
            self.assertNotIn("saber", wid.lower())
            self.assertNotIn("laser", wid.lower())
        recursos.validar_sprites_conteudo(self.content)

    def test_flamethrower_piercing_and_burn(self):
        world = FakeMap()
        player = Entidade(10, 10, "Survivor", self.context)
        world.jogador = player

        enemy1 = Entidade(11.0, 10.0, "Walker", self.context)
        enemy2 = Entidade(12.0, 10.0, "Walker", self.context)
        world.entidades.extend([player, enemy1, enemy2])

        player.weapons.current_id = "flamethrower"
        player.weapons.attack(15, 10, world)
        self.assertEqual(len(world.projeteis), 1)
        proj = world.projeteis[0]
        self.assertEqual(proj.projectile_type, "flame")

        # Ao atualizar, o fogo atravessa inimigos em fila, infligindo dano e queimadura
        proj.update(0.1, world)
        self.assertTrue(proj.active, "O projétil de fogo deve ser perfurante (piercing)")
        self.assertGreater(enemy1.combat.burn_timer, 0.0)

    def test_explosion_aoe_and_knockback(self):
        world = FakeMap()
        player = Entidade(10, 10, "Survivor", self.context)
        world.jogador = player

        enemy_near = Entidade(12.0, 10, "Walker", self.context)
        enemy_far = Entidade(15.0, 10, "Walker", self.context)
        world.entidades.extend([player, enemy_near, enemy_far])

        hp_near_before = enemy_near.hp
        hp_far_before = enemy_far.hp
        x_near_before = enemy_near.x

        proj = combat_system.Projetil(
            10.5, 10.5, 0.0, "player", player, damage=140, speed=20.0, projectile_type="rocket"
        )
        proj._criar_explosao(world, 11.5, 10.5)

        # Inimigo próximo deve sofrer dano alto, queimadura e knockback radial
        self.assertLess(enemy_near.hp, hp_near_before)
        self.assertGreater(enemy_near.combat.burn_timer, 0.0)
        self.assertGreater(enemy_near.x, x_near_before)

        # Inimigo distante (> raio 2.8) não deve sofrer dano
        self.assertEqual(enemy_far.hp, hp_far_before)

        # Animação procedural rica de explosão deve ter sido criada
        self.assertTrue(any(isinstance(e, efeitos.ExplosaoAnimada) for e in world.efeitos))

    def test_shotgun_balanced_behavior(self):
        shotgun = self.content.weapons["shotgun_remington870"]
        # A escopeta deve ter entre 6 e 8 projéteis (pellets) e dano balanceado por pellet (<= 20)
        self.assertGreaterEqual(shotgun.pellets, 6)
        self.assertLessEqual(shotgun.pellets, 8)
        self.assertLessEqual(shotgun.damage, 20)
        self.assertGreaterEqual(shotgun.damage, 10)
        self.assertEqual(shotgun.ammo_type, "shell")
        self.assertFalse(shotgun.auto)

        world = FakeMap()
        player = Entidade(10, 10, "Survivor", self.context)
        world.jogador = player
        player.weapons.current_id = "shotgun_remington870"

        # Disparar escopeta gera exatamente a quantidade de pellets configurada
        player.weapons.attack(15, 10, world)
        self.assertEqual(len(world.projeteis), shotgun.pellets)

    def test_smg_single_pellet_and_automatic(self):
        smg = self.content.weapons["smg_mp5"]
        # SMG DEVE disparar 1 projétil por ciclo (pellets == 1), NÃO múltiplos simultâneos
        self.assertEqual(smg.pellets, 1)
        self.assertTrue(smg.auto)
        self.assertLessEqual(smg.cooldown, 0.1)
        self.assertLessEqual(smg.critical_chance, 0.2)
        self.assertEqual(smg.ammo_type, "9mm")

        world = FakeMap()
        player = Entidade(10, 10, "Survivor", self.context)
        world.jogador = player
        player.weapons.unlocked.add("smg_mp5")
        player.weapons.current_id = "smg_mp5"

        player.weapons.attack(15, 10, world)
        self.assertEqual(len(world.projeteis), 1)

    def test_machete_hits_at_point_blank_and_arc(self):
        world = FakeMap()
        player = Entidade(10, 10, "Survivor", self.context)
        world.jogador = player

        # Inimigo colado no jogador (à queima roupa, x=10.4)
        enemy_close = Entidade(10.4, 10, "Walker", self.context)
        # Inimigo um pouco à frente dentro do alcance (x=11.1)
        enemy_reach = Entidade(11.1, 10, "Walker", self.context)
        # Inimigo atrás do jogador (x=9.0) - NÃO deve ser atingido
        enemy_behind = Entidade(9.0, 10, "Walker", self.context)

        world.entidades.extend([player, enemy_close, enemy_reach, enemy_behind])

        hp_close_before = enemy_close.hp
        hp_reach_before = enemy_reach.hp
        hp_behind_before = enemy_behind.hp

        # Golpeando para a direita (alvo em x=15, y=10)
        combat_system.executar_golpe_espada(player, 15, 10, world, damage=35, alcance=1.4)

        # Inimigo colado e inimigo dentro do alcance frontal devem tomar dano
        self.assertLess(enemy_close.hp, hp_close_before)
        self.assertLess(enemy_reach.hp, hp_reach_before)
        # Inimigo atrás NÃO deve tomar dano
        self.assertEqual(enemy_behind.hp, hp_behind_before)

        # Efeito visual de arco de corte deve ser criado
        self.assertGreater(len(world.efeitos), 0)
        self.assertIsInstance(world.efeitos[0], combat_system.EfeitoVisual)

    def test_pistol_semi_auto_and_accuracy(self):
        pistol = self.content.weapons["pistol_glock17"]
        self.assertEqual(pistol.pellets, 1)
        self.assertFalse(pistol.auto)
        self.assertEqual(pistol.magazine_size, 17)
        self.assertEqual(pistol.ammo_type, "9mm")
        self.assertLess(pistol.spread, 0.05)

    def test_smg_unlock_by_inventory_item(self):
        player = Entidade(10, 10, "Survivor", self.context)
        weapons = player.weapons
        self.assertNotIn("smg_mp5", weapons.unlocked)

        player.inventory.add_item("Submetralhadora MP5")
        idx = len(player.inventory.items) - 1
        success = player.inventory.usar_item(idx, player)
        self.assertTrue(success)
        self.assertIn("smg_mp5", weapons.unlocked)
        self.assertEqual(weapons.current_id, "smg_mp5")


if __name__ == "__main__":
    unittest.main()
