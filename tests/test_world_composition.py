import random
import unittest

import pygame

from core.content import ContentCatalog
from core.context import GameContext
from core.input_manager import InputManager
from graphics.renderer import Renderer
from graphics.lighting import LightingRenderer
from map.composicao import (
    CompositorMundo,
    Lagoa,
    classificar_lagoa,
    gerar_lagoas,
    suavizar_margens_lagoa,
)
from map.tile import Tile
from map.map_gen import Mapa
from map.settings import WorldSettings


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

    def obter_tile(self, x, y):
        if 0 <= x < self.largura and 0 <= y < self.altura:
            return self.grid[y][x]
        return None


class PondCompositionTests(unittest.TestCase):
    def test_pond_has_water_core_shore_and_exterior(self):
        pond = Lagoa(20, 20, 5, 4)

        self.assertEqual(classificar_lagoa(20, 20, [pond]), "agua")
        self.assertEqual(classificar_lagoa(26, 20, [pond]), "margem")
        self.assertIsNone(classificar_lagoa(29, 20, [pond]))

    def test_pond_generation_is_deterministic_and_honors_validator(self):
        def valid_center(x, _y, _rx, _ry):
            return x >= 40

        first = gerar_lagoas(
            100,
            80,
            random.Random(44),
            quantidade=3,
            centro_valido=valid_center,
        )
        second = gerar_lagoas(
            100,
            80,
            random.Random(44),
            quantidade=3,
            centro_valido=valid_center,
        )

        self.assertEqual(first, second)
        self.assertEqual(len(first), 3)
        self.assertTrue(all(pond.x >= 40 for pond in first))

    def test_renderer_selects_cardinal_and_corner_pond_edges(self):
        world = FakeMap(5, 5)
        for row in world.grid:
            for tile in row:
                tile.tipo = "deep_water"
        world.obter_tile(2, 1).tipo = "grass"

        self.assertEqual(Renderer._pond_edge_name(world, 2, 2), "north")

        world.obter_tile(1, 2).tipo = "grass"
        self.assertEqual(Renderer._pond_edge_name(world, 2, 2), "north_west")

    def test_pond_smoothing_removes_unsupported_single_tile_tip(self):
        world = FakeMap(9, 9)
        for y in range(2, 7):
            for x in range(2, 7):
                tile = world.obter_tile(x, y)
                tile.tipo = "deep_water"
                tile.bioma = "lagoa"
                tile.bloqueado = True

        tip = world.obter_tile(7, 4)
        tip.tipo = "deep_water"
        tip.bioma = "lagoa"
        tip.bloqueado = True

        remaining = suavizar_margens_lagoa(world)

        self.assertEqual(tip.tipo, "grass")
        self.assertFalse(tip.bloqueado)
        self.assertEqual(world.obter_tile(4, 4).tipo, "deep_water")
        self.assertEqual(remaining, 25)


class WorldGenerationTests(unittest.TestCase):
    @staticmethod
    def _signature(world):
        tiles = tuple(
            (tile.tipo, tile.bioma, tile.decoracao, tile.bloqueado)
            for row in world.grid
            for tile in row
        )
        entities = tuple(
            sorted((entity.nome, round(entity.x, 4), round(entity.y, 4)) for entity in world.entidades)
        )
        return tiles, entities, tuple(world.ponds), tuple(world.clareiras)

    def test_same_seed_builds_the_same_world(self):
        context = GameContext(InputManager(), ContentCatalog.load_default())
        settings = WorldSettings(
            width=64,
            height=64,
            chunk_size=16,
            enemy_count=3,
        )

        first = Mapa(context, seed=12_345, settings=settings)
        second = Mapa(context, seed=12_345, settings=settings)

        self.assertEqual(self._signature(first), self._signature(second))

    def test_world_settings_reject_invalid_dimensions(self):
        with self.assertRaisesRegex(ValueError, "at least 64x64"):
            WorldSettings(width=32, height=64)


class BonfireRenderingTests(unittest.TestCase):
    def test_bonfire_adds_warm_light_around_its_tile(self):
        world = FakeMap(9, 9)
        world.projeteis = []
        world.obter_tile(4, 4).decoracao = "nature_bonfire"
        lighting = LightingRenderer((288, 288))
        surface = pygame.Surface((288, 288))
        surface.fill((0, 0, 0))

        lighting.draw_lights(surface, world, 0, 0)

        center = surface.get_at((144, 138))[:3]
        middle = surface.get_at((190, 138))[:3]
        self.assertGreater(sum(center), sum(middle))
        self.assertGreater(sum(middle), 0)
        self.assertLess(max(center), 220)
        self.assertEqual(surface.get_at((0, 0))[:3], (0, 0, 0))


class ClearingCompositionTests(unittest.TestCase):
    def test_clearings_are_connected_clear_and_receive_landmarks(self):
        world = FakeMap()
        compositor = CompositorMundo(world, seed=91)

        clearings = compositor.gerar(quantidade_clareiras=4)

        self.assertEqual(len(clearings), 4)
        self.assertGreater(len(world.trilha_tiles), 0)
        self.assertEqual(
            {point.tipo for point in world.pontos_interesse},
            {"horta_abandonada", "acampamento"},
        )
        for clearing in clearings:
            tile = world.obter_tile(*clearing.centro)
            self.assertFalse(tile.bloqueado)
            self.assertNotEqual(tile.tipo, "deep_water")
            self.assertIn(clearing.centro, world.trilha_tiles)
        for x, y in world.trilha_tiles:
            tile = world.obter_tile(x, y)
            self.assertFalse(tile.bloqueado)
            self.assertNotEqual(tile.tipo, "deep_water")

        garden = next(
            point
            for point in world.pontos_interesse
            if point.tipo == "horta_abandonada"
        )
        self.assertFalse(world.obter_tile(garden.x, garden.y - 3).bloqueado)
        fence_footprint = [
            world.obter_tile(garden.x + dx, garden.y + dy)
            for dx, dy in (
                (-3, -3),
                (3, -3),
                (-4, -2),
                (4, -2),
                (-3, 3),
                (3, 3),
            )
        ]
        self.assertTrue(any(tile.bloqueado for tile in fence_footprint))


if __name__ == "__main__":
    unittest.main()
