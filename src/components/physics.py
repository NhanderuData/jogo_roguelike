import pygame
from core import config

class PhysicsComponent:
    def __init__(self, entity, x, y, largura_hb=0.6, altura_hb=0.4):
        self.entity = entity
        self.x = float(x)
        self.y = float(y)
        self.speed = 0.0
        
        self.largura_hb_ratio = largura_hb
        self.altura_hb_ratio = altura_hb
        self.hitbox = pygame.Rect(0, 0, 0, 0)
        self.moving = False
        self.update_hitbox()

    def update_hitbox(self):
        tamanho = config.TAMANHO_TILE
        largura = int(tamanho * self.largura_hb_ratio)
        altura = int(tamanho * self.altura_hb_ratio)

        # Atualiza tamanho se mudou
        if self.hitbox.width != largura or self.hitbox.height != altura:
            self.hitbox.size = (largura, altura)
        
        px_x = self.x * tamanho
        px_y = self.y * tamanho

        # Centraliza hitbox na base do tile
        self.hitbox.centerx = int(px_x + (tamanho // 2))
        self.hitbox.bottom = int(px_y + tamanho)

    def move(self, dx, dy, mapa_obj):
        """Tenta mover a entidade e verifica colisões"""
        self.moving = False
        if dx == 0 and dy == 0:
            return

        # Normaliza velocidade se estiver na diagonal
        if dx != 0 and dy != 0:
            dx *= 0.707
            dy *= 0.707
            
        # Calcula nova posição potencial
        nx = self.x + dx * self.speed
        ny = self.y + dy * self.speed
        
        # Colisão Eixo X
        if not mapa_obj.is_blocked_terrain(nx, self.y):
            self.x = nx
            self.moving = True
            
        # Colisão Eixo Y
        if not mapa_obj.is_blocked_terrain(self.x, ny):
            self.y = ny
            self.moving = True
            
        self.update_hitbox()

    def update(self, dt):
        # Aqui poderíamos colocar inércia ou knockback no futuro
        pass