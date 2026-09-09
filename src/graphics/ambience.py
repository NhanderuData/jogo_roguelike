from __future__ import annotations

import pygame


class AmbientRenderer:
    """Applies biome tint and slow 2D fog ribbons."""

    TINTS = {
        "blue_ground": (95, 175, 190, 7),
        "mud": (150, 115, 75, 5),
        "rubble": (155, 155, 150, 4),
        "sand": (235, 190, 105, 5),
    }

    def __init__(self) -> None:
        self._tint_cache = {}
        self._fog_surface = None

    def _tint(self, size, color):
        key = (size, color)
        tint = self._tint_cache.get(key)
        if tint is None:
            tint = pygame.Surface(size, pygame.SRCALPHA)
            tint.fill(color)
            self._tint_cache[key] = tint
        return tint

    def draw(self, surface: pygame.Surface, map_obj) -> None:
        player = map_obj.jogador
        if not player:
            return
        tile = map_obj.obter_tile(player.x, player.y)
        terrain = tile.tipo if tile else "grass"

        tint_color = self.TINTS.get(terrain)
        if tint_color:
            surface.blit(self._tint(surface.get_size(), tint_color), (0, 0))

        if terrain not in ("blue_ground", "mud"):
            return

        width, height = surface.get_size()
        elapsed = pygame.time.get_ticks() / 1000.0
        if self._fog_surface is None or self._fog_surface.get_size() != (width, height):
            self._fog_surface = pygame.Surface((width, height), pygame.SRCALPHA)
        fog = self._fog_surface
        fog.fill((0, 0, 0, 0))
        for index in range(3):
            offset = int((elapsed * (9 + index * 2) + index * 370) % (width + 500)) - 500
            y = int(height * (0.28 + index * 0.23))
            points = [
                (offset, y),
                (offset + 260, y - 10),
                (offset + 520, y + 7),
                (offset + 760, y - 4),
                (offset + 760, y + 18),
                (offset + 500, y + 26),
                (offset + 230, y + 14),
                (offset, y + 22),
            ]
            pygame.draw.polygon(fog, (170, 190, 185, 10), points)
        surface.blit(fog, (0, 0))
