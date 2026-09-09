from __future__ import annotations


BLOCKING_TERRAIN = frozenset({"parede", "deep_water"})

SOLID_DECORATIONS = frozenset({
    "nature_bush_green",
    "nature_bush_autumn",
    "nature_leaf_cluster",
    "nature_plant_tall",
    "nature_cattail",
    "nature_dry_leafy",
    "nature_dry_cattail",
    "nature_stump",
    "nature_crystal_blue",
    "nature_bonfire",
    "farm_fence_top",
    "farm_fence_bottom",
    "farm_fence_left",
    "farm_fence_right",
    # Partes de casas de vilas
    "house_window_front",
    "house_window_shutters",
    "house_wall_h",
    "house_wall_v",
    "house_chimney",
})

TERRAIN_MATERIALS = {
    "deep_water": "water",
    "parede": "stone",
    "rubble": "stone",
    "rocha": "stone",
}


def decoration_is_solid(decoration: str | None) -> bool:
    return decoration in SOLID_DECORATIONS


def tile_is_blocking(tile) -> bool:
    return bool(
        tile
        and (
            tile.bloqueado
            or tile.tipo in BLOCKING_TERRAIN
            or decoration_is_solid(tile.decoracao)
        )
    )


def terrain_material(tile) -> str:
    if not tile:
        return "stone"
    return TERRAIN_MATERIALS.get(tile.tipo, "stone")
