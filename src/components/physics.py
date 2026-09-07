import math

import pygame
from core import config

class PhysicsComponent:
    MAX_STEP_PIXELS = 4
    CORNER_NUDGE_PIXELS = 4

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
        self.hitbox = self.rect_at(self.x, self.y)

    def rect_at(self, x, y):
        """Retorna a hitbox dos pés para uma posição do mundo."""
        tamanho = config.TAMANHO_TILE
        largura = int(tamanho * self.largura_hb_ratio)
        altura = int(tamanho * self.altura_hb_ratio)
        rect = pygame.Rect(0, 0, largura, altura)
        rect.centerx = round(x * tamanho + tamanho / 2)
        rect.bottom = round(y * tamanho + tamanho)
        return rect

    # --- CORREÇÃO AQUI: Adicionado parametro ignore_ent ---
    def check_collision(self, target_x, target_y, mapa_obj, ignore_ent=None):
        tamanho = config.TAMANHO_TILE
        futuro_rect = self.rect_at(target_x, target_y)
        
        # A. Tiles
        # pygame.Rect usa right/bottom exclusivos. Subtrair 1 evita que apenas
        # tocar a borda de um tile conte como invasão do tile vizinho.
        left = futuro_rect.left // tamanho
        right = (futuro_rect.right - 1) // tamanho
        top = futuro_rect.top // tamanho
        bottom = (futuro_rect.bottom - 1) // tamanho
        for ty in range(top, bottom + 1):
            for tx in range(left, right + 1):
                if mapa_obj.is_blocked_terrain(tx, ty):
                    return True

        # B. Entidades
        candidates = (
            mapa_obj.nearby_entities(futuro_rect)
            if hasattr(mapa_obj, "nearby_entities")
            else mapa_obj.entidades
        )
        for ent in candidates:
            if ent is self.entity: continue
            if ent.hp <= 0: continue
            
            # SE FOR O DONO, IGNORA!
            if ignore_ent and ent is ignore_ent: continue 
            
            if futuro_rect.colliderect(ent.hitbox):
                return True 

        return False

    def move(self, dx, dy, mapa_obj, dt, ignore_ent=None):
        """Move em tiles por segundo, independentemente da taxa de quadros."""
        dt = max(0.0, dt)
        return self.move_by(dx, dy, self.speed * dt, mapa_obj, ignore_ent)

    def move_by(self, dx, dy, distance, mapa_obj, ignore_ent=None):
        """Move uma distância fixa; usado também por impulsos como knockback."""
        self.moving = False
        magnitude = math.hypot(dx, dy)
        if magnitude == 0 or distance <= 0:
            return False

        total_x = dx / magnitude * distance
        total_y = dy / magnitude * distance
        distance_px = max(abs(total_x), abs(total_y)) * config.TAMANHO_TILE
        steps = max(1, math.ceil(distance_px / self.MAX_STEP_PIXELS))
        step_x, step_y = total_x / steps, total_y / steps

        for _ in range(steps):
            if self._move_step(step_x, step_y, mapa_obj, ignore_ent):
                self.moving = True

        self.update_hitbox()
        spatial_index = getattr(mapa_obj, "spatial_index", None)
        if spatial_index is not None:
            spatial_index.update(self.entity)
        return self.moving

    def _move_step(self, step_x, step_y, mapa_obj, ignore_ent):
        target_x, target_y = self.x + step_x, self.y + step_y
        if not self.check_collision(target_x, target_y, mapa_obj, ignore_ent):
            self.x, self.y = target_x, target_y
            return True

        moved = False
        # Em diagonais, desliza pelo eixo livre sem alterar a velocidade total.
        if step_x and step_y:
            if not self.check_collision(self.x + step_x, self.y, mapa_obj, ignore_ent):
                self.x += step_x
                moved = True
            if not self.check_collision(self.x, self.y + step_y, mapa_obj, ignore_ent):
                self.y += step_y
                moved = True
            return moved

        # Se só uma pequena ponta da hitbox tocou a quina, desloca no máximo
        # quatro pixels para contorná-la. Uma parede inteira continua bloqueando.
        tile_size = config.TAMANHO_TILE
        for pixels in range(1, self.CORNER_NUDGE_PIXELS + 1):
            for sign in (-1, 1):
                nudge = sign * pixels / tile_size
                candidate_x = target_x + (nudge if step_y else 0)
                candidate_y = target_y + (nudge if step_x else 0)
                if not self.check_collision(candidate_x, candidate_y, mapa_obj, ignore_ent):
                    self.x, self.y = candidate_x, candidate_y
                    return True
        return False

    def update(self, dt):
        pass
