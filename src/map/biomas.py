import random

from entities import actor


FOREST_TREES = ("Arvore", "Arvore", "Arvore", "RedTree")


def _spawn_tree(map_obj, x, y, tree_name):
    map_obj.entidades.append(actor.Entidade(x, y, tree_name, map_obj.context))


def aplicar_bioma_floresta(map_obj, x, y, tile, roll):
    tile.tipo = "grass"
    if roll < 3:
        _spawn_tree(map_obj, x, y, random.choice(FOREST_TREES))
    elif roll < 6:
        tile.tipo = "rocha"
    elif roll < 12:
        tile.tipo = "mud"


def aplicar_bioma_ruinas(map_obj, x, y, tile, roll):
    tile.tipo = "rubble"
    if roll < 2:
        _spawn_tree(map_obj, x, y, "RedTree")
    elif roll < 9:
        tile.tipo = "parede"
        tile.bloqueado = True
    elif roll < 24:
        tile.tipo = "terra"


def aplicar_bioma_azul(map_obj, x, y, tile, roll):
    tile.tipo = "blue_ground"
    if roll < 2:
        _spawn_tree(map_obj, x, y, "Arvore")
    elif roll < 7:
        tile.tipo = "mud"


def spawn_inimigos_por_bioma(map_obj, origin_x, origin_y, biome_type):
    quantity = random.randint(2, 4)
    enemy_name = {"ruinas": "Runner", "azul": "Tank"}.get(biome_type, "Walker")
    for _ in range(quantity):
        x = origin_x + random.randint(5, 25)
        y = origin_y + random.randint(5, 25)
        if not map_obj.is_blocked_terrain(x, y):
            map_obj.entidades.append(actor.Entidade(x, y, enemy_name, map_obj.context))
