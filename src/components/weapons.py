from __future__ import annotations

import random

from components import combat_system
from core.audio import SoundManager
from core.content import ContentCatalog, WeaponDefinition


class WeaponComponent:
    SLOT_ORDER = ("pistol", "shotgun", "smg", "machete")

    def __init__(self, owner, content: ContentCatalog, audio: SoundManager):
        self.owner = owner
        self.content = content
        self.audio = audio
        self.unlocked = {"pistol", "shotgun", "machete"}
        self.current_id = "pistol"
        self.magazines = {
            weapon_id: definition.magazine_size
            for weapon_id, definition in content.weapons.items()
        }
        self.cooldown = 0.0
        self.reload_remaining = 0.0
        self.reload_total = 0.0

    @property
    def current(self) -> WeaponDefinition:
        return self.content.weapons[self.current_id]

    @property
    def is_reloading(self) -> bool:
        return self.reload_remaining > 0

    @property
    def reload_progress(self) -> float:
        if not self.is_reloading or self.reload_total <= 0:
            return 0.0
        return 1.0 - self.reload_remaining / self.reload_total

    def unlock(self, weapon_id: str) -> bool:
        if weapon_id not in self.content.weapons or weapon_id in self.unlocked:
            return False
        self.unlocked.add(weapon_id)
        self.current_id = weapon_id
        self.audio.play("pickup")
        return True

    def select_slot(self, slot_index: int) -> bool:
        if not 0 <= slot_index < len(self.SLOT_ORDER):
            return False
        weapon_id = self.SLOT_ORDER[slot_index]
        if weapon_id not in self.unlocked:
            return False
        self.current_id = weapon_id
        self.reload_remaining = 0.0
        self.audio.play("reload", 0.35)
        return True

    def start_reload(self) -> bool:
        weapon = self.current
        if weapon.kind != "ranged" or self.is_reloading:
            return False
        current_ammo = self.magazines[self.current_id]
        reserve = self.owner.inventory.ammo_count(weapon.ammo_type)
        if current_ammo >= weapon.magazine_size or reserve <= 0:
            return False
        self.reload_total = weapon.reload_time
        self.reload_remaining = weapon.reload_time
        self.audio.play("reload")
        return True

    def update(self, dt: float) -> None:
        self.cooldown = max(0.0, self.cooldown - dt)
        if not self.is_reloading:
            return
        self.reload_remaining = max(0.0, self.reload_remaining - dt)
        if self.reload_remaining == 0:
            self._finish_reload()

    def _finish_reload(self) -> None:
        weapon = self.current
        missing = weapon.magazine_size - self.magazines[self.current_id]
        loaded = self.owner.inventory.consume_ammo(weapon.ammo_type, missing)
        self.magazines[self.current_id] += loaded

    def attack(self, target_x: float, target_y: float, map_obj) -> bool:
        if self.cooldown > 0 or self.is_reloading:
            return False

        weapon = self.current
        if weapon.kind == "melee":
            combat_system.executar_golpe_espada(
                self.owner,
                target_x,
                target_y,
                map_obj,
                damage=weapon.damage,
                alcance=weapon.melee_range,
            )
            self.cooldown = weapon.cooldown
            self.audio.play(weapon.sound)
            return True

        if self.magazines[self.current_id] <= 0:
            if not self.start_reload():
                self.audio.play("empty")
            return False

        self.magazines[self.current_id] -= 1
        for _ in range(weapon.pellets):
            combat_system.criar_projetil(
                self.owner.x,
                self.owner.y,
                target_x,
                target_y,
                "player",
                map_obj,
                dono=self.owner,
                damage=weapon.damage,
                speed=weapon.projectile_speed,
                angle_offset=random.uniform(-weapon.spread, weapon.spread),
            )
        self.cooldown = weapon.cooldown
        self.audio.play(weapon.sound)
        return True
