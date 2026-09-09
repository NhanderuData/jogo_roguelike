import random

from entities import actor
from .terrain import SOLID_DECORATIONS, decoration_is_solid


FOREST_TREES = (
    "Arvore",
    "Arvore",
    "Carvalho",
    "Salgueiro",
    "Pinheiro",
    "RedTree",
)
RUINS_TREES = ("Arvore Seca", "RedTree")
BLUE_TREES = (
    "Arvore Congelada",
    "Arvore Congelada",
    "Salgueiro",
    "Pinheiro",
)

FOREST_DECORATIONS = (
    "nature_sprout",
    "nature_sprout",
    "nature_leaf_cluster",
    "nature_plant_tall",
    "nature_cattail",
    "nature_flower_purple",
    "nature_mushroom",
    "nature_fallen_leaves",
    "nature_flower_white",
    "nature_flower_yellow",
    "nature_bush_green",
    "nature_pebble_gray",
    "nature_stump",
)
RUINS_DECORATIONS = (
    "nature_dry_sprout",
    "nature_dry_leafy",
    "nature_twig",
    "nature_stump",
    "nature_fallen_leaves",
    "nature_mushroom",
    "nature_pebble_gray",
    "nature_ore_orange",
    "nature_bush_autumn",
)
BLUE_DECORATIONS = (
    "nature_flower_blue",
    "nature_flower_white",
    "nature_pebble_gray",
    "nature_pebble_gray",
    "nature_dry_sprout",
    "nature_twig",
)
DESERT_DECORATIONS = (
    "nature_dry_sprout",
    "nature_dry_sprout",
    "nature_dry_cattail",
    "nature_twig",
    "nature_pebble_brown",
    "nature_ore_orange",
)
MEADOW_DECORATIONS = (
    "nature_sprout",
    "nature_sprout",
    "nature_flower_white",
    "nature_flower_yellow",
    "nature_flower_purple",
    "nature_mushroom",
)
POND_DECORATIONS = (
    "nature_cattail",
    "nature_cattail",
    "nature_sprout",
    "nature_flower_blue",
    "nature_flower_white",
    "nature_pebble_gray",
)

def decoracao_solida(decoracao):
    """Compatibilidade; novas regras de colisão pertencem a map.terrain."""
    return decoration_is_solid(decoracao)


def _spawn_tree(map_obj, x, y, tree_name):
    positions = getattr(map_obj, "_tree_positions", None)
    if positions is not None:
        for offset_y in (-1, 0, 1):
            for offset_x in (-1, 0, 1):
                if (x + offset_x, y + offset_y) in positions:
                    return False
    map_obj.entidades.append(
        actor.Entidade(
            x,
            y,
            tree_name,
            map_obj.context,
            rng=getattr(map_obj, "gameplay_rng", None),
        )
    )
    if positions is not None:
        positions.add((x, y))
    return True


def aplicar_bioma_floresta(map_obj, x, y, tile, roll, densidade=0.0, rng=None):
    chooser = rng or random
    tile.tipo = "grass"
    tile.bloqueado = False
    tile.bioma = "floresta"

    # Valores baixos viram clareiras naturais; valores altos concentram bosque.
    if densidade < -0.16:
        tile.tipo = "terra"
        if roll < 9:
            tile.decoracao = chooser.choice((
                "nature_fallen_leaves",
                "nature_pebble_gray",
                "nature_mushroom",
            ))
        return
    if densidade < -0.07:
        if roll < 32:
            tile.decoracao = chooser.choice(MEADOW_DECORATIONS)
        return

    tree_chance = 4
    if densidade > 0.14:
        tree_chance = 13
    elif densidade > 0.06:
        tree_chance = 8

    decoration_chance = 18 if densidade < 0.08 else 12

    if roll < tree_chance:
        _spawn_tree(map_obj, x, y, chooser.choice(FOREST_TREES))
    elif roll < tree_chance + 3:
        tile.tipo = "rocha"
        tile.bloqueado = True
    elif roll < tree_chance + 9 and densidade < 0.08:
        tile.tipo = "mud"
    elif roll < tree_chance + decoration_chance:
        tile.decoracao = chooser.choice(FOREST_DECORATIONS)


def aplicar_bioma_ruinas(map_obj, x, y, tile, roll, densidade=0.0, rng=None):
    chooser = rng or random
    tile.tipo = "rubble"
    tile.bloqueado = False
    tile.bioma = "ruinas"
    if densidade < -0.14:
        tile.tipo = "terra"
        if roll < 18:
            tile.decoracao = chooser.choice(RUINS_DECORATIONS)
        return

    tree_chance = 2 if densidade < 0.1 else 4
    wall_limit = tree_chance + (7 if densidade < 0.12 else 13)
    if roll < tree_chance:
        _spawn_tree(map_obj, x, y, chooser.choice(RUINS_TREES))
    elif roll < wall_limit:
        tile.tipo = "parede"
        tile.bloqueado = True
    elif roll < wall_limit + 15:
        tile.tipo = "terra"
    elif roll < wall_limit + 31:
        tile.decoracao = chooser.choice(RUINS_DECORATIONS)


def aplicar_bioma_azul(map_obj, x, y, tile, roll, densidade=0.0, rng=None):
    chooser = rng or random
    tile.tipo = "blue_ground"
    tile.bloqueado = False
    tile.bioma = "neve"
    tree_chance = 2 if densidade < 0.08 else 7
    if roll < tree_chance:
        _spawn_tree(map_obj, x, y, chooser.choice(BLUE_TREES))
    elif roll < tree_chance + 2:
        tile.tipo = "rocha"
        tile.bloqueado = True
    elif roll < tree_chance + (7 if densidade < 0.04 else 12):
        tile.decoracao = chooser.choice(BLUE_DECORATIONS)
    elif (x * 37 + y * 19 + 11) % 211 == 0:
        tile.decoracao = "nature_crystal_blue"


def aplicar_margem_lagoa(tile, roll, rng=None):
    tile.tipo = "grass"
    tile.bloqueado = False
    tile.bioma = "lagoa"
    if roll < 30:
        tile.decoracao = (rng or random).choice(POND_DECORATIONS)


def aplicar_bioma_deserto(map_obj, x, y, tile, roll, densidade=0.0, rng=None):
    """Deserto aberto usando a textura de areia já carregada pelo jogo."""
    tile.tipo = "sand"
    tile.bloqueado = False
    tile.bioma = "deserto"
    decoration_chance = 6
    if densidade > 0.12:
        decoration_chance = 18
    elif densidade < -0.08:
        decoration_chance = 2
    if roll < decoration_chance:
        tile.decoracao = (rng or random).choice(DESERT_DECORATIONS)


def spawn_inimigos_por_bioma(map_obj, origin_x, origin_y, biome_type, rng=None):
    chooser = rng or random
    quantity = chooser.randint(2, 4)
    enemy_name = {"ruinas": "Runner", "azul": "Tank"}.get(biome_type, "Walker")
    for _ in range(quantity):
        x = origin_x + chooser.randint(5, 25)
        y = origin_y + chooser.randint(5, 25)
        if not map_obj.is_blocked_terrain(x, y):
            map_obj.entidades.append(
                actor.Entidade(
                    x,
                    y,
                    enemy_name,
                    map_obj.context,
                    rng=getattr(map_obj, "gameplay_rng", None),
                )
            )
