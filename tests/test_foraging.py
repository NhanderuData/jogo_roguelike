import math
import unittest

import pygame

from components.combat import CombatComponent
from components.combat_system import executar_golpe_espada
from components.inventory import InventoryComponent
from components.physics import PhysicsComponent
from components.status import StatusComponent
from core.camera import Camera
from core.content import ContentCatalog
from core.context import GameContext
from graphics.lighting import LightingRenderer
from map.map_gen import HARVESTABLE_CROPS, Mapa
from map.tile import Tile


class MinimalWorld:
    def __init__(self, content):
        self.content = content
        self.largura = 20
        self.altura = 20
        self.grid = [[Tile("grass") for _ in range(self.largura)] for _ in range(self.altura)]
        self.items_no_chao = []
        self.safras_em_crescimento = []
        self.entidades = []
        self.efeitos = []
        self.projeteis = []
        self.particulas = None
        self.jogador = None

    def obter_tile(self, x, y):
        if 0 <= x < self.largura and 0 <= y < self.altura:
            return self.grid[y][x]
        return None

    def colher_decoracao(self, x, y, jogador=None):
        return Mapa.colher_decoracao(self, x, y, jogador)

    def obter_decoracao_colhivel_proxima(self, px, py, raio=1.5):
        return Mapa.obter_decoracao_colhivel_proxima(self, px, py, raio)

    def colher_mais_proximo(self, px, py, raio=1.5, jogador=None):
        return Mapa.colher_mais_proximo(self, px, py, raio, jogador)

    def atualizar_regeneracao_safras(self, current_day=None):
        return Mapa.atualizar_regeneracao_safras(self, current_day)


class DummyPlayer:
    def __init__(self, content, x=5.0, y=5.0):
        self.x = x
        self.y = y
        self.nome = "Player"
        self.role = "player"
        self.direction = "right"
        self.status = StatusComponent(self)
        self.inventory = InventoryComponent(content)
        self.combat = CombatComponent(self, hp_max=100, damage=10)
        self.physics = PhysicsComponent(self, x, y)
        self.physics.speed = 4.0
        self.hitbox = pygame.Rect(int(x * 32), int(y * 32), 24, 24)

    def tomar_dano(self, dano):
        self.combat.take_damage(dano)

    @property
    def hp(self):
        return self.combat.hp

    @hp.setter
    def hp(self, val):
        self.combat.hp = val

    @property
    def hp_max(self):
        return self.combat.hp_max


class ForagingAndFoodTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        if not pygame.display.get_surface():
            pygame.display.set_mode((1, 1), pygame.NOFRAME)

    def setUp(self):
        self.content = ContentCatalog.load_default()
        self.world = MinimalWorld(self.content)
        self.player = DummyPlayer(self.content, 5.0, 5.0)
        self.world.jogador = self.player

    def test_harvestable_crops_defined_in_catalog(self):
        for crop_key, (item_name, _) in HARVESTABLE_CROPS.items():
            self.assertIn(item_name, self.content.items, f"Item {item_name} must exist in catalog")
            item_def = self.content.items[item_name]
            self.assertEqual(item_def.kind, "comida")

    def test_direct_harvest_clears_tile_and_spawns_loot(self):
        tile = self.world.obter_tile(5, 5)
        tile.decoracao = "farm_carrot"

        harvested = self.world.colher_decoracao(5, 5, self.player)
        self.assertTrue(harvested)
        self.assertIsNone(tile.decoracao)
        self.assertEqual(len(self.world.items_no_chao), 1)
        loot = self.world.items_no_chao[0]
        self.assertEqual(loot.item_name, "Cenoura")
        self.assertEqual(len(self.world.safras_em_crescimento), 1)
        safra = self.world.safras_em_crescimento[0]
        self.assertEqual(safra["especie"], "farm_carrot")
        self.assertEqual(safra["dias_para_brotar"], 1)

    def test_harvest_closest_with_range_limit(self):
        tile = self.world.obter_tile(6, 5)
        tile.decoracao = "farm_beet"

        # Player at (5.0, 5.0), target tile center is (6.5, 5.5) -> distance is sqrt(1.5^2 + 0.5^2) ~ 1.58
        far = self.world.colher_mais_proximo(5.0, 5.0, raio=1.2, jogador=self.player)
        self.assertFalse(far)
        self.assertEqual(tile.decoracao, "farm_beet")

        # Within 2.0 tiles: successfully harvested
        near = self.world.colher_mais_proximo(5.0, 5.0, raio=2.0, jogador=self.player)
        self.assertTrue(near)
        self.assertIsNone(tile.decoracao)
        self.assertEqual(self.world.items_no_chao[-1].item_name, "Beterraba")

    def test_crop_regrowth_cycle(self):
        tile = self.world.obter_tile(7, 7)
        tile.decoracao = "farm_cabbage"

        self.world.colher_decoracao(7, 7, self.player)
        self.assertIsNone(tile.decoracao)

        # Day 1: should not regrow yet
        self.world.atualizar_regeneracao_safras(current_day=1)
        self.assertIsNone(tile.decoracao)

        # Day 2: 1 cycle elapsed, should regrow cabbage
        self.world.atualizar_regeneracao_safras(current_day=2)
        self.assertEqual(tile.decoracao, "farm_cabbage")
        self.assertEqual(len(self.world.safras_em_crescimento), 0)

    def test_mushroom_regrowth_takes_two_cycles(self):
        tile = self.world.obter_tile(8, 8)
        tile.decoracao = "nature_mushroom"

        self.world.colher_decoracao(8, 8, self.player)
        self.assertIsNone(tile.decoracao)

        # Day 2: 1 cycle, mushrooms require 2
        self.world.atualizar_regeneracao_safras(current_day=2)
        self.assertIsNone(tile.decoracao)

        # Day 3: 2 cycles elapsed, should regrow
        self.world.atualizar_regeneracao_safras(current_day=3)
        self.assertEqual(tile.decoracao, "nature_mushroom")

    def test_harvest_via_sword_attack(self):
        # Place a crop directly 1 tile to the right of player
        tile = self.world.obter_tile(6, 5)
        tile.decoracao = "farm_onion"

        # Sword strike to the right (target 7.0, 5.0)
        executar_golpe_espada(self.player, 7.0, 5.0, self.world)

        self.assertIsNone(tile.decoracao)
        self.assertTrue(any(l.item_name == "Cebola" for l in self.world.items_no_chao))

    def test_food_consumption_effects(self):
        # 1. Carrot: Light heal + Night Vision
        self.player.hp = 50
        self.player.inventory.add_item("Cenoura", 1)
        used = self.player.inventory.usar_item(0, self.player)
        self.assertTrue(used)
        self.assertEqual(self.player.hp, 60)
        self.assertGreater(self.player.status.night_vision_timer, 0)

        # 2. Beet: Gradual regeneration
        self.player.inventory.add_item("Beterraba", 1)
        used = self.player.inventory.usar_item(0, self.player)
        self.assertTrue(used)
        self.assertGreater(self.player.status.regen_timer, 0)

        # Gradual regen tick
        initial_hp = self.player.hp
        self.player.status.update(1.6)
        self.assertGreater(self.player.hp, initial_hp)

        # 3. Mushroom: Heals and cures bleeding
        self.player.status.add_sangramento(3)
        self.player.inventory.add_item("Cogumelo", 1)
        used = self.player.inventory.usar_item(0, self.player)
        self.assertTrue(used)
        self.assertEqual(self.player.status.sangramento, 0)

        # 4. Toxic mushroom: Dizziness effect
        self.player.inventory.add_item("Cogumelo Estranho", 1)
        used = self.player.inventory.usar_item(0, self.player)
        self.assertTrue(used)
        self.assertGreater(self.player.status.dizziness_timer, 0)

    def test_camera_dizziness_sway(self):
        camera = Camera()
        camera.update(self.player.x, self.player.y, 0.1, world_size=(20, 20), dizziness=0.0)
        base_x = camera.camera_x

        camera.update(self.player.x, self.player.y, 0.1, world_size=(20, 20), dizziness=5.0)
        self.assertNotEqual(camera.camera_x, base_x)

    def test_lighting_night_vision_softens_darkness(self):
        lighting = LightingRenderer((800, 600))
        surf = pygame.Surface((100, 100))

        # Without night vision
        self.player.status.night_vision_timer = 0.0
        lighting.apply_darkness(surf, (10, 10, 20, 200), player=self.player)
        normal_alpha = lighting._darkness.get_at((0, 0))[3]

        # With night vision
        self.player.status.night_vision_timer = 30.0
        lighting.apply_darkness(surf, (10, 10, 20, 200), player=self.player)
        softened_alpha = lighting._darkness.get_at((0, 0))[3]

        self.assertLess(softened_alpha, normal_alpha)
        self.assertEqual(softened_alpha, int(200 * 0.65))


if __name__ == "__main__":
    unittest.main()
