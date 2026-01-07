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
    if rng < 8:
        arv_vermelha = actor.ObjetoDestrutivel(gx, gy, "RedTree", hp=60)
        mapa.entidades.append(arv_vermelha)
        tile.bloqueado = True
        
    # 2. Spawn de Paredes com Relevo (8% de chance: 8 a 15)
    elif rng < 16:
        tile.tipo = "parede"
        tile.bloqueado = True
        tile.z_level = 1  # Mantém o relevo das ruínas
        
    # 3. Chão de Terra/Sujeira (10% de chance: 16 a 25)
    elif rng < 26:
        tile.tipo = "terra"

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