import unittest
import math
from types import SimpleNamespace
import pygame

from core import config
from core.content import ContentCatalog
from core.context import GameContext
from core.input_manager import InputManager
from entities.actor import Entidade
from components.ai import AIComponent, NPC_DIALOGOS
from map.tile import Tile
from map.map_gen import Mapa, CUSTOM_DECORATION_HITBOXES
from map.terrain import SOLID_DECORATIONS, terrain_material
from map.composicao import CompositorMundo


class FakeMap:
    def __init__(self, largura=80, altura=64):
        self.largura = largura
        self.altura = altura
        self.grid = []
        for _ in range(altura):
            row = []
            for _ in range(largura):
                tile = Tile("grass")
                tile.bioma = "floresta"
                row.append(tile)
            self.grid.append(row)
        self.entidades = []
        self._tree_positions = set()
        self.pontos_interesse = []
        self.trilha_tiles = set()
        self.bonfire_positions = set()
        self.town_lights = set()
        self.efeitos = []
        self.textos = []
        self.particulas = SimpleNamespace(emit=lambda *a, **k: None)

    def obter_tile(self, x, y):
        if 0 <= x < self.largura and 0 <= y < self.altura:
            return self.grid[y][x]
        return None

    def get_tile_hitbox(self, x, y):
        return Mapa.get_tile_hitbox(self, x, y)

    def is_blocked_terrain(self, x, y):
        t = self.obter_tile(x, y)
        return not t or t.bloqueado

    def criar_texto_dano(self, x, y, val, cor=None):
        pass


class TownLifeTests(unittest.TestCase):
    def setUp(self):
        pygame.init()
        self.content = ContentCatalog.load_default()
        self.context = SimpleNamespace(
            content=self.content,
            audio=SimpleNamespace(play=lambda name: None, play_ambient=lambda name: None, stop_ambient=lambda: None),
            input=InputManager(),
            debug_enabled=False,
            settings=None,
        )

    def test_town_props_registration_and_materials(self):
        expected_solid_props = [
            "town_well",
            "street_lamp",
            "market_stall",
            "blacksmith_furnace",
            "blacksmith_anvil",
            "town_workbench",
            "town_bench",
            "barrel_wood",
            "crate_wood",
        ]
        for prop in expected_solid_props:
            self.assertIn(prop, SOLID_DECORATIONS, f"{prop} must be in SOLID_DECORATIONS")
            test_tile = Tile("grass")
            test_tile.decoracao = prop
            mat = terrain_material(test_tile)
            self.assertIn(mat, ["wood", "metal", "stone"], f"{prop} must resolve to a valid material")

    def test_town_props_hitboxes(self):
        expected_hitboxes = [
            "town_well",
            "street_lamp",
            "market_stall",
            "blacksmith_furnace",
            "blacksmith_anvil",
            "town_workbench",
        ]
        for prop in expected_hitboxes:
            self.assertIn(prop, CUSTOM_DECORATION_HITBOXES, f"{prop} must have custom sub-tile hitbox")
            hb = CUSTOM_DECORATION_HITBOXES[prop]
            self.assertEqual(len(hb), 4)
            self.assertGreater(hb[2], 0)
            self.assertGreater(hb[3], 0)

    def test_town_composition_places_new_districts(self):
        world = FakeMap()
        compositor = CompositorMundo(world, seed=91)
        clearings = compositor.gerar(quantidade_clareiras=4)

        # Clearings 2 and 3 are villages
        found_well = False
        found_lamp = False
        found_stall = False
        found_furnace = False
        found_anvil = False
        found_workbench = False

        for y in range(world.altura):
            for x in range(world.largura):
                tile = world.obter_tile(x, y)
                if not tile or not tile.decoracao:
                    continue
                dec = tile.decoracao
                if dec == "town_well":
                    found_well = True
                elif dec == "street_lamp":
                    found_lamp = True
                elif dec == "market_stall":
                    found_stall = True
                elif dec == "blacksmith_furnace":
                    found_furnace = True
                elif dec == "blacksmith_anvil":
                    found_anvil = True
                elif dec == "town_workbench":
                    found_workbench = True

        self.assertTrue(found_well, "Town well must be placed in villages")
        self.assertTrue(found_lamp, "Street lamps must be placed in villages")
        self.assertTrue(found_stall, "Market stalls must be placed in villages")
        self.assertTrue(found_furnace, "Blacksmith furnace must be placed in villages")
        self.assertTrue(found_anvil, "Blacksmith anvil must be placed in villages")
        self.assertTrue(found_workbench, "Town workbench must be placed in villages")

        # Ensure trails are not blocked by new props
        for x, y in world.trilha_tiles:
            tile = world.obter_tile(x, y)
            self.assertFalse(tile.bloqueado, f"Trail tile ({x}, {y}) should not be blocked")

    def test_town_npcs_in_catalog(self):
        npc_names = ["Aldeão", "Guarda da Cidade", "Taberneira", "Mercador", "Alquimista"]
        for name in npc_names:
            self.assertIn(name, self.content.entities)
            spec = self.content.entities[name]
            self.assertEqual(spec.role, "npc")
            self.assertIn(spec.ai_mode, ["citizen", "guard"])
            self.assertGreater(spec.hp, 0)

    def test_npc_dialogue_system(self):
        aldeao = Entidade(10, 10, "Aldeão", self.context)
        self.assertEqual(aldeao.role, "npc")
        self.assertIsNotNone(aldeao.ai)
        self.assertIsNone(aldeao.ai.current_dialog)

        # Trigger dialogue
        world = FakeMap()
        world.entidades.append(aldeao)
        aldeao.ai.falar(world)

        self.assertIsNotNone(aldeao.ai.current_dialog)
        self.assertIn(aldeao.ai.current_dialog, NPC_DIALOGOS["Aldeão"])
        self.assertGreater(aldeao.ai.dialog_timer, 0)

    def test_guard_protects_citizens_from_hostiles(self):
        world = FakeMap()
        world.jogador = None

        guarda = Entidade(10, 10, "Guarda da Cidade", self.context)
        walker = Entidade(11, 10, "Walker", self.context)  # distance 1.0 (< 1.3)
        self.assertEqual(walker.role, "enemy")

        world.entidades.extend([guarda, walker])

        initial_hp = walker.hp
        # Update Guard AI (should detect hostile walker, move/attack)
        guarda.ai.update(world, 0.1)

        self.assertLess(walker.hp, initial_hp)

    def test_town_lights_and_bonfire_query(self):
        mapa = Mapa(self.context)
        # Verify town lights indexed
        self.assertGreater(len(mapa.town_lights), 0)
        first_light = next(iter(mapa.town_lights))
        # Check is_near_bonfire returns true near this light
        self.assertTrue(mapa.is_near_bonfire(first_light[0], first_light[1], radius=3.0))


if __name__ == "__main__":
    unittest.main()
