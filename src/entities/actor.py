# src/entidades.py
import math
import random
import pygame
from graphics import config
from graphics import recursos
from entities import combat

class Entidade:
    def __init__(self, x, y, nome, hp, dano, xp_reward=0):
        # 1. Atributos Básicos
        self.x = float(x)
        self.y = float(y)
        self.nome = nome
        self.hp_max = hp
        self.hp = hp
        self.dano = dano
        # self.off_z removido

        # 2. Configurações de Nível
        self.xp = 0
        self.nivel = 1
        self.xp_proximo_nivel = 20
        self.xp_reward = xp_reward
        self.speed = 0.15 if nome == "Heroi" else 0.04

        # 3. Cooldowns
        self.cooldown_tiro = 0
        self.cooldown_espada = 0

        # 4. Configuração Visual (Simplificada)
        # Mantemos offset_x/y apenas para ajuste fino de sprite (centralizar desenho), não altura
        configs_visuais = {
            "Heroi":      { "sombra": 1.2, "ajuste_x": 0, "ajuste_y": 0 }, 
            "Orc":        { "sombra": 1.0, "ajuste_x": 0, "ajuste_y": 0 },
            "Troll":      { "sombra": 2.0, "ajuste_x": 0, "ajuste_y": 0 },
            "REI TROLL":  { "sombra": 3.0, "ajuste_x": 0, "ajuste_y": 0 },
            "Arvore":     { "sombra": 1.5, "ajuste_x": -2, "ajuste_y": 0 }, # Exemplo de ajuste lateral
            "RedTree":    { "sombra": 1.5, "ajuste_x": 0, "ajuste_y": 0 },
        }

        dados = configs_visuais.get(nome, { "sombra": 1.0, "ajuste_x": 0, "ajuste_y": 0 })
        self.scale_sombra = dados["sombra"]
        self.offset_x = dados["ajuste_x"]
        self.offset_y = dados["ajuste_y"]

        # 5. Hitbox
        self.largura_hb = 0.6 
        self.altura_hb = 0.4 
        self.hitbox = pygame.Rect(0, 0, 0, 0)

        # 6. Sprites
        key = "orc_run"
        if nome == "Heroi": key = "llama_run"
        elif nome == "Troll": key = "troll_run"
        elif nome == "REI TROLL": key = "boss_run"
        elif nome == "Arvore": key = "tree"
        elif nome == "RedTree": key = "red_tree"

        self.frames = recursos.SPRITES.get(key)
        self.frame_index = 0.0
        self.image = self.frames[0] if self.frames else None
        self.moving = False

        self.atualizar_hitbox()

    def atualizar_hitbox(self):
        tamanho = config.TAMANHO_TILE
        largura = int(tamanho * self.largura_hb)
        altura = int(tamanho * self.altura_hb)

        if self.hitbox.width != largura or self.hitbox.height != altura:
            self.hitbox.size = (largura, altura)
        
        px_x = self.x * tamanho
        px_y = self.y * tamanho

        # Simples: Centro do tile + ajuste lateral visual, Base do tile
        self.hitbox.centerx = int(px_x + (tamanho // 2))
        self.hitbox.bottom = int(px_y + tamanho)

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
        if self.speed == 0: return 
        if self.moving and self.frames:
            self.frame_index += config.VELOCIDADE_ANIMACAO
            if self.frame_index >= len(self.frames): 
                self.frame_index = 0
            self.image = self.frames[int(self.frame_index)]
        elif self.frames:
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

    def update(self, mapa_obj):
        if self.cooldown_tiro > 0: self.cooldown_tiro -= 1
        if self.cooldown_espada > 0: self.cooldown_espada -= 1
        
        # Não verificamos mais z-level aqui
        self.atualizar_hitbox()
        self.animar()

    def update_ia(self, mapa_obj):
        # (Mesma lógica de antes)
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

class ObjetoDestrutivel(Entidade):
    def __init__(self, x, y, nome, hp):
        super().__init__(x, y, nome, hp, dano=0, xp_reward=5)
        self.speed = 0 
        self.sombra_cache = None
        
    def update_ia(self, mapa_obj):
        pass