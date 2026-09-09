from __future__ import annotations

import random

from components import combat_system
from core.audio import AudioService
from core.content import ContentCatalog, WeaponDefinition


class WeaponComponent:
    def __init__(self, owner, content: ContentCatalog, audio: AudioService):
        self.owner = owner
        self.content = content
        self.audio = audio
        self.slot_order = tuple(
            sorted(content.weapons, key=lambda key: content.weapons[key].slot)
        )
        self.unlocked = {
            weapon_id
            for weapon_id, definition in content.weapons.items()
            if definition.unlocked_by_default
        }
        if not self.unlocked:
            raise ValueError("At least one weapon must be unlocked by default")
        self.current_id = next(
            weapon_id for weapon_id in self.slot_order if weapon_id in self.unlocked
        )
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
        if not 0 <= slot_index < len(self.slot_order):
            return False
        weapon_id = self.slot_order[slot_index]
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
                critical_chance=weapon.critical_chance,
                critical_multiplier=weapon.critical_multiplier,
            )
            self.cooldown = weapon.cooldown
            self.audio.play(weapon.sound)
            return True

        if self.magazines[self.current_id] <= 0:
            if not self.start_reload():
                self.audio.play("empty")
            return False

        self.magazines[self.current_id] -= 1
        rng = getattr(map_obj, "gameplay_rng", random)
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
                angle_offset=rng.uniform(-weapon.spread, weapon.spread),
                critical_chance=weapon.critical_chance,
                critical_multiplier=weapon.critical_multiplier,
            )
        combat_system.criar_feedback_disparo(
            self.owner,
            target_x,
            target_y,
            map_obj,
            intensity=1.25 if weapon.pellets > 1 else 0.9,
        )
        self.cooldown = weapon.cooldown
        self.audio.play(weapon.sound)
        self.audio.play("casing", 0.16)
        camera = getattr(map_obj, "camera", None)
        if camera:
            recoil = min(0.28, 0.06 + weapon.damage * weapon.pellets / 260)
            camera.add_trauma(recoil)
        return True
