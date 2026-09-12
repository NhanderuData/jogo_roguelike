from core import config
from components import combat_system
# Importe todos os componentes
from components.physics import PhysicsComponent
from components.sprite import SpriteComponent
from components.ai import AIComponent
from components.combat import CombatComponent
from components.inventory import InventoryComponent
from components.status import StatusComponent
from components.weapons import WeaponComponent
from core.context import GameContext

class Entidade:
    def __init__(self, x, y, nome, context: GameContext, rng=None):
        self.nome = nome
        self.context = context
        self.content = context.content
        
        if nome not in self.content.entities:
            raise ValueError(f"Definição de entidade inexistente: {nome}")

        dados = self.content.entities[nome]
        self.is_static = dados.is_static
        self.impact_material = dados.impact_material
        self.role = dados.role
        self.tags = frozenset(dados.tags)
        self.ai_mode = dados.ai_mode
        self.ranged_interval = dados.ranged_interval
        # --- 1. FÍSICA ---
        self.physics = PhysicsComponent(self, x, y)
        self.physics.speed = dados.speed

        # Capacidades do jogador são definidas pelo papel no catálogo.
        if self.role == "player":
            # Inventário já existia aqui
            self.inventory = InventoryComponent(self.content)
            self.weapons = WeaponComponent(self, self.content, context.audio)
            self.inventory.add_item("Bandagem", 2)
            self.inventory.add_item("Enlatado", 1)
            self.inventory.add_item("Garrafa d'Agua", 1)
            self.inventory.add_item("Energético", 1)
            self.inventory.add_item("Colete Tático", 1)
            self.inventory.add_item("Munição 9mm", 4)
            self.inventory.add_item("Cartuchos calibre 12", 2)
            
            # Novo Sistema de Sobrevivência
            self.status = StatusComponent(self) 
        else:
            self.inventory = None
            self.weapons = None
            self.status = None

        # --- 2. VISUAL ---
        sprite_key = dados.sprite
        
        # Define a layer (chão, corpo ou topo) automaticamente
        layer = config.LAYER_CORPO
        if dados.top_layer:
            layer = config.LAYER_TOPO
            
        self.sprite = SpriteComponent(self, sprite_key, layer=layer)
        
        # --- 3. COMBATE ---
        self.combat = CombatComponent(
            self, 
            hp_max=dados.hp,
            damage=dados.damage,
            xp_reward=dados.xp,
        )
        
        # --- 4. INTELIGÊNCIA ARTIFICIAL ---
        self.ai = AIComponent(self, rng=rng) if dados.has_ai else None


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
    def tomar_dano(self, qtd, mapa_obj=None, critical=False):
        hp_before = self.combat.hp
        result = self.combat.take_damage(qtd, mapa_obj, critical=critical)
        if self.role == "player" and self.combat.hp < hp_before:
            self.context.audio.play("hurt", 0.65)
        elif mapa_obj and hasattr(mapa_obj, "alert_allies") and self.role in ("enemy", "animal"):
            mapa_obj.alert_allies(self, radius=7.0)
        return result

    def ganhar_xp(self, qtd):
        self.combat.gain_xp(qtd)

    def atirar(self, tx, ty, mapa_obj, origem):
        if self.combat.cooldown_shoot > 0: return
        if origem == "enemy":
            # A IA fornece a posição do tile do jogador; mira no centro dele.
            tx += 0.5
            ty += 0.5
        combat_system.criar_projetil(self.x, self.y, tx, ty, origem, mapa_obj, dono=self)
        self.combat.cooldown_shoot = 10 / config.FPS

    def atacar_espada(self, tx, ty, mapa_obj):
        if self.combat.cooldown_sword > 0: return
        combat_system.executar_golpe_espada(self, tx, ty, mapa_obj)
        self.combat.cooldown_sword = 30 / config.FPS

    def update(self, dt, mapa_obj):
        # Atualiza TODOS os sistemas da entidade
        self.physics.update(dt)
        self.sprite.update(dt)
        self.combat.update(dt)
        if self.weapons:
            self.weapons.update(dt)
        if self.status:
            self.status.update(dt)
        
        # A IA decide se move ou ataca
        if self.ai:
            self.ai.update(mapa_obj, dt)
