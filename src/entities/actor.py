# src/entities/actor.py
import math
import random
import pygame
from core import config
from graphics import recursos
from entities import combat
# Importe o novo componente
from components.physics import PhysicsComponent

class Entidade:
    def __init__(self, x, y, nome, hp, dano, xp_reward=0):
        self.nome = nome
        
        # --- NOVO: SISTEMA DE COMPONENTES ---
        # A Entidade agora possui um componente de física
        self.physics = PhysicsComponent(self, x, y)
        
        # Propriedades "Proxy" para manter compatibilidade com o código antigo
        # (Isso permite que self.x funcione acessando self.physics.x)
        # Nota: Idealmente removeremos isso no futuro, mas ajuda na transição.
        
        self.hp_max = hp
        self.hp = hp
        self.dano = dano
        
        # ... (Mantém XP, Nivel, Cooldowns iguais) ...
        self.xp = 0
        self.nivel = 1
        self.xp_proximo_nivel = 20
        self.xp_reward = xp_reward
        self.cooldown_tiro = 0
        self.cooldown_espada = 0

        # Velocidade agora é controlada no componente, mas configuramos aqui
        base_speed = 0.15 if nome == "Heroi" else 0.04
        self.physics.speed = base_speed

        # ... (Configuração Visual mantém igual por enquanto) ...
        configs_visuais = {
            "Heroi":      { "sombra": 1.2, "ajuste_x": 0, "ajuste_y": 0 }, 
            "Orc":        { "sombra": 1.0, "ajuste_x": 0, "ajuste_y": 0 },
            "Troll":      { "sombra": 2.0, "ajuste_x": 0, "ajuste_y": 0 },
            "REI TROLL":  { "sombra": 3.0, "ajuste_x": 0, "ajuste_y": 0 },
            "Arvore":     { "sombra": 1.5, "ajuste_x": -2, "ajuste_y": 0 },
            "RedTree":    { "sombra": 1.5, "ajuste_x": 0, "ajuste_y": 0 },
            "Cipreste":   { "sombra": 1.5, "ajuste_x": -2, "ajuste_y": 0 },
        }
        dados = configs_visuais.get(nome, { "sombra": 1.0, "ajuste_x": 0, "ajuste_y": 0 })
        self.scale_sombra = dados["sombra"]
        self.offset_x = dados["ajuste_x"]
        self.offset_y = dados["ajuste_y"]

        # ... (Sprites mantêm igual) ...
        key = "orc_run"
        if nome == "Heroi": key = "llama_run"
        elif nome == "Troll": key = "troll_run"
        elif nome == "REI TROLL": key = "boss_run"
        elif nome == "Arvore": key = "tree"
        elif nome == "RedTree": key = "red_tree"
        elif nome == "Cipreste": key = "cipreste"
        
        self.frames = recursos.SPRITES.get(key)
        self.frame_index = 0.0
        self.image = self.frames[0] if self.frames else None

    # --- PROPRIEDADES (GETTERS/SETTERS MÁGICOS) ---
    # Isso faz com que quando alguém peça 'entidade.x', ele pegue 'entidade.physics.x'
    @property
    def x(self): return self.physics.x
    @x.setter
    def x(self, value): self.physics.x = value

    @property
    def y(self): return self.physics.y
    @y.setter
    def y(self, value): self.physics.y = value
    
    @property
    def hitbox(self): return self.physics.hitbox
    
    @property
    def moving(self): return self.physics.moving
    @moving.setter
    def moving(self, value): self.physics.moving = value
    
    @property
    def speed(self): return self.physics.speed
    @speed.setter
    def speed(self, value): self.physics.speed = value

    # ... (Métodos de Combate/Dano mantêm igual por enquanto) ...
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
        # self.moving = False # Removido, o PhysicsComponent cuida disso

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
        
        # Hitbox atualizada pelo componente
        # Animação ainda aqui
        self.animar()

    def update_ia(self, mapa_obj):
        if self.nome == "Heroi" or self.speed == 0: return 
        player = mapa_obj.jogador
        dist = ((self.x - player.x)**2 + (self.y - player.y)**2)**0.5
        
        if 0.8 < dist < 10: 
            dx = (player.x - self.x) / dist
            dy = (player.y - self.y) / dist
            
            # --- USO DO NOVO COMPONENTE ---
            # Em vez de calcular nx/ny manualmente, pedimos ao componente mover
            self.physics.move(dx, dy, mapa_obj)

        if dist < 8:
            if dist < 1.5:
                self.atacar_espada(player.x, player.y, mapa_obj)
            elif dist > 3 and ("Troll" in self.nome or "REI" in self.nome):
                if random.randint(0, 100) < 5:
                    self.atirar(player.x, player.y, mapa_obj, "enemy")

class ObjetoDestrutivel(Entidade):
    def __init__(self, x, y, nome, hp):
        super().__init__(x, y, nome, hp, dano=0, xp_reward=5)
        self.physics.speed = 0 # Garante que não move
        self.sombra_cache = None
        
    def update_ia(self, mapa_obj):
        pass