# src/entities/loot.py
import pygame
import math
from core import config
from core.content import ContentCatalog
from graphics import recursos

class LootDrop:
    def __init__(self, x, y, item_name, content: ContentCatalog):
        self.x = x
        self.y = y
        self.item_name = item_name
        self.active = True
        
        # Pega dados visuais
        data = content.items.get(item_name)
        self.cor = data.color if data else (255, 255, 255)
        self.sprite_key = data.sprite if data else None
        source_image = recursos.SPRITES.get(self.sprite_key)
        self.image = (
            pygame.transform.scale(source_image, (40, 40))
            if source_image
            else None
        )
        
        # Animação
        self.float_y = 0
        self.timer = 0
        
        # --- NOVO: Delay para evitar coleta instantânea ---
        self.pickup_delay = 0.7
        
        # Hitbox (será usada na verificação)
        self.rect = pygame.Rect(x * config.TAMANHO_TILE, y * config.TAMANHO_TILE, 32, 32)

    def update(self, dt):
        self.timer += dt * 5
        self.float_y = math.sin(self.timer) * 5
        
        # Reduz o tempo de espera
        if self.pickup_delay > 0:
            self.pickup_delay -= dt

    def pode_pegar(self):
        """Só retorna True se o tempo de delay já passou"""
        return self.pickup_delay <= 0

    def draw(self, surface, camera_x, camera_y):
        if not self.active: return
        
        # --- CORREÇÃO: Converter para INT para evitar erros de desenho ---
        screen_x = int((self.x * config.TAMANHO_TILE) - camera_x)
        screen_y = int((self.y * config.TAMANHO_TILE) - camera_y + self.float_y)
        
        # Desenha brilho (Sólido se não tiver alpha blend na surface principal)
        pygame.draw.circle(surface, (255, 255, 255), 
                         (screen_x + 16, screen_y + 16), 12, 2) # Círculo vazado (borda 2)
        
        if self.image:
            surface.blit(self.image, (screen_x - 4, screen_y - 4))
        else:
            rect_draw = pygame.Rect(screen_x + 8, screen_y + 8, 16, 16)
            pygame.draw.rect(surface, self.cor, rect_draw)
            pygame.draw.rect(surface, config.PRETO, rect_draw, 1)
