import math
import random
import pygame
from core import config
from graphics import recursos
from systems import combat_system
from components.physics import PhysicsComponent
from components.sprite import SpriteComponent

class Entidade:
    def __init__(self, x, y, nome, hp, dano, xp_reward=0):
        self.nome = nome
        
        # --- COMPONENTES ---
        self.physics = PhysicsComponent(self, x, y)
        
        # Define a key do sprite baseado no nome (Lógica simplificada)
        sprite_key = "orc_run"
        if nome == "Heroi": sprite_key = "llama_run"
        elif nome == "Troll": sprite_key = "troll_run"
        elif nome == "REI TROLL": sprite_key = "boss_run"
        elif nome == "Arvore": sprite_key = "tree"
        elif nome == "RedTree": sprite_key = "red_tree"
        elif nome == "Cipreste": sprite_key = "cipreste"
        
        self.sprite = SpriteComponent(self, sprite_key)
        
        # --- ATRIBUTOS DE RPG ---
        self.hp_max = hp
        self.hp = hp
        self.dano = dano
        self.xp = 0
        self.nivel = 1
        self.xp_proximo_nivel = 20
        self.xp_reward = xp_reward
        self.cooldown_tiro = 0
        self.cooldown_espada = 0

        # Configura velocidade na física
        base_speed = 0.15 if nome == "Heroi" else 0.04
        self.physics.speed = base_speed

    # --- PROXIES DE FÍSICA ---
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

    # --- PROXIES VISUAIS (Para manter compatibilidade temporária) ---
    @property
    def image(self): return self.sprite.image
    
    @property
    def offset_x(self): return self.sprite.offset_x
    
    @property
    def offset_y(self): return self.sprite.offset_y
    
    @property
    def sombra_cache(self): 
        # Pequeno hack para guardar o cache da sombra no componente
        if not hasattr(self.sprite, 'sombra_cache'): self.sprite.sombra_cache = None
        return self.sprite.sombra_cache
    @sombra_cache.setter
    def sombra_cache(self, val): self.sprite.sombra_cache = val


    def tomar_dano(self, qtd, mapa_obj=None):
        self.hp -= qtd
        if mapa_obj:
            mapa_obj.criar_texto_dano(self.x, self.y, int(qtd))
        # Efeito visual de dano
        if hasattr(self.sprite, 'dano_timer'):
             self.sprite.dano_timer = 5 # Flash branco por 5 frames

    def ganhar_xp(self, qtd):
        self.xp += qtd
        if self.xp >= self.xp_proximo_nivel:
            self.xp -= self.xp_proximo_nivel
            self.nivel += 1
            self.hp_max += 10
            self.hp = self.hp_max
            self.xp_proximo_nivel = int(self.xp_proximo_nivel * 1.5)

    def atirar(self, tx, ty, mapa_obj, origem):
        if self.cooldown_tiro > 0: return
        combat_system.criar_projetil(self.x, self.y, tx, ty, origem, mapa_obj)
        self.cooldown_tiro = 40 

    def atacar_espada(self, tx, ty, mapa_obj):
        if self.cooldown_espada > 0: return
        combat_system.executar_golpe_espada(self, tx, ty, mapa_obj)
        self.cooldown_espada = 30 

    def update(self, mapa_obj):
        if self.cooldown_tiro > 0: self.cooldown_tiro -= 1
        if self.cooldown_espada > 0: self.cooldown_espada -= 1
        
        # Atualiza componentes
        self.physics.update(0) # (dt não usado na física ainda)
        self.sprite.update(0)

    def update_ia(self, mapa_obj):
        if self.nome == "Heroi" or self.physics.speed == 0: return 
        player = mapa_obj.jogador
        dist = ((self.x - player.x)**2 + (self.y - player.y)**2)**0.5
        
        if 0.8 < dist < 10: 
            dx = (player.x - self.x) / dist
            dy = (player.y - self.y) / dist
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
        self.physics.speed = 0 
        
    def update_ia(self, mapa_obj):
        pass