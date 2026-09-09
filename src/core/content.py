from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Mapping

from core.paths import DATA_DIR


@dataclass(frozen=True)
class ItemDefinition:
    kind: str
    value: int
    color: tuple[int, int, int]
    sprite: str
    effect: str | None = None
    ammo_type: str | None = None
    weapon_id: str | None = None
    duration: float = 0.0


@dataclass(frozen=True)
class WeaponDefinition:
    name: str
    kind: str
    damage: int
    cooldown: float
    sprite: str
    sound: str
    projectile_speed: float = 0.3
    pellets: int = 1
    spread: float = 0.0
    magazine_size: int = 0
    reload_time: float = 0.0
    ammo_type: str | None = None
    melee_range: float = 1.0
    critical_chance: float = 0.0
    critical_multiplier: float = 1.5
    slot: int = 0
    unlocked_by_default: bool = False


@dataclass(frozen=True)
class EntityDefinition:
    hp: int
    damage: int
    xp: int
    speed: float
    sprite: str
    has_ai: bool
    top_layer: bool
    is_static: bool = False
    impact_material: str = "flesh"
    role: str = "enemy"
    ai_mode: str = "melee"
    ranged_interval: float = 1.8
    tags: tuple[str, ...] = ()
    loot: tuple[str, ...] = ()
    loot_chance: float = 0.0


