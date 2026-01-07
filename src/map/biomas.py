# src/map/biomas.py
import random
from entities import actor

def aplicar_bioma_floresta(mapa, gx, gy, tile, rng):
    """ Regras para o bioma de Orcs e Bétulas """
    if rng < 10: 
        arv = actor.ObjetoDestrutivel(gx, gy, "Arvore", hp=50)
        mapa.entidades.append(arv)
        tile.bloqueado = True 
    elif rng < 12:
        tile.tipo = "rocha"
        tile.bloqueado = True

def aplicar_bioma_ruinas(mapa, gx, gy, tile, rng):
    """ Regras para o bioma de Trolls e Paredes """
    if rng < 8:
        tile.tipo = "parede"
        tile.bloqueado = True
        tile.z_level = 1 # Ruínas costumam ter relevo
    elif rng < 12:
        tile.tipo = "terra" # Chão de ruína é mais sujo

def spawn_inimigos_por_bioma(mapa, ox, oy, tipo_bioma):
    """ Spawna os monstros certos no lugar certo """
    qtd = random.randint(2, 4)
    for _ in range(qtd):
        mx = ox + random.randint(5, 25)
        my = oy + random.randint(5, 25)
        
        if not mapa.is_blocked_terrain(mx, my):
            if tipo_bioma == "ruinas":
                nome, hp, dano, xp = "Troll", 80, 15, 50
            else:
                nome, hp, dano, xp = "Orc", 30, 5, 15
                
            mapa.entidades.append(actor.Entidade(mx, my, nome, hp, dano, xp_reward=xp))