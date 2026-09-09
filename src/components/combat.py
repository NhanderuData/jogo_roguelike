import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DamageResult:
    requested: int
    absorbed: int
    health_damage: int
    critical: bool = False


# src/components/combat.py

class CombatComponent:
    def __init__(self, entity, hp_max, damage, xp_reward=0):
        self.entity = entity
        self.hp_max = hp_max
        self.hp = hp_max
        self.damage = damage
        self.dead = False
        self.armor = 0
        self.max_armor = 100
        
        # --- FOME (NOVO) ---
        self.fome = 100
        self.max_fome = 100
        self.fome_timer = 0 # Contador para diminuir a fome
        
        # XP e Nível
        self.xp = 0
        self.level = 1
        self.next_level_xp = 20
        self.xp_reward = xp_reward
        
        # Cooldowns
        self.cooldown_sword = 0
        self.cooldown_shoot = 0

    def take_damage(self, amount, map_obj=None, critical=False):
        amount = max(0, int(amount))
        if self.dead:
            return DamageResult(amount, 0, 0, critical)
        requested = amount
        absorbed = min(self.armor, amount)
        self.armor -= absorbed
        amount -= absorbed
        health_damage = amount
        self.hp -= health_damage
        
        if hasattr(self.entity, 'sprite') and self.entity.sprite:
            self.entity.sprite.dano_timer = 0.12

        if map_obj and self.entity is getattr(map_obj, "jogador", None):
            camera = getattr(map_obj, "camera", None)
            if camera:
                camera.add_trauma(min(0.55, 0.12 + requested / 100))
            
        if map_obj:
            if critical and health_damage:
                map_obj.criar_texto_dano(
                    self.entity.x, self.entity.y, f"CRÍTICO! {health_damage}", (255, 220, 70)
                )
            elif health_damage:
                map_obj.criar_texto_dano(self.entity.x, self.entity.y, health_damage)
            elif absorbed:
                map_obj.criar_texto_dano(
                    self.entity.x, self.entity.y, "BLOQUEADO", (90, 205, 255)
                )

        if self.hp <= 0:
            self.hp = 0
            self.dead = True
        return DamageResult(requested, absorbed, health_damage, critical)

    def heal(self, amount):
        self.hp += amount
        if self.hp > self.hp_max: self.hp = self.hp_max

    def add_armor(self, amount):
        self.armor = min(self.max_armor, self.armor + amount)

    def gain_xp(self, amount):
        self.xp += amount
        while self.xp >= self.next_level_xp:
            self._level_up()

    def _level_up(self):
        self.xp -= self.next_level_xp
        self.level += 1
        self.hp_max += 10
        self.hp = self.hp_max
        self.damage += 1
        self.next_level_xp = int(self.next_level_xp * 1.5)
        logger.info("%s reached level %s", self.entity.nome, self.level)

    def update(self, dt):
        self.cooldown_shoot = max(0.0, self.cooldown_shoot - dt)
        self.cooldown_sword = max(0.0, self.cooldown_sword - dt)