class ContentCatalog:
    """Validated, read-only gameplay definitions loaded from data files."""

    def __init__(
        self,
        items: Mapping[str, ItemDefinition],
        entities: Mapping[str, EntityDefinition],
        weapons: Mapping[str, WeaponDefinition] | None = None,
    ):
        self.items = dict(items)
        self.entities = dict(entities)
        self.weapons = dict(weapons or {})
        self._validate_references()

    @classmethod
    def load_default(cls) -> "ContentCatalog":
        return cls.from_directory(DATA_DIR)

    @classmethod
    def from_directory(cls, directory: Path) -> "ContentCatalog":
        items_raw = cls._read_json(directory / "items.json")
        entities_raw = cls._read_json(directory / "entities.json")
        weapons_raw = cls._read_json(directory / "weapons.json", optional=True)

        items = {
            name: ItemDefinition(
                kind=cls._required(data, "type", name),
                value=int(cls._required(data, "value", name)),
                color=cls._color(cls._required(data, "color", name), name),
                sprite=cls._required(data, "sprite", name),
                effect=data.get("effect"),
                ammo_type=data.get("ammo_type"),
                weapon_id=data.get("weapon_id"),
                duration=float(data.get("duration", 0.0)),
            )
            for name, data in items_raw.items()
        }
        entities = {
            name: EntityDefinition(
                hp=int(cls._required(data, "hp", name)),
                damage=int(cls._required(data, "damage", name)),
                xp=int(cls._required(data, "xp", name)),
                speed=float(cls._required(data, "speed", name)),
                sprite=cls._required(data, "sprite", name),
                has_ai=cls._boolean(data.get("ai", True), name, "ai"),
                top_layer=cls._boolean(
                    data.get("top_layer", False), name, "top_layer"
                ),
                is_static=cls._boolean(
                    data.get("static", False), name, "static"
                ),
                impact_material=str(data.get("impact_material", "flesh")),
                role=str(data.get("role", "enemy")),
                ai_mode=str(data.get("ai_mode", "melee")),
                ranged_interval=float(data.get("ranged_interval", 1.8)),
                tags=cls._string_list(data.get("tags", []), name, "tags"),
                loot=cls._string_list(data.get("loot", []), name, "loot"),
                loot_chance=float(data.get("loot_chance", 0.0)),
            )
            for name, data in entities_raw.items()
        }
        weapons = {
            weapon_id: WeaponDefinition(
                name=cls._required(data, "name", weapon_id),
                kind=cls._required(data, "type", weapon_id),
                damage=int(cls._required(data, "damage", weapon_id)),
                cooldown=float(cls._required(data, "cooldown", weapon_id)),
                sprite=cls._required(data, "sprite", weapon_id),
                sound=cls._required(data, "sound", weapon_id),
                projectile_speed=float(data.get("projectile_speed", 0.3)),
                pellets=int(data.get("pellets", 1)),
                spread=float(data.get("spread", 0.0)),
                magazine_size=int(data.get("magazine_size", 0)),
                reload_time=float(data.get("reload_time", 0.0)),
                ammo_type=data.get("ammo_type"),
                melee_range=float(data.get("melee_range", 1.0)),
                critical_chance=float(data.get("critical_chance", 0.0)),
                critical_multiplier=float(data.get("critical_multiplier", 1.5)),
                slot=int(data.get("slot", 0)),
                unlocked_by_default=cls._boolean(
                    data.get("unlocked_by_default", False),
                    weapon_id,
                    "unlocked_by_default",
                ),
            )
            for weapon_id, data in weapons_raw.items()
        }
        return cls(items, entities, weapons)

    @staticmethod
    def _read_json(path: Path, optional: bool = False) -> Dict[str, Dict[str, Any]]:
        try:
            with path.open(encoding="utf-8") as file:
                data = json.load(file)
        except FileNotFoundError as exc:
            if optional:
                return {}
            raise RuntimeError(f"Content file not found: {path}") from exc
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Invalid JSON in content file {path}: {exc}") from exc

        if not isinstance(data, dict):
            raise RuntimeError(f"Content file must contain an object: {path}")
        return data

    @staticmethod
    def _required(data: Mapping[str, Any], field: str, name: str) -> Any:
        if field not in data:
            raise RuntimeError(f"Content '{name}' is missing required field '{field}'")
        return data[field]

    @staticmethod
    def _color(value: Any, name: str) -> tuple[int, int, int]:
        if not isinstance(value, list) or len(value) != 3:
            raise RuntimeError(f"Content '{name}' has an invalid RGB color")
        color = tuple(int(channel) for channel in value)
        if any(channel < 0 or channel > 255 for channel in color):
            raise RuntimeError(f"Content '{name}' has an RGB channel outside 0..255")
        return color

    @staticmethod
    def _boolean(value: Any, name: str, field: str) -> bool:
        if not isinstance(value, bool):
            raise RuntimeError(f"Content '{name}' has a non-boolean '{field}'")
        return value

    @staticmethod
    def _string_list(value: Any, name: str, field: str) -> tuple[str, ...]:
        if not isinstance(value, list) or not all(
            isinstance(item, str) for item in value
        ):
            raise RuntimeError(f"Content '{name}' has an invalid '{field}' list")
        return tuple(value)

    def _validate_references(self) -> None:
        valid_item_kinds = {
            "comida", "bebida", "cura", "cura_status", "energia",
            "armadura", "arma", "municao",
        }
        for name, item in self.items.items():
            if item.kind not in valid_item_kinds:
                raise RuntimeError(f"Item '{name}' has unknown type '{item.kind}'")
            if item.value < 0 or item.duration < 0:
                raise RuntimeError(f"Item '{name}' has negative numeric values")

        for name, entity in self.entities.items():
            if entity.hp <= 0 or entity.damage < 0 or entity.speed < 0:
                raise RuntimeError(f"Entity '{name}' has invalid combat values")
            if not 0.0 <= entity.loot_chance <= 1.0:
                raise RuntimeError(f"Entity '{name}' has invalid loot_chance")
            if entity.role not in {"player", "enemy", "prop"}:
                raise RuntimeError(f"Entity '{name}' has unknown role '{entity.role}'")
            if entity.ai_mode not in {"melee", "ranged", "hybrid"}:
                raise RuntimeError(
                    f"Entity '{name}' has unknown ai_mode '{entity.ai_mode}'"
                )
            if entity.ranged_interval <= 0:
                raise RuntimeError(f"Entity '{name}' has invalid ranged_interval")

        for weapon_id, weapon in self.weapons.items():
            if weapon.kind not in {"ranged", "melee"}:
                raise RuntimeError(
                    f"Weapon '{weapon_id}' has unknown type '{weapon.kind}'"
                )
            if weapon.damage < 0 or weapon.cooldown < 0:
                raise RuntimeError(f"Weapon '{weapon_id}' has invalid combat values")
            if weapon.kind == "ranged" and (
                weapon.projectile_speed <= 0 or weapon.magazine_size <= 0
            ):
                raise RuntimeError(f"Ranged weapon '{weapon_id}' is incomplete")
            if weapon.kind == "melee" and weapon.melee_range <= 0:
                raise RuntimeError(f"Melee weapon '{weapon_id}' has invalid range")
            if weapon.slot < 0:
                raise RuntimeError(f"Weapon '{weapon_id}' has invalid slot")

        slots = [weapon.slot for weapon in self.weapons.values()]
        if len(slots) != len(set(slots)):
            raise RuntimeError("Weapon slots must be unique")

        valid_materials = {"flesh", "wood", "stone", "metal", "water"}
        invalid_materials = {
            entity.impact_material
            for entity in self.entities.values()
            if entity.impact_material not in valid_materials
        }
        if invalid_materials:
            names = ", ".join(sorted(invalid_materials))
            raise RuntimeError(f"Entities use unknown impact materials: {names}")

        unknown = {
            item
            for entity in self.entities.values()
            for item in entity.loot
            if item not in self.items
        }
        if unknown:
            names = ", ".join(sorted(unknown))
            raise RuntimeError(f"Entity loot references unknown items: {names}")

        unknown_weapons = {
            item.weapon_id
            for item in self.items.values()
            if item.weapon_id and item.weapon_id not in self.weapons
        }
        if unknown_weapons:
            names = ", ".join(sorted(unknown_weapons))
            raise RuntimeError(f"Items reference unknown weapons: {names}")
