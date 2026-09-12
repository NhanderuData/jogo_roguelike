from __future__ import annotations

from . import biomas, composicao


def inside_ellipse(x, y, center, radii, edge_noise=0.0):
    radius_x, radius_y = radii
    distance = (
        ((x - center[0]) / radius_x) ** 2
        + ((y - center[1]) / radius_y) ** 2
    )
    return distance + edge_noise * 0.45 <= 1.0


class TerrainPainter:
    """Traduz campos de ruído em tiles; não controla spawn nem runtime."""

    def __init__(self, world, noise, rng):
        self.world = world
        self.noise = noise
        self.rng = rng

    def paint(self) -> None:
        for y in range(self.world.altura):
            for x in range(self.world.largura):
                self._paint_tile(x, y)
        self._paint_shorelines()

    def _paint_tile(self, x, y) -> None:
        tile = self.world.obter_tile(x, y)
        if not tile:
            return
        tile.bloqueado = False
        tile.tipo = "terra"
        tile.decoracao = None
        tile.bioma = None
        tile.orientacao = None

        terrain_value = self.noise.terrain(x, y)
        biome_value = self.noise.biome(x, y)
        density = self.noise.detail(x, y)
        roll = self.rng.randint(0, 100)
        pond_zone = composicao.classificar_lagoa(
            x, y, self.world.ponds, self.noise.pond_edge(x, y)
        )

        if inside_ellipse(
            x,
            y,
            self.world.desert_center,
            self.world.desert_radii,
            self.noise.desert(x, y),
        ):
            biomas.aplicar_bioma_deserto(
                self.world, x, y, tile, roll, density, self.rng
            )
            self.world.desert_tile_count += 1
        elif pond_zone == "agua":
            tile.tipo = "deep_water"
            tile.bloqueado = True
            tile.bioma = "lagoa"
            self.world.pond_tile_count += 1
        elif pond_zone == "margem":
            biomas.aplicar_margem_lagoa(tile, roll, self.rng)
        elif terrain_value < -0.28:
            tile.tipo = "deep_water"
            tile.bloqueado = True
            tile.bioma = "agua"
        elif inside_ellipse(
            x,
            y,
            self.world.snow_center,
            self.world.snow_radii,
            self.noise.snow(x, y),
        ):
            biomas.aplicar_bioma_azul(
                self.world, x, y, tile, roll, density, self.rng
            )
            self.world.snow_tile_count += 1
        elif biome_value < 0.1:
            biomas.aplicar_bioma_floresta(
                self.world, x, y, tile, roll, density, self.rng
            )
        else:
            biomas.aplicar_bioma_ruinas(
                self.world, x, y, tile, roll, density, self.rng
            )

    def _paint_shorelines(self) -> None:
        """Aplica areia e costa exclusivamente ao redor de corpos reais de água profunda."""
        water_tiles = set()
        for y in range(self.world.altura):
            for x in range(self.world.largura):
                tile = self.world.obter_tile(x, y)
                if tile and tile.tipo == "deep_water" and tile.bioma == "agua":
                    water_tiles.add((x, y))

        if not water_tiles:
            return

        sand_candidates = set()
        for wx, wy in water_tiles:
            for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
                nx, ny = wx + dx, wy + dy
                tile = self.world.obter_tile(nx, ny)
                if (
                    tile
                    and tile.tipo not in ("deep_water", "sand", "blue_ground")
                    and tile.bioma not in ("deserto", "neve")
                ):
                    sand_candidates.add((nx, ny))

        for sx, sy in sand_candidates:
            tile = self.world.obter_tile(sx, sy)
            if tile:
                tile.tipo = "sand"
                tile.bioma = "litoral"
                tile.bloqueado = False
                if tile.decoracao and biomas.decoracao_solida(tile.decoracao):
                    tile.decoracao = None

        for sx, sy in sand_candidates:
            for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
                nx, ny = sx + dx, sy + dy
                tile = self.world.obter_tile(nx, ny)
                if (
                    tile
                    and tile.tipo == "grass"
                    and tile.bioma not in ("deserto", "neve")
                ):
                    tile.tipo = "coast"
                    tile.bioma = "litoral"
