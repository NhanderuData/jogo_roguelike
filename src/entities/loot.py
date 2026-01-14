# src/entities/loot.py
import pygame
import math
from core import config
from core import game_data
from graphics import recursos

class LootDrop:
    def __init__(self, x, y, item_name):
        self.x = x
        self.y = y
        self.item_name = item_name
        self.active = True
        
        # Pega dados visuais
        data = game_data.DATA_ITEMS.get(item_name, {})
        self.cor = data.get("cor", (255, 255, 255))
        
        # Animação de flutuar
        self.float_y = 0
        self.timer = 0
        
        # Hitbox para pegar
        self.rect = pygame.Rect(x * config.TAMANHO_TILE, y * config.TAMANHO_TILE, 32, 32)

    def update(self, dt):
        self.timer += dt * 5
        self.float_y = math.sin(self.timer) * 5 # Flutua 5 pixels

    def draw(self, surface, camera_x, camera_y):
        if not self.active: return
        
        screen_x = (self.x * config.TAMANHO_TILE) - camera_x
        screen_y = (self.y * config.TAMANHO_TILE) - camera_y + self.float_y
        
        # Desenha um brilho/círculo atrás
        pygame.draw.circle(surface, (255, 255, 255, 50), 
                         (screen_x + 16, screen_y + 16 + 5), 10)
        
        # Desenha um quadrado colorido (ou sprite futuramente) representando o item
        # Estamos desenhando pequeno (16x16) centralizado
        rect_draw = pygame.Rect(screen_x + 8, screen_y + 8, 16, 16)
        pygame.draw.rect(surface, self.cor, rect_draw)
        pygame.draw.rect(surface, config.PRETO, rect_draw, 1) # Borda