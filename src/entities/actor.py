import math
import random
import pygame
from core import config
from graphics import recursos
from components import combat_system
# Importe todos os componentes
from components.physics import PhysicsComponent
from components.sprite import SpriteComponent
from components.ai import AIComponent
from components.combat import CombatComponent
from components.inventory import InventoryComponent
# --- NOVO IMPORT ESSENCIAL ---
from core.game_data import DATA_INIMIGOS 

class Entidade:
    # A MÁGICA ESTÁ AQUI: Removemos hp, dano e xp do __init__
    def __init__(self, x, y, nome):
        self.nome = nome
        
        # Busca os dados no dicionário. Se não achar, usa o Orc como padrão
        dados = DATA_INIMIGOS.get(nome, DATA_INIMIGOS["Orc"])
        
        # --- 1. FÍSICA ---
        self.physics = PhysicsComponent(self, x, y)
        self.physics.speed = dados.get("speed", 0.04)

        if nome == "Heroi":
            self.inventory = InventoryComponent()
            # Itens iniciais para teste
            self.inventory.add_item("Poção de Cura", 3)
            self.inventory.add_item("Espada Velha", 1)
        else:
            self.inventory = None

        # --- 2. VISUAL ---
        sprite_key = dados.get("sprite", "orc_run")
        
        # Define a layer (chão, corpo ou topo) automaticamente
        layer = config.LAYER_CORPO
        if dados.get("layer_topo"):
            layer = config.LAYER_TOPO
            
        self.sprite = SpriteComponent(self, sprite_key, layer=layer)
        
        # --- 3. COMBATE ---
        # Pega HP e Dano do arquivo de dados
        self.combat = CombatComponent(
            self, 
            hp_max=dados.get("hp", 10), 
            damage=dados.get("dano", 1), 
            xp_reward=dados.get("xp", 0)
        )
        
        # --- 4. INTELIGÊNCIA ARTIFICIAL ---
        self.ai = AIComponent(self)
        # Desativa a IA se o dado disser que não tem (ex: Árvores)
        if not dados.get("ai", True):
            self.ai.active = False


    # --- PROXIES (Mantemos para compatibilidade) ---
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
    def image(self): return self.sprite.image
    @property
    def offset_x(self): return self.sprite.offset_x
    @property
    def offset_y(self): return self.sprite.offset_y

    @property
    def hp(self): return self.combat.hp
    @hp.setter
    def hp(self, val): self.combat.hp = val
    @property
    def hp_max(self): return self.combat.hp_max
    @hp_max.setter
    def hp_max(self, val): self.combat.hp_max = val
    @property
    def xp(self): return self.combat.xp
    @property
    def nivel(self): return self.combat.level
    @property
    def dano(self): return self.combat.damage
    @property
    def xp_reward(self): return self.combat.xp_reward
    @property
    def xp_proximo_nivel(self): return self.combat.next_level_xp

    # --- MÉTODOS DE AÇÃO ---
    def tomar_dano(self, qtd, mapa_obj=None):
        self.combat.take_damage(qtd, mapa_obj)

    def ganhar_xp(self, qtd):
        self.combat.gain_xp(qtd)

    def atirar(self, tx, ty, mapa_obj, origem):
        if self.combat.cooldown_shoot > 0: return
        combat_system.criar_projetil(self.x, self.y, tx, ty, origem, mapa_obj, dono=self)
        self.combat.cooldown_shoot = 10

    def atacar_espada(self, tx, ty, mapa_obj):
        if self.combat.cooldown_sword > 0: return
        combat_system.executar_golpe_espada(self, tx, ty, mapa_obj)
        self.combat.cooldown_sword = 30 

    def update(self, mapa_obj):
        # Atualiza TODOS os sistemas da entidade
        self.physics.update(0)
        self.sprite.update(0)
        self.combat.update(0)
        
        # A IA decide se move ou ataca
        self.ai.update(mapa_obj)