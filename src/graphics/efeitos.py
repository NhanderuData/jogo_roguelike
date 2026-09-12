import math
import random
import pygame
from core import config

class TextoFlutuante:
    def __init__(self, x, y, texto, cor):
        self.x = x  # Posição no Grid
        self.y = y
        self.texto = str(texto)
        self.cor = cor
        self.life = 1.0
        self.offset_y = 0.0 # Começa no chão e sobe
        
        # Cria a fonte (Pequena e negrito)
        self.font = pygame.font.SysFont("arial", 20, bold=True)
        self.image = self.font.render(self.texto, True, self.cor)
        self.shadow = self.font.render(self.texto, True, config.PRETO) # Sombra

    def update(self, dt):
        self.life -= dt
        self.offset_y -= 1.2 * dt

    def draw(self, surface, camera_x, camera_y):
        # Converte Grid -> Pixel
        screen_x = (self.x * config.TAMANHO_TILE) - camera_x + 10 
        screen_y = (self.y * config.TAMANHO_TILE) - camera_y + (self.offset_y * 32)
        
        # Desenha sombra deslocada e depois o texto
        surface.blit(self.shadow, (screen_x + 2, screen_y + 2))
        surface.blit(self.image, (screen_x, screen_y))


class ImpactoDirecional:
    def __init__(self, x, y, dir_x, dir_y, cor=(255, 210, 95)):
        self.x, self.y = x, y
        self.dir_x, self.dir_y = dir_x, dir_y
        self.cor = cor
        self.life = 0.18
        self.max_life = self.life

    def update(self, dt):
        self.life -= dt

    def draw(self, surface, camera_x, camera_y):
        alpha = int(255 * max(0.0, self.life / self.max_life))
        overlay = pygame.Surface((44, 44), pygame.SRCALPHA)
        center = pygame.Vector2(22, 22)
        direction = pygame.Vector2(self.dir_x, self.dir_y)
        if direction.length_squared() == 0:
            return
        direction = direction.normalize()
        perpendicular = pygame.Vector2(-direction.y, direction.x)
        tip = center - direction * 4
        tail = center - direction * 18
        color = (*self.cor, alpha)
        pygame.draw.line(overlay, color, tail + perpendicular * 5, tip, 2)
        pygame.draw.line(overlay, color, tail - perpendicular * 5, tip, 2)
        screen_x = self.x * config.TAMANHO_TILE - camera_x - 22
        screen_y = self.y * config.TAMANHO_TILE - camera_y - 22
        surface.blit(overlay, (screen_x, screen_y))


class FlashDisparo:
    def __init__(self, x, y, angle, intensity=1.0):
        self.x, self.y = x, y
        self.angle = angle
        self.intensity = intensity
        self.life = 0.075
        self.max_life = self.life

    def update(self, dt):
        self.life -= dt

    def draw(self, surface, camera_x, camera_y):
        alpha = int(255 * max(0.0, self.life / self.max_life))
        size = round(18 * self.intensity)
        overlay = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
        center = pygame.Vector2(size, size)
        direction = pygame.Vector2(1, 0).rotate_rad(self.angle)
        perpendicular = pygame.Vector2(-direction.y, direction.x)
        points = (
            center - perpendicular * 4,
            center + direction * size,
            center + perpendicular * 4,
        )
        pygame.draw.polygon(overlay, (255, 184, 45, alpha // 2), points)
        pygame.draw.circle(overlay, (255, 246, 190, alpha), center, 4)
        sx = self.x * config.TAMANHO_TILE - camera_x - size
        sy = self.y * config.TAMANHO_TILE - camera_y - size
        surface.blit(overlay, (sx, sy))


class Capsula:
    def __init__(self, x, y, angle):
        self.x, self.y = x, y
        side = pygame.Vector2(0, -1).rotate_rad(angle)
        self.vx = side.x * 1.8
        self.vy = side.y * 1.8 - 0.7
        self.height = 0.15
        self.vertical_speed = 2.2
        self.rotation = 0.0
        self.life = 0.65
        self.max_life = self.life

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vx *= max(0.0, 1.0 - 3.0 * dt)
        self.vy *= max(0.0, 1.0 - 3.0 * dt)
        self.height += self.vertical_speed * dt
        self.vertical_speed -= 8.5 * dt
        if self.height < 0:
            self.height = 0
            self.vertical_speed *= -0.28
        self.rotation += 620 * dt
        self.life -= dt

    def draw(self, surface, camera_x, camera_y):
        alpha = int(255 * min(1.0, max(0.0, self.life / 0.18)))
        image = pygame.Surface((7, 3), pygame.SRCALPHA)
        image.fill((205, 145, 45, alpha))
        pygame.draw.line(image, (255, 220, 105, alpha), (1, 0), (5, 0))
        image = pygame.transform.rotate(image, self.rotation)
        sx = self.x * config.TAMANHO_TILE - camera_x - image.get_width() / 2
        sy = (self.y - self.height) * config.TAMANHO_TILE - camera_y - image.get_height() / 2
        surface.blit(image, (sx, sy))


class ExplosaoAnimada:
    """Animação procedural rica de explosão: choque, bola de fogo, fumaça e estilhaços."""
    def __init__(self, x, y, radius_tiles=2.8, damage=140):
        self.x = float(x)
        self.y = float(y)
        self.radius_tiles = radius_tiles
        self.radius_pixels = radius_tiles * config.TAMANHO_TILE
        self.damage = damage
        self.life = 0.58
        self.max_life = self.life
        self.shockwave_radius = 8.0
        self.max_shockwave = self.radius_pixels * 1.15
        self.debris = []
        for _ in range(16):
            ang = random.uniform(0, math.pi * 2)
            spd = random.uniform(130, 290)
            sz = random.choice((2, 3, 4))
            clr = random.choice([
                (255, 255, 220),
                (255, 200, 60),
                (255, 120, 30),
                (240, 50, 20),
            ])
            self.debris.append({
                "ang": ang,
                "spd": spd,
                "dist": random.uniform(4, 12),
                "size": sz,
                "color": clr,
            })

    def update(self, dt):
        self.life -= dt
        progress = 1.0 - max(0.0, self.life / self.max_life)
        self.shockwave_radius = self.max_shockwave * (progress ** 0.5)
        for d in self.debris:
            d["dist"] += d["spd"] * dt * (1.0 - progress * 0.7)

    def draw(self, surface, camera_x, camera_y):
        if self.life <= 0:
            return
        cx = int(self.x * config.TAMANHO_TILE - camera_x)
        cy = int(self.y * config.TAMANHO_TILE - camera_y)

        progress = 1.0 - max(0.0, self.life / self.max_life)

        surf_size = int(self.max_shockwave * 2.4)
        draw_surf = pygame.Surface((surf_size, surf_size), pygame.SRCALPHA)
        local_cx = surf_size // 2
        local_cy = surf_size // 2

        # 1. Onda de choque expansiva
        ring_alpha = int(210 * (1.0 - progress))
        if ring_alpha > 0 and self.shockwave_radius > 6:
            ring_thick = max(2, int(5 * (1.0 - progress)))
            pygame.draw.circle(
                draw_surf,
                (255, 220, 160, ring_alpha),
                (local_cx, local_cy),
                int(self.shockwave_radius),
                ring_thick,
            )

        # 2. Nuvem de fumaça escura
        if progress > 0.12:
            smoke_prog = (progress - 0.12) / 0.88
            smoke_alpha = int(180 * (1.0 - smoke_prog))
            smoke_rad = int(self.radius_pixels * 0.85 * (0.6 + 0.4 * smoke_prog))
            for i in range(6):
                ang = i * (math.pi * 2 / 6) + progress * 0.4
                offset = smoke_rad * 0.35
                sx = int(local_cx + math.cos(ang) * offset)
                sy = int(local_cy + math.sin(ang) * offset)
                pygame.draw.circle(draw_surf, (50, 46, 44, smoke_alpha), (sx, sy), int(smoke_rad * 0.55))

        # 3. Bola de fogo incandescente
        if progress < 0.75:
            fire_prog = progress / 0.75
            fire_alpha = int(240 * (1.0 - fire_prog))
            fire_rad = int(self.radius_pixels * (0.3 + 0.7 * (1.0 - (1.0 - fire_prog)**2)))
            pygame.draw.circle(draw_surf, (240, 65, 20, fire_alpha), (local_cx, local_cy), fire_rad)
            mid_rad = max(4, int(fire_rad * 0.65))
            pygame.draw.circle(draw_surf, (255, 175, 30, fire_alpha), (local_cx, local_cy), mid_rad)

        # 4. Flash ofuscante no início
        if progress < 0.3:
            core_prog = progress / 0.3
            core_alpha = int(255 * (1.0 - core_prog))
            core_rad = max(6, int(self.radius_pixels * 0.45 * (1.0 - core_prog)))
            pygame.draw.circle(draw_surf, (255, 255, 235, core_alpha), (local_cx, local_cy), core_rad)

        # 5. Estilhaços incandescentes
        for d in self.debris:
            px = int(local_cx + math.cos(d["ang"]) * d["dist"])
            py = int(local_cy + math.sin(d["ang"]) * d["dist"])
            p_alpha = int(255 * max(0.0, self.life / self.max_life))
            color_with_alpha = (*d["color"][:3], p_alpha)
            pygame.draw.circle(draw_surf, color_with_alpha, (px, py), d["size"])

        surface.blit(draw_surf, (cx - local_cx, cy - local_cy))


class EfeitoChama:
    """Pluma de fogo animada do lança-chamas com expansão, turbulência e resfriamento."""
    def __init__(self, x, y, angle, speed=16.0):
        self.x = float(x)
        self.y = float(y)
        self.angle = angle + random.uniform(-0.14, 0.14)
        self.speed = speed * random.uniform(0.85, 1.15)
        self.vx = math.cos(self.angle) * self.speed
        self.vy = math.sin(self.angle) * self.speed
        self.life = random.uniform(0.38, 0.52)
        self.max_life = self.life
        self.initial_radius = random.uniform(6, 9)
        self.final_radius = random.uniform(22, 30)
        self.turbulence = random.uniform(-2.2, 2.2)

    def update(self, dt):
        self.life -= dt
        progress = 1.0 - max(0.0, self.life / self.max_life)
        self.vx *= max(0.0, 1.0 - 1.8 * dt)
        self.vy *= max(0.0, 1.0 - 1.8 * dt)
        perp_x = -math.sin(self.angle) * self.turbulence * (1.0 - progress)
        perp_y = math.cos(self.angle) * self.turbulence * (1.0 - progress)
        self.x += (self.vx + perp_x) * dt
        self.y += (self.vy + perp_y) * dt

    def draw(self, surface, camera_x, camera_y):
        if self.life <= 0:
            return
        cx = int(self.x * config.TAMANHO_TILE - camera_x)
        cy = int(self.y * config.TAMANHO_TILE - camera_y)

        progress = 1.0 - max(0.0, self.life / self.max_life)
        radius = int(self.initial_radius + (self.final_radius - self.initial_radius) * (progress ** 0.7))

        if progress < 0.28:
            core_color = (255, 255, 200)
            edge_color = (255, 180, 40)
            alpha = int(230 * (1.0 - progress * 0.5))
        elif progress < 0.72:
            core_color = (255, 140, 30)
            edge_color = (220, 50, 15)
            alpha = int(210 * (1.0 - (progress - 0.28) / 0.44 * 0.4))
        else:
            core_color = (180, 40, 20)
            edge_color = (65, 55, 55)
            alpha = int(140 * max(0.0, (1.0 - progress) / 0.28))

        flame_surf = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
        local_c = radius + 2

        pygame.draw.circle(flame_surf, (*edge_color, alpha), (local_c, local_c), radius)
        inner_r = max(2, int(radius * 0.52))
        pygame.draw.circle(flame_surf, (*core_color, min(255, alpha + 35)), (local_c, local_c), inner_r)

        surface.blit(flame_surf, (cx - local_c, cy - local_c))
