# src/map/biomas.py
import random
from entities import actor

def aplicar_bioma_floresta(mapa, gx, gy, tile, rng):
    if rng < 6: 
        arv = actor.ObjetoDestrutivel(gx, gy, "Arvore", hp=50)
        mapa.entidades.append(arv)
        tile.bloqueado = True 
    elif rng < 12:
        tile.tipo = "rocha"
        tile.bloqueado = True

def aplicar_bioma_ruinas(mapa, gx, gy, tile, rng):
    if rng < 5:
        arv_vermelha = actor.ObjetoDestrutivel(gx, gy, "RedTree", hp=60)
        mapa.entidades.append(arv_vermelha)
        tile.bloqueado = True
    elif rng < 16:
        tile.tipo = "parede"
        tile.bloqueado = True
        # z_level removido
    elif rng < 26:
        tile.tipo = "terra"

def aplicar_bioma_azul(mapa, gx, gy, tile, rng):
    tile.tipo = "blue_ground"
    # z_level removido
    if rng < 5:
        tile.bloqueado = True # Cristais/pedras azuis

def spawn_inimigos_por_bioma(mapa, ox, oy, tipo_bioma):
    qtd = random.randint(2, 4)
    for _ in range(qtd):
        mx = ox + random.randint(5, 25)
        my = oy + random.randint(5, 25)
        
        if not mapa.is_blocked_terrain(mx, my):
            if tipo_bioma == "ruinas":
                nome, hp, dano, xp = "Troll", 80, 15, 50
            elif tipo_bioma == "azul":
                nome, hp, dano, xp = "REI TROLL", 150, 20, 100
            else:
                nome, hp, dano, xp = "Orc", 30, 5, 15
                
            mapa.entidades.append(actor.Entidade(mx, my, nome, hp, dano, xp_reward=xp))