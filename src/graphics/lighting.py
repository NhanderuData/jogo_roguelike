from __future__ import annotations

import math

import pygame

from core import config


class LightingRenderer:
    """Compõe escuridão e fontes de luz visíveis sem alocar por frame."""

    def __init__(self, size):
        self.projectile_light = self.create_gradient(50, (255, 100, 50))
        bonfire = self.create_gradient(92, (255, 112, 35), 50)
        bonfire_core = self.create_gradient(36, (255, 205, 105), 72)
        self._bonfire_halos = self._variants(bonfire, 0.72, 1.0)
        self._bonfire_cores = self._variants(bonfire_core, 0.82, 1.0)
        self._darkness = pygame.Surface(size, pygame.SRCALPHA)
        self.eye_glow = self.create_gradient(16, (240, 25, 25), 140)
        self.flame_light = self.create_gradient(48, (255, 140, 40), 110)
        self.explosion_light = self.create_gradient(160, (255, 180, 75), 210)
        self.explosion_core = self.create_gradient(70, (255, 245, 190), 255)

    @staticmethod
    def create_gradient(radius, color=(255, 255, 255), intensity=100):
        light = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        light.fill((0, 0, 0, 0))
        red, green, blue = color
        for current_radius in range(radius, 0, -1):
            ratio = current_radius / radius
            strength = intensity * ((1 - ratio) ** 2) / 255
            ring_color = (
                round(red * strength),
                round(green * strength),
                round(blue * strength),
                255,
            )
            pygame.draw.circle(
                light, ring_color, (radius, radius), current_radius
            )
        return light

    @staticmethod
    def _variants(base, minimum, maximum, count=12):
        variants = []
        for index in range(count):
            fraction = index / max(1, count - 1)
            strength = minimum + (maximum - minimum) * fraction
            variant = base.copy()
            value = round(255 * strength)
            variant.fill(
                (value, value, value, 255),
                special_flags=pygame.BLEND_RGBA_MULT,
            )
            variants.append(variant)
        return variants

    def apply_darkness(self, surface, color, player=None):
        if self._darkness.get_size() != surface.get_size():
            self._darkness = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        
        # Visão noturna suaviza o véu de escuridão da noite
        if player and getattr(getattr(player, "status", None), "night_vision_timer", 0) > 0:
            r, g, b, *a = color
            alpha = a[0] if a else 255
            color = (r, g, b, int(alpha * 0.65))

        self._darkness.fill(color)
        surface.blit(self._darkness, (0, 0))

    def draw_lights(self, surface, world, camera_x, camera_y):
        elapsed = pygame.time.get_ticks() / 1000.0
        oscillation = (
            math.sin(elapsed * 7.3) * 0.07
            + math.sin(elapsed * 12.7) * 0.03
        )
        halo_strength = max(0.72, min(1.0, 0.88 + oscillation))
        core_strength = max(0.82, min(1.0, 0.94 + oscillation * 0.45))
        halo_index = round(
            (halo_strength - 0.72) / 0.28 * (len(self._bonfire_halos) - 1)
        )
        core_index = round(
            (core_strength - 0.82) / 0.18 * (len(self._bonfire_cores) - 1)
        )
        halo = self._bonfire_halos[halo_index]
        core = self._bonfire_cores[core_index]

        tile_size = config.TAMANHO_TILE
        margin = math.ceil(halo.get_width() / tile_size)
        start_x = max(0, int(camera_x // tile_size) - margin)
        end_x = min(
            world.largura,
            int((camera_x + surface.get_width()) // tile_size) + margin + 1,
        )
        start_y = max(0, int(camera_y // tile_size) - margin)
        end_y = min(
            world.altura,
            int((camera_y + surface.get_height()) // tile_size) + margin + 1,
        )

        for y in range(start_y, end_y):
            for x in range(start_x, end_x):
                tile = world.obter_tile(x, y)
                if tile and tile.decoracao in {"nature_bonfire", "street_lamp", "blacksmith_furnace"}:
                    center_x = x * tile_size - camera_x + tile_size // 2
                    center_y = y * tile_size - camera_y + tile_size // 3
                    self._blit_centered(surface, halo, center_x, center_y)
                    self._blit_centered(surface, core, center_x, center_y)

        # Aura de Visão Noturna do Jogador (concedida por cenouras)
        player = getattr(world, "jogador", None)
        if player and getattr(getattr(player, "status", None), "night_vision_timer", 0) > 0:
            if not hasattr(self, "_night_vision_halo"):
                self._night_vision_halo = self.create_gradient(135, (255, 195, 120), 80)
                self._night_vision_core = self.create_gradient(65, (255, 235, 180), 100)
            pcx = player.x * tile_size - camera_x + tile_size // 2
            pcy = player.y * tile_size - camera_y + tile_size // 2
            self._blit_centered(surface, self._night_vision_halo, pcx, pcy)
            self._blit_centered(surface, self._night_vision_core, pcx, pcy)

        for projectile in world.projeteis:
            if not projectile.active:
                continue
            center_x = projectile.x * tile_size - camera_x
            center_y = projectile.y * tile_size - camera_y
            self._blit_centered(
                surface, self.projectile_light, center_x, center_y
            )

        for entity in getattr(world, "entidades", ()):
            if "nocturnal" not in getattr(entity, "tags", ()):
                continue
            if getattr(getattr(entity, "combat", None), "hp", 1) <= 0:
                continue

            phys = getattr(entity, "physics", None)
            if not phys:
                continue

            cx = int(phys.x * tile_size - camera_x + tile_size // 2)
            cy = int(phys.y * tile_size - camera_y + tile_size // 3)

            if not (-32 <= cx <= surface.get_width() + 32 and -32 <= cy <= surface.get_height() + 32):
                continue

            facing_dir = getattr(getattr(entity, "sprite", None), "direction", "right")
            eye_shift = 1 if facing_dir == "right" else -1
            e1_x = cx - 3 + eye_shift
            e2_x = cx + 3 + eye_shift
            eye_y = cy - 2

            self._blit_centered(surface, self.eye_glow, e1_x, eye_y)
            self._blit_centered(surface, self.eye_glow, e2_x, eye_y)
            pygame.draw.circle(surface, (255, 45, 35), (e1_x, eye_y), 2)
            pygame.draw.circle(surface, (255, 220, 200), (e1_x, eye_y), 1)
            pygame.draw.circle(surface, (255, 45, 35), (e2_x, eye_y), 2)
            pygame.draw.circle(surface, (255, 220, 200), (e2_x, eye_y), 1)

        # Iluminação dinâmica de efeitos visuais (Explosões e Chamas)
        for efeito in getattr(world, "efeitos", ()):
            if getattr(efeito, "life", 0) <= 0:
                continue
            ex = getattr(efeito, "x", None)
            ey = getattr(efeito, "y", None)
            if ex is None or ey is None:
                continue
            cx = int(ex * tile_size - camera_x)
            cy = int(ey * tile_size - camera_y)
            if not (-180 <= cx <= surface.get_width() + 180 and -180 <= cy <= surface.get_height() + 180):
                continue
            cls_name = efeito.__class__.__name__
            if cls_name == "ExplosaoAnimada":
                self._blit_centered(surface, self.explosion_light, cx, cy)
                self._blit_centered(surface, self.explosion_core, cx, cy)
            elif cls_name == "EfeitoChama":
                self._blit_centered(surface, self.flame_light, cx, cy)

        for entity in getattr(world, "entidades", ()):
            combat = getattr(entity, "combat", None)
            if combat and getattr(combat, "burn_timer", 0) > 0 and getattr(combat, "hp", 1) > 0:
                cx = int((entity.x + 0.5) * tile_size - camera_x)
                cy = int((entity.y + 0.5) * tile_size - camera_y)
                self._blit_centered(surface, self.flame_light, cx, cy)

    @staticmethod
    def _blit_centered(surface, light, center_x, center_y):
        surface.blit(
            light,
            (
                center_x - light.get_width() // 2,
                center_y - light.get_height() // 2,
            ),
            special_flags=pygame.BLEND_ADD,
        )
