import math
import pygame
from core import config
from graphics import recursos
# Importamos os componentes para o Projétil usar a mesma lógica do Herói
from components.physics import PhysicsComponent
from components.sprite import SpriteComponent

# --- EFEITO VISUAL (Risco da Espada) ---
# Mantemos simples pois é apenas visual temporário
class EfeitoVisual:
    def __init__(self, x, y, angle):
        self.x = x
        self.y = y
        self.angle = angle
        self.life = 10 

    def update(self):
        self.life -= 1

    def draw(self, surface, camera_x, camera_y):
        cx = self.x * config.TAMANHO_TILE - camera_x
        cy = self.y * config.TAMANHO_TILE - camera_y
        end_x = cx + math.cos(self.angle) * 40
        end_y = cy + math.sin(self.angle) * 40
        largura = max(1, int(self.life / 2))
        pygame.draw.line(surface, config.BRANCO, (cx, cy), (end_x, end_y), largura)

# --- HELPER DE COLISÃO ---
class Hitbox:
    def __init__(self, x, y, w, h):
        self.x, self.y, self.w, self.h = x, y, w, h
    def colliderect(self, other):
        return (self.x < other.x + other.w and self.x + self.w > other.x and
                self.y < other.y + other.h and self.y + self.h > other.y)

# --- NOVO PROJÉTIL (Entidade ECS) ---
class Projetil:
    # 1. Recebe 'dono' no __init__
    def __init__(self, x, y, angle, origem, dono, damage=None, speed=0.3):
        self.name = "Projetil"
        self.origem = origem 
        self.dono = dono # Guarda quem atirou
        self.damage = damage
        self.active = True
        self.life = 100
        
        # Física e Sprite iguais ao anterior...
        self.physics = PhysicsComponent(self, x, y, largura_hb=0.4, altura_hb=0.4)
        self.physics.speed = speed
        self.dx = math.cos(angle)
        self.dy = math.sin(angle)
        self.sprite = SpriteComponent(self, "shoot", layer=config.LAYER_AEREO)

    # ... Properties x, y, image iguais ...
    @property
    def x(self): return self.physics.x
    @x.setter
    def x(self, val): self.physics.x = val
    @property
    def y(self): return self.physics.y
    @y.setter
    def y(self, val): self.physics.y = val
    @property
    def image(self): return self.sprite.image

    def update(self, mapa_obj):
        old_x, old_y = self.x, self.y
        
        # 2. Passa self.dono para o move
        self.physics.move(self.dx, self.dy, mapa_obj, ignore_ent=self.dono)
        
        if abs(self.x - old_x) < 0.001 and abs(self.y - old_y) < 0.001:
            self.active = False
            return

        self.sprite.update(0)
        self.life -= 1
        if self.life <= 0: self.active = False

        # Lógica de Dano igual, mas podemos usar o dono para evitar friendly fire extra
        proj_rect = Hitbox(self.x * 32, self.y * 32, 12, 12)
        
        # Define alvos (agora garantimos que não pega o dono)
        targets = [e for e in mapa_obj.entidades if e != self.dono]
        
        for ent in targets:
            ent_rect = Hitbox(ent.x * 32, ent.y * 32, 32, 32)
            if proj_rect.colliderect(ent_rect):
                dano = self.damage if self.damage is not None else (5 if self.origem == "enemy" else 15)
                ent.tomar_dano(dano, mapa_obj)
                mapa_obj.particulas.emit(ent.x, ent.y, "hit", 8)
                
                # --- ALTERAÇÃO AQUI ---
                # Apenas verificamos se morreu, mas NÃO removemos aqui.
                # O map_gen.py vai tratar do XP e do Loot depois.
                if ent.hp <= 0 and ent != mapa_obj.jogador:
                     pass # mapa_obj.entidades.remove(ent)  <--- COMENTE OU APAGUE ESTA LINHA
                # ----------------------
                
                self.active = False
                return

    def draw(self, surface, cx, cy): pass

# --- Factory Atualizada ---
def criar_projetil(
    x, y, tx, ty, origem, mapa_obj, dono, damage=None, speed=0.3, angle_offset=0.0
):
    angle = math.atan2(ty - y, tx - x) + angle_offset
    p = Projetil(x, y, angle, origem, dono, damage=damage, speed=speed)
    mapa_obj.projeteis.append(p)

def executar_golpe_espada(atacante, tx, ty, mapa_obj, damage=None, alcance=1.0):
    angle = math.atan2(ty - atacante.y, tx - atacante.x)
    efeito = EfeitoVisual(atacante.x, atacante.y, angle)
    mapa_obj.efeitos.append(efeito)
    
    distancia_golpe = alcance
    hit_x = atacante.x + math.cos(angle) * distancia_golpe
    hit_y = atacante.y + math.sin(angle) * distancia_golpe
    area_golpe = Hitbox(hit_x * 32 - 24, hit_y * 32 - 24, 48, 48)
    
    alvos = [e for e in mapa_obj.entidades if e != atacante]
    acertou = False
    
    for alvo in alvos:
        alvo_rect = Hitbox(alvo.x * 32, alvo.y * 32, 32, 32)
        if area_golpe.colliderect(alvo_rect):
            # Usa o Dano vindo do CombatComponent do atacante
            alvo.tomar_dano(damage if damage is not None else atacante.dano * 2, mapa_obj)
            mapa_obj.particulas.emit(alvo.x, alvo.y, "hit", 10)
            
            # Knockback: Empurra usando o sistema de física do alvo
            alvo.physics.move(math.cos(angle) * 0.5, math.sin(angle) * 0.5, mapa_obj)
            
            acertou = True
            if alvo.hp <= 0:
                pass
                #atacante.ganhar_xp(alvo.xp_reward)
                #if alvo in mapa_obj.entidades: mapa_obj.entidades.remove(alvo)
    return acertou
