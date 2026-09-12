import random
from types import SimpleNamespace
import unittest

import pygame

from core import config
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

        # Inner corners (cardinal neighbors are water, diagonal neighbor is land)
        for row in world.grid:
            for tile in row:
                tile.tipo = "deep_water"
        world.obter_tile(1, 1).tipo = "grass"
        self.assertEqual(Renderer._pond_edge_name(world, 2, 2), "inner_north_west")

        world.obter_tile(1, 1).tipo = "deep_water"
        world.obter_tile(3, 1).tipo = "grass"
        self.assertEqual(Renderer._pond_edge_name(world, 2, 2), "inner_north_east")

        world.obter_tile(3, 1).tipo = "deep_water"
        world.obter_tile(1, 3).tipo = "grass"
        self.assertEqual(Renderer._pond_edge_name(world, 2, 2), "inner_south_west")

        world.obter_tile(1, 3).tipo = "deep_water"
        world.obter_tile(3, 3).tipo = "grass"
        self.assertEqual(Renderer._pond_edge_name(world, 2, 2), "inner_south_east")

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


class DepthSortingTests(unittest.TestCase):
    @staticmethod
    def _order(object_y, player_y):
        object_depth = (object_y + 1) * config.TAMANHO_TILE
        player_depth = Renderer._linha_de_profundidade(player_y)
        commands = [
            (config.LAYER_CORPO, object_depth, "object"),
            (config.LAYER_CORPO, player_depth, "player"),
        ]
        commands.sort(key=lambda item: (item[0], item[1]))
        return [item[2] for item in commands]

    def test_player_depth_uses_feet_instead_of_tile_origin(self):
        self.assertEqual(self._order(object_y=10, player_y=9.8), [
            "player",
            "object",
        ])
        self.assertEqual(self._order(object_y=10, player_y=10.2), [
            "object",
            "player",
        ])

    def test_player_wins_stable_tie_with_tile_decoration(self):
        self.assertEqual(self._order(object_y=10, player_y=10), [
            "object",
            "player",
        ])


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
    @staticmethod
    def _build_composition():
        world = FakeMap()
        compositor = CompositorMundo(world, seed=91)
        clearings = compositor.gerar(quantidade_clareiras=4)
        return world, compositor, clearings

    def test_clearings_are_connected_clear_and_receive_landmarks(self):
        world, _compositor, clearings = self._build_composition()

        self.assertEqual(len(clearings), 4)
        self.assertGreater(len(world.trilha_tiles), 0)
        self.assertTrue(
            {"horta_abandonada", "acampamento", "vila"}.issubset(
                {point.tipo for point in world.pontos_interesse}
            )
        )
        village_points = [
            point for point in world.pontos_interesse if point.tipo == "vila"
        ]
        self.assertCountEqual(
            [point.centro for point in village_points],
            [clearing.centro for clearing in clearings[2:]],
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

    def test_each_village_has_three_prefabs_with_coherent_collision(self):
        world, compositor, clearings = self._build_composition()
        layouts = compositor._LAYOUTS_CASA

        self.assertEqual(len(layouts), 3)
        required_layout_fields = {
            "dx",
            "dy",
            "largura",
            "profundidade",
            "sprite",
        }
        for layout in layouts:
            self.assertTrue(required_layout_fields.issubset(layout))
            self.assertTrue(layout["sprite"].startswith("village_house_"))

        expected_anchors = {}
        for clearing in clearings[2:]:
            anchors_for_clearing = []
            for layout in layouts:
                anchor = (
                    clearing.x + layout["dx"],
                    clearing.y + layout["dy"],
                )
                anchors_for_clearing.append(anchor)
                expected_anchors[anchor] = layout["sprite"]

                anchor_tile = world.obter_tile(*anchor)
                self.assertIsNotNone(anchor_tile)
                self.assertEqual(anchor_tile.decoracao, layout["sprite"])
                self.assertTrue(anchor_tile.decoracao.startswith("village_house_"))
                self.assertTrue(anchor_tile.bloqueado)

                half_width = layout["largura"] // 2
                footprint = [
                    world.obter_tile(x, y)
                    for y in range(
                        anchor[1] - layout["profundidade"] + 1,
                        anchor[1] + 1,
                    )
                    for x in range(
                        anchor[0] - half_width,
                        anchor[0] + half_width + 1,
                    )
                ]
                self.assertTrue(all(tile is not None for tile in footprint))
                self.assertTrue(all(tile.bloqueado for tile in footprint))

                access_tile = world.obter_tile(anchor[0], anchor[1] + 1)
                self.assertIsNotNone(access_tile)
                self.assertFalse(access_tile.bloqueado)

            self.assertEqual(len(set(anchors_for_clearing)), 3)

        self.assertEqual(len(expected_anchors), 3 * len(clearings[2:]))
        actual_houses = {
            (x, y): tile.decoracao
            for y, row in enumerate(world.grid)
            for x, tile in enumerate(row)
            if (tile.decoracao or "").startswith("village_house_")
        }
        self.assertEqual(actual_houses, expected_anchors)


class TreeLifecycleTests(unittest.TestCase):
    def test_spawn_tree_blocks_base_tile_and_clears_base_decoration(self):
        from types import SimpleNamespace
        from map.biomas import _spawn_tree
        from core.content import ContentCatalog
        from map.tile import Tile

        class WorldStub:
            def __init__(self):
                self.tiles = {(5, 5): Tile(tipo="grass", bloqueado=False)}
                self.tiles[(5, 5)].decoracao = "nature_flower_white"
                self.entidades = []
                self._tree_positions = set()
                self.context = SimpleNamespace(
                    content=ContentCatalog.load_default(),
                    audio=None,
                )
                self.gameplay_rng = None

            def obter_tile(self, x, y):
                return self.tiles.get((x, y))

        world = WorldStub()
        spawned = _spawn_tree(world, 5, 5, "Arvore")
        self.assertTrue(spawned)
        self.assertTrue(world.tiles[(5, 5)].bloqueado)
        self.assertIsNone(world.tiles[(5, 5)].decoracao)
        self.assertIn((5, 5), world._tree_positions)
        self.assertEqual(len(world.entidades), 1)
        tree = world.entidades[0]
        self.assertEqual(tree.hitbox, pygame.Rect(5 * 32, 5 * 32, 32, 32))

    def test_tree_death_unblocks_tile_and_drops_wood(self):
        import random
        from map.simulation import WorldSimulation
        from core.content import ContentCatalog
        from map.tile import Tile
        from entities import actor

        catalog = ContentCatalog.load_default()
        context = SimpleNamespace(content=catalog, audio=None)

        class ParticleStub:
            def emit(self, *args):
                pass
            def update(self, *args):
                pass

        class SpatialIndexStub:
            def remove(self, *args):
                pass

        class WorldStub:
            def __init__(self):
                self.jogador = None
                self.tile = Tile(tipo="grass", bloqueado=True)
                self.entidades = []
                self._tree_positions = {(3, 4)}
                self.items_no_chao = []
                self.projeteis = []
                self.efeitos = []
                self.textos = []
                self.particulas = ParticleStub()
                self.spatial_index = SpatialIndexStub()
                self.content = catalog
                self.context = context
                self.gameplay_rng = random.Random(42)

            def obter_tile(self, x, y):
                if (x, y) == (3, 4):
                    return self.tile
                return None

        world = WorldStub()
        tree = actor.Entidade(3, 4, "Arvore", context)
        world.entidades.append(tree)

        sim = WorldSimulation(world)
        sim._resolve_deaths()
        self.assertTrue(world.tile.bloqueado)
        self.assertEqual(len(world.items_no_chao), 0)

        tree.combat.hp = 0
        sim._resolve_deaths()
        self.assertFalse(world.tile.bloqueado)
        self.assertNotIn((3, 4), world._tree_positions)
        self.assertEqual(len(world.entidades), 0)
        self.assertEqual(len(world.items_no_chao), 1)
        self.assertEqual(world.items_no_chao[0].item_name, "Madeira")


if __name__ == "__main__":
    unittest.main()
