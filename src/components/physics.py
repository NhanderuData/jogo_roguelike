import pygame
from core import config

class PhysicsComponent:
    def __init__(self, entity, x, y, largura_hb=0.6, altura_hb=0.4):
        self.entity = entity
        self.x = float(x)
        self.y = float(y)
        self.speed = 0.0
        
        # Configuração da Hitbox
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

        # Centraliza hitbox na base do tile (pé do personagem no mundo)
        self.hitbox.centerx = int(px_x + (tamanho // 2))
        self.hitbox.bottom = int(px_y + tamanho)

    def check_collision(self, target_x, target_y, mapa_obj):
        """
        Verifica se a hitbox colidiria com parede na posição alvo.
        Checamos os 4 cantos da hitbox futura para garantir solidez.
        """
        tamanho = config.TAMANHO_TILE
        
        # Cria uma hitbox temporária na posição futura
        temp_rect = self.hitbox.copy()
        
        # Calcula onde a hitbox estaria em pixels
        futuro_px_x = target_x * tamanho
        futuro_px_y = target_y * tamanho
        
        temp_rect.centerx = int(futuro_px_x + (tamanho // 2))
        temp_rect.bottom = int(futuro_px_y + tamanho)
        
        # Pontos para checar (Base e Topo da hitbox)
        pontos = [
            temp_rect.bottomleft,
            temp_rect.bottomright,
            temp_rect.midbottom, # Importante para não passar em quinas
            temp_rect.center
        ]
        
        for px, py in pontos:
            # Converte pixel de volta para Grid (Tile X, Tile Y)
            tx = int(px // tamanho)
            ty = int(py // tamanho)
            
            if mapa_obj.is_blocked_terrain(tx, ty):
                return True # Colidiu
                
        return False

    def move(self, dx, dy, mapa_obj):
        """Move tentando deslizar nas paredes"""
        self.moving = False
        if dx == 0 and dy == 0:
            return

        # Normaliza diagonal
        if dx != 0 and dy != 0:
            dx *= 0.707
            dy *= 0.707
            
        # Tentativa de movimento em X
        new_x = self.x + dx * self.speed
        if not self.check_collision(new_x, self.y, mapa_obj):
            self.x = new_x
            self.moving = True
            
        # Tentativa de movimento em Y
        new_y = self.y + dy * self.speed
        if not self.check_collision(self.x, new_y, mapa_obj):
            self.y = new_y
            self.moving = True
            
        self.update_hitbox()

    def update(self, dt):
        pass