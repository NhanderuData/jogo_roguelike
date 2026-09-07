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


@dataclass(frozen=True)
class EntityDefinition:
    hp: int
    damage: int
    xp: int
    speed: float
    sprite: str
    has_ai: bool
    top_layer: bool
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
                has_ai=bool(data.get("ai", True)),
                top_layer=bool(data.get("top_layer", False)),
                loot=tuple(data.get("loot", [])),
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

    def _validate_references(self) -> None:
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
