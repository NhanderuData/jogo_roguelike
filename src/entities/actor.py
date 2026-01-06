# src/entidades.py
import math
import random
import pygame
from graphics import config
from graphics import recursos
from entities import combat

class Entidade:
    def __init__(self, x, y, nome, hp, dano, xp_reward=0):
        # Agora X e Y representam o CENTRO do tile
        self.x = float(x)
        self.y = float(y)
        self.nome = nome
        self.hp_max = hp
        self.hp = hp
        self.dano = dano
        
        # Sistema de Colisão (Hitbox centralizada)
        self.largura_hb = 0.6 # Fração do tile (0.6 de 24px)
        self.altura_hb = 0.6
        self.hitbox = pygame.Rect(0, 0, 0, 0)
        self.atualizar_hitbox()
        
        # Level System
        self.xp = 0
        self.nivel = 1
        self.xp_proximo_nivel = 20
        self.xp_reward = xp_reward
        
        self.speed = 0.15 if nome == "Heroi" else 0.04
        
        # Cooldowns
        self.cooldown_tiro = 0
        self.cooldown_espada = 0

        # --- CONFIGURAÇÃO VISUAL CENTRALIZADA ---
        configs_visuais = {
            "Heroi":      { "sombra": 1.2, "ajuste_x": 0, "ajuste_y": 0 }, 
            "Orc":        { "sombra": 1.0, "ajuste_x": 0, "ajuste_y": 0 },
            "Troll":      { "sombra": 2.0, "ajuste_x": 0, "ajuste_y": 0 },
            "REI TROLL":  { "sombra": 3.0, "ajuste_x": 0, "ajuste_y": 0 },
            "Arvore":     { "sombra": 1.5, "ajuste_x": 0, "ajuste_y": 0 },
        }

        dados = configs_visuais.get(nome, { "sombra": 1.0, "ajuste_x": 0, "ajuste_y": 0 })
        
        self.scale_sombra = dados["sombra"]
        self.offset_x = dados["ajuste_x"]
        self.offset_y = dados["ajuste_y"] # Novo ajuste para centralização fina
        
        # Visual (Sprites)
        key = "orc_run"
        if nome == "Heroi": key = "llama_run"
        elif nome == "Troll": key = "troll_run"
        elif nome == "REI TROLL": key = "boss_run"
        elif nome == "Arvore": key = "tree"
        
        self.frames = recursos.SPRITES.get(key)
        self.frame_index = 0.0
        self.image = self.frames[0] if self.frames else None
        self.moving = False

    def atualizar_hitbox(self):
        tamanho = config.TAMANHO_TILE
        # Usamos round() para evitar que a hitbox fique sambando entre pixels
        px_x = round(self.x * tamanho)
        px_y = round(self.y * tamanho)
        
        # Hitbox um pouco menor que o tile para facilitar passar entre árvores
        largura = int(tamanho * 0.7)
        altura = int(tamanho * 0.7)
        
        self.hitbox = pygame.Rect(0, 0, largura, altura)
        # O centro da hitbox é o centro do tile (12, 12 se for 24px)
        self.hitbox.center = (px_x + tamanho // 2, px_y + tamanho // 2)

    def tomar_dano(self, qtd, mapa_obj=None):
        self.hp -= qtd
        if mapa_obj:
            mapa_obj.criar_texto_dano(self.x, self.y, int(qtd))

    def ganhar_xp(self, qtd):
        self.xp += qtd
        if self.xp >= self.xp_proximo_nivel:
            self.xp -= self.xp_proximo_nivel
            self.nivel += 1
            self.hp_max += 10
            self.hp = self.hp_max
            self.xp_proximo_nivel = int(self.xp_proximo_nivel * 1.5)

    def animar(self):
        # 1. Trava para Objetos Estáticos (Árvores)
        # Se a velocidade for 0, não mudamos o frame. 
        # Isso evita que o Renderer recalcule a sombra e destrua seu FPS.
        if self.speed == 0:
            return 

        # 2. Animação de Movimento (Lhama e Inimigos)
        if self.moving and self.frames:
            self.frame_index += config.VELOCIDADE_ANIMACAO
            if self.frame_index >= len(self.frames): 
                self.frame_index = 0
            self.image = self.frames[int(self.frame_index)]
            
        # 3. Estado de Repouso (Idle)
        elif self.frames:
            # Inimigos e Herói voltam para o frame 0 quando param
            self.frame_index = 0
            self.image = self.frames[0]
            
        self.moving = False

    def atirar(self, tx, ty, mapa_obj, origem):
        if self.cooldown_tiro > 0: return
        combat.criar_projetil(self.x, self.y, tx, ty, origem, mapa_obj)
        self.cooldown_tiro = 40 

    def atacar_espada(self, tx, ty, mapa_obj):
        if self.cooldown_espada > 0: return
        combat.executar_golpe_espada(self, tx, ty, mapa_obj)
        self.cooldown_espada = 30 

    def update(self):
        if self.cooldown_tiro > 0: self.cooldown_tiro -= 1
        if self.cooldown_espada > 0: self.cooldown_espada -= 1
        self.atualizar_hitbox()
        self.animar()

    def update_ia(self, mapa_obj):
        if self.nome == "Heroi" or self.speed == 0: return 

        player = mapa_obj.jogador
        dist = ((self.x - player.x)**2 + (self.y - player.y)**2)**0.5
        
        if 0.8 < dist < 10: 
            dx = (player.x - self.x) / dist
            dy = (player.y - self.y) / dist
            
            nx = self.x + dx * self.speed
            ny = self.y + dy * self.speed
            
            if not mapa_obj.is_blocked_terrain(nx, self.y): self.x = nx
            if not mapa_obj.is_blocked_terrain(self.x, ny): self.y = ny
            self.moving = True

        if dist < 8:
            if dist < 1.5:
                self.atacar_espada(player.x, player.y, mapa_obj)
            elif dist > 3 and ("Troll" in self.nome or "REI" in self.nome):
                if random.randint(0, 100) < 5:
                    self.atirar(player.x, player.y, mapa_obj, "enemy")

# --- CLASSE PARA OBJETOS DESTREUTÍVEIS (ÁRVORES) ---
class ObjetoDestrutivel(Entidade):
    def __init__(self, x, y, nome, hp):
        super().__init__(x, y, nome, hp, dano=0, xp_reward=5)
        self.speed = 0 # Árvores não andam
        self.sombra_cache = None
        
    def update_ia(self, mapa_obj):
        pass # Árvores não pensam
