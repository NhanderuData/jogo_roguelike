from __future__ import annotations


BLOCKING_TERRAIN = frozenset({"parede", "deep_water"})

SOLID_DECORATIONS = frozenset({
    # Plantas, arbustos e juncos baixos são atravessáveis. Este conjunto fica
    # reservado para objetos com volume físico ou partes estruturais.
    "nature_stump",
    "nature_crystal_blue",
    "nature_bonfire",
    "farm_fence_top",
    "farm_fence_bottom",
    "farm_fence_left",
    "farm_fence_right",
    "farm_fence_h",
    "farm_fence_h_left",
    "farm_fence_h_mid",
    "farm_fence_h_right",
    "farm_fence_v",
    "farm_fence_corner_tl",
    "farm_fence_corner_tr",
    "farm_fence_corner_bl",
    "farm_fence_corner_br",
    # Partes de casas de vilas
    "house_window_front",
    "house_window_shutters",
    "house_chimney",
    "village_house_amber",
    "village_house_brick",
    "village_house_moss",
    # Props da cidade
    "town_well",
    "street_lamp",
    "market_stall",
    "blacksmith_furnace",
    "blacksmith_anvil",
    "town_workbench",
    "town_bench",
    "town_bench_large",
    "barrel_wood",
    "crate_wood",
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
    decoracao = getattr(tile, "decoracao", None)
    if decoracao:
        if "fence" in decoracao or decoracao in {
            "barrel_wood", "crate_wood", "town_workbench", "market_stall",
            "town_bench", "town_bench_large", "logs_firewood"
        }:
            return "wood"
        if decoracao in {"blacksmith_anvil", "street_lamp"}:
            return "metal"
        if decoracao in {"town_well", "blacksmith_furnace"}:
            return "stone"
    return TERRAIN_MATERIALS.get(getattr(tile, "tipo", None), "stone")

