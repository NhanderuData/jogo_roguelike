from __future__ import annotations

from dataclasses import dataclass
import random

import pygame

from core import config


@dataclass
class Particle:
    x: float
    y: float
    vx: float
    vy: float
    life: float
    max_life: float
    color: tuple[int, int, int]
    size: int
    gravity: float = 0.0

    def update(self, dt: float) -> None:
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += self.gravity * dt
        self.life -= dt


class ParticleSystem:
    """World-space particles for ambience and gameplay feedback."""

    MAX_PARTICLES = 240

    def __init__(self) -> None:
        self.particles: list[Particle] = []
        self.ambient_timer = 0.0
        self.footstep_timer = 0.0
        self._surface_cache = {}

    def emit(self, x: float, y: float, kind: str, count: int = 6, direction=None) -> None:
        palettes = {
            "leaf": ((100, 135, 55), (145, 165, 70), (180, 125, 45)),
            "dust": ((125, 105, 75), (155, 135, 95), (95, 80, 65)),
            "mist": ((155, 180, 175), (125, 155, 155), (185, 195, 185)),
            "hit": ((225, 185, 70), (180, 70, 45), (240, 225, 170)),
            "blood": ((120, 24, 28), (185, 38, 35), (225, 75, 45)),
            "pickup": ((255, 225, 85), (110, 210, 255), (255, 255, 220)),
            "spark": ((255, 245, 170), (255, 170, 45), (245, 95, 35)),
            "stone": ((95, 91, 84), (145, 137, 121), (190, 180, 155)),
            "wood": ((88, 55, 30), (145, 91, 42), (188, 132, 66)),
            "splash": ((110, 205, 255), (65, 150, 235), (210, 240, 255)),
            "armor": ((120, 205, 255), (230, 245, 255), (85, 125, 170)),
            "critical": ((255, 235, 85), (255, 145, 35), (255, 255, 220)),
        }
        palette = palettes.get(kind, palettes["dust"])
        for _ in range(min(count, self.MAX_PARTICLES - len(self.particles))):
            if kind == "leaf":
                vx, vy, life, size, gravity = random.uniform(-0.15, 0.25), random.uniform(0.08, 0.3), random.uniform(1.5, 3.0), random.choice((2, 3)), 0.0
            elif kind == "mist":
                vx, vy, life, size, gravity = random.uniform(0.08, 0.22), random.uniform(-0.03, 0.03), random.uniform(2.0, 4.0), random.choice((4, 5, 6)), 0.0
            elif kind in {"blood", "spark", "stone", "wood", "splash", "armor", "critical"} and direction:
                dir_x, dir_y = direction
                force = random.uniform(0.8, 1.8)
                vx = dir_x * force + random.uniform(-0.35, 0.35)
                vy = dir_y * force + random.uniform(-0.35, 0.35)
                life = random.uniform(0.2, 0.55)
                size = random.choice((2, 3))
                gravity = -0.5 if kind == "splash" else 1.1
            else:
                vx, vy, life, size, gravity = random.uniform(-0.8, 0.8), random.uniform(-0.9, -0.15), random.uniform(0.25, 0.65), random.choice((2, 3)), 1.4
            self.particles.append(
                Particle(
                    x=x + random.uniform(-0.25, 0.25),
                    y=y + random.uniform(-0.15, 0.15),
                    vx=vx,
                    vy=vy,
                    life=life,
                    max_life=life,
                    color=random.choice(palette),
                    size=size,
                    gravity=gravity,
                )
            )

    def update(self, dt: float, map_obj) -> None:
        for particle in self.particles:
            particle.update(dt)
        self.particles[:] = [
            particle for particle in self.particles if particle.life > 0
        ]

        player = map_obj.jogador
        if not player:
            return

        tile = map_obj.obter_tile(player.x, player.y)
        terrain = tile.tipo if tile else "terra"

        self.ambient_timer -= dt
        if self.ambient_timer <= 0 and len(self.particles) < self.MAX_PARTICLES:
            self.ambient_timer = 0.12
            x = player.x + random.uniform(-22, 22)
            y = player.y + random.uniform(-14, 14)
            kind = "mist" if terrain in ("mud", "blue_ground", "deep_water") else "leaf"
            self.emit(x, y, kind, 1)

        self.footstep_timer = max(0.0, self.footstep_timer - dt)
        if player.moving and self.footstep_timer == 0:
            self.footstep_timer = 0.12
            kind = "leaf" if terrain in ("grass", "blue_ground") else "dust"
            self.emit(player.x, player.y + 0.6, kind, 2)

    def draw(self, surface: pygame.Surface, camera_x: float, camera_y: float) -> None:
        for particle in self.particles:
            alpha = int(255 * max(0.0, particle.life / particle.max_life))
            x = int(particle.x * config.TAMANHO_TILE - camera_x)
            y = int(particle.y * config.TAMANHO_TILE - camera_y)
            alpha = (alpha // 16) * 16
            key = (particle.size, particle.color, alpha)
            particle_surface = self._surface_cache.get(key)
            if particle_surface is None:
                particle_surface = pygame.Surface(
                    (particle.size, particle.size), pygame.SRCALPHA
                )
                particle_surface.fill((*particle.color, alpha))
                self._surface_cache[key] = particle_surface
            surface.blit(particle_surface, (x, y))
