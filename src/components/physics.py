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

        if self.hitbox.width != largura or self.hitbox.height != altura:
            self.hitbox.size = (largura, altura)
        
        px_x = self.x * tamanho
        px_y = self.y * tamanho

        self.hitbox.centerx = int(px_x + (tamanho // 2))
        self.hitbox.bottom = int(px_y + tamanho)

    # --- CORREÇÃO AQUI: Adicionado parametro ignore_ent ---
    def check_collision(self, target_x, target_y, mapa_obj, ignore_ent=None):
        tamanho = config.TAMANHO_TILE
        futuro_rect = self.hitbox.copy()
        futuro_px_x = target_x * tamanho
        futuro_px_y = target_y * tamanho
        futuro_rect.centerx = int(futuro_px_x + (tamanho // 2))
        futuro_rect.bottom = int(futuro_px_y + tamanho)
        
        # A. Tiles
        pontos = [futuro_rect.bottomleft, futuro_rect.bottomright, futuro_rect.midbottom, futuro_rect.center]
        for px, py in pontos:
            tx = int(px // tamanho)
            ty = int(py // tamanho)
            if mapa_obj.is_blocked_terrain(tx, ty):
                return True 

        # B. Entidades
        for ent in mapa_obj.entidades:
            if ent is self.entity: continue
            if ent.hp <= 0: continue
            
            # SE FOR O DONO, IGNORA!
            if ignore_ent and ent is ignore_ent: continue 
            
            if futuro_rect.colliderect(ent.hitbox):
                return True 

        return False

    # --- CORREÇÃO AQUI: Repassa o ignore_ent ---
    def move(self, dx, dy, mapa_obj, ignore_ent=None):
        self.moving = False
        if dx == 0 and dy == 0: return

        if dx != 0 and dy != 0:
            dx *= 0.707
            dy *= 0.707
            
        new_x = self.x + dx * self.speed
        if not self.check_collision(new_x, self.y, mapa_obj, ignore_ent):
            self.x = new_x
            self.moving = True
            
        new_y = self.y + dy * self.speed
        if not self.check_collision(self.x, new_y, mapa_obj, ignore_ent):
            self.y = new_y
            self.moving = True
            
        self.update_hitbox()

    def update(self, dt):
        pass