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
    def __init__(self, x, y, angle, origem):
        self.name = "Projetil"
        self.origem = origem # "player" ou "enemy"
        self.active = True
        self.life = 100
        
        # 1. Componente de Física (Gerencia Movimento e Colisão com Parede)
        # Usamos uma hitbox pequena (0.4 tile)
        self.physics = PhysicsComponent(self, x, y, largura_hb=0.4, altura_hb=0.4)
        self.physics.speed = 0.3
        
        # Vetor de movimento
        self.dx = math.cos(angle)
        self.dy = math.sin(angle)
        
        # 2. Componente Visual (Gerencia Imagem e Renderização)
        # Layer Aéreo para desenhar por cima de chão e buracos
        self.sprite = SpriteComponent(self, "shoot", layer=config.LAYER_AEREO)

    # --- PROXIES (Para compatibilidade com o Renderer atual) ---
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
        # 1. Movimento via Física
        old_x, old_y = self.x, self.y
        
        # O physics.move já cuida de não entrar em paredes!
        self.physics.move(self.dx, self.dy, mapa_obj)
        
        # Se tentou mover mas a posição não mudou, bateu na parede
        if abs(self.x - old_x) < 0.001 and abs(self.y - old_y) < 0.001:
            self.active = False
            return

        # 2. Atualiza Visual
        self.sprite.update(0)
        self.life -= 1
        if self.life <= 0: self.active = False

        # 3. Lógica de Dano (Hitbox contra Entidades)
        # Mantemos a verificação manual aqui pois projéteis têm regras específicas
        proj_rect = Hitbox(self.x * 32, self.y * 32, 12, 12)
        
        targets = [mapa_obj.jogador] if self.origem == "enemy" else [e for e in mapa_obj.entidades if e != mapa_obj.jogador]
        
        for ent in targets:
            ent_rect = Hitbox(ent.x * 32, ent.y * 32, 32, 32)
            
            if proj_rect.colliderect(ent_rect):
                dano = 5 if self.origem == "enemy" else 15
                
                # Chama o método da entidade (que usa o CombatComponent internamente)
                ent.tomar_dano(dano, mapa_obj)
                
                # Lógica de XP
                if ent.hp <= 0 and ent != mapa_obj.jogador:
                    mapa_obj.jogador.ganhar_xp(ent.xp_reward)
                    if ent in mapa_obj.entidades: mapa_obj.entidades.remove(ent)
                
                self.active = False
                return

    def draw(self, surface, cx, cy):
        pass # O Renderer desenha automaticamente agora

# --- FUNÇÕES FACTORY (Geradores) ---

def criar_projetil(x, y, tx, ty, origem, mapa_obj):
    angle = math.atan2(ty - y, tx - x)
    # Cria a nova classe Projetil refatorada
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
            # Usa o Dano vindo do CombatComponent do atacante
            alvo.tomar_dano(atacante.dano * 2, mapa_obj)
            
            # Knockback: Empurra usando o sistema de física do alvo
            alvo.physics.move(math.cos(angle) * 0.5, math.sin(angle) * 0.5, mapa_obj)
            
            acertou = True
            if alvo.hp <= 0:
                atacante.ganhar_xp(alvo.xp_reward)
                if alvo in mapa_obj.entidades: mapa_obj.entidades.remove(alvo)
    return acertou