# src/efeitos.py
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
