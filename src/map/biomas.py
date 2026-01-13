# src/map/biomas.py
import random
from entities import actor

def aplicar_bioma_floresta(mapa, gx, gy, tile, rng):
    if rng < 6: 
        # Chance de ser Arvore ou Cipreste
        tipo_arvore = "Arvore"
        if random.random() < 0.5: # 50% de chance
            tipo_arvore = "Cipreste"
            
        # CORREÇÃO: Agora usamos actor.Entidade diretamente, sem passar HP
        arv = actor.Entidade(gx, gy, tipo_arvore)
        mapa.entidades.append(arv)
        tile.bloqueado = True 
        
    elif rng < 12:
        tile.tipo = "rocha"
        tile.bloqueado = True

def aplicar_bioma_ruinas(mapa, gx, gy, tile, rng):
    if rng < 5:
        # CORREÇÃO: Usa Entidade e o nome "RedTree" (que deve estar no game_data.py)
        arv_vermelha = actor.Entidade(gx, gy, "RedTree")
        mapa.entidades.append(arv_vermelha)
        tile.bloqueado = True
    elif rng < 16:
        tile.tipo = "parede"
        tile.bloqueado = True
    elif rng < 26:
        tile.tipo = "terra"

def aplicar_bioma_azul(mapa, gx, gy, tile, rng):
    tile.tipo = "blue_ground"
    if rng < 5:
        tile.bloqueado = True # Cristais/pedras azuis

def spawn_inimigos_por_bioma(mapa, ox, oy, tipo_bioma):
    qtd = random.randint(2, 4)
    for _ in range(qtd):
        mx = ox + random.randint(5, 25)
        my = oy + random.randint(5, 25)
        
        if not mapa.is_blocked_terrain(mx, my):
            # Define apenas o NOME do inimigo
            if tipo_bioma == "ruinas":
                nome = "Troll"
            elif tipo_bioma == "azul":
                nome = "REI TROLL"
            else:
                nome = "Orc"
                
            # CORREÇÃO: Instancia Entidade apenas com posição e nome
            # A classe Entidade vai buscar o HP/Dano no game_data.py
            mapa.entidades.append(actor.Entidade(mx, my, nome))