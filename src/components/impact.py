from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ImpactProfile:
    particle: str
    sound: str
    color: tuple[int, int, int]


IMPACT_PROFILES = {
    "flesh": ImpactProfile("blood", "impact_flesh", (255, 210, 95)),
    "wood": ImpactProfile("wood", "impact_wood", (205, 165, 95)),
    "stone": ImpactProfile("stone", "impact_stone", (185, 185, 175)),
    "metal": ImpactProfile("spark", "impact_metal", (180, 215, 230)),
    "water": ImpactProfile("splash", "impact_water", (120, 205, 255)),
}


def impact_profile(material: str | None) -> ImpactProfile:
    """Retorna feedback consistente sem espalhar decisões por nome de entidade."""
    return IMPACT_PROFILES.get(material or "", IMPACT_PROFILES["stone"])
