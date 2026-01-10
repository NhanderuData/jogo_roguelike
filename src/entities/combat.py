# src/entities/combat.py
import math
import pygame
from graphics import config
from graphics import recursos 

# --- EFEITO VISUAL (Risco da Espada) ---
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

# --- HITBOX ---
class Hitbox:
    def __init__(self, x, y, w, h):
        self.x, self.y, self.w, self.h = x, y, w, h
    def colliderect(self, other):
        return (self.x < other.x + other.w and self.x + self.w > other.x and
                self.y < other.y + other.h and self.y + self.h > other.y)

# --- FUNÇÕES AUXILIARES ---
def criar_projetil(x, y, tx, ty, origem, mapa_obj):
    angle = math.atan2(ty - y, tx - x)
    p = Projetil(x, y, angle, origem)
    mapa_obj.projeteis.append(p)

def executar_golpe_espada(atacante, tx, ty, mapa_obj):
    angle = math.atan2(ty - atacante.y, tx - atacante.x)
    efeito = EfeitoVisual(atacante.x, atacante.y, angle)
    mapa_obj.efeitos.append(efeito)
    
    distancia_golpe = 1.0
    hit_x = atacante.x + math.cos(angle) * distancia_golpe
    hit_y = atacante.y + math.sin(angle) * distancia_golpe
    area_golpe = Hitbox(hit_x * 32 - 24, hit_y * 32 - 24, 48, 48)
    
    alvos = [e for e in mapa_obj.entidades if e != atacante]
    acertou = False
    
    for alvo in alvos:
        alvo_rect = Hitbox(alvo.x * 32, alvo.y * 32, 32, 32)
        if area_golpe.colliderect(alvo_rect):
            alvo.tomar_dano(atacante.dano * 2, mapa_obj)
            alvo.x += math.cos(angle) * 0.5
            alvo.y += math.sin(angle) * 0.5
            acertou = True
            if alvo.hp <= 0:
                atacante.ganhar_xp(alvo.xp_reward)
                if alvo in mapa_obj.entidades: mapa_obj.entidades.remove(alvo)
    return acertou

# --- PROJÉTIL (Bola de Fogo) ---
class Projetil:
    def __init__(self, x, y, angle, origem):
        self.x = x; self.y = y; self.speed = 0.3
        self.dx = math.cos(angle) * self.speed
        self.dy = math.sin(angle) * self.speed
        self.life = 100; self.active = True; self.origem = origem
        
        # CORREÇÃO AQUI: "shoot" tudo minúsculo para bater com recursos.py
        self.image = recursos.SPRITES.get("shoot") 

    def update(self, mapa_obj):
        self.x += self.dx; self.y += self.dy; self.life -= 1
        
        if mapa_obj.is_blocked_terrain(int(self.x), int(self.y)): 
            self.active = False; return
        
        proj_rect = Hitbox(self.x * 32, self.y * 32, 12, 12)
        targets = [mapa_obj.jogador] if self.origem == "enemy" else [e for e in mapa_obj.entidades if e != mapa_obj.jogador]
        
        for ent in targets:
            ent_rect = Hitbox(ent.x * 32, ent.y * 32, 32, 32)
            if proj_rect.colliderect(ent_rect):
                dano = 5 if self.origem == "enemy" else 15
                ent.tomar_dano(dano, mapa_obj)
                if ent.hp <= 0 and ent != mapa_obj.jogador:
                    mapa_obj.jogador.ganhar_xp(ent.xp_reward)
                    if ent in mapa_obj.entidades: mapa_obj.entidades.remove(ent)
                self.active = False; return
                
        if self.life <= 0: self.active = False

    def draw(self, surface, camera_x, camera_y):
        pass # O Renderer desenha agora