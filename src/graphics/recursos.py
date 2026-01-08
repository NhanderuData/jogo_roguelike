# src/graphics/recursos.py
import pygame
import random
from . import config

SPRITES = {}

def criar_sprite_provisorio(cor):
    surf = pygame.Surface((32, 32))
    surf.fill(cor)
    return surf

# --- GERADOR DE PRAIA (TRANSIÇÃO SUAVE) ---
def criar_borda_praia(lado):
    """
    Gera uma borda de areia que se dissolve na água.
    lado: 'top', 'bottom', 'left', 'right'
    """
    surf = pygame.Surface((32, 32), pygame.SRCALPHA)
    
    # Cores da Praia
    cor_areia = (238, 214, 175)      # Bege Areia
    cor_areia_molhada = (194, 178, 128) # Areia mais escura/molhada
    
    largura = 32
    tamanho_praia = 12 # Largura total da faixa de areia

    # Função auxiliar para desenhar o grão de areia com probabilidade
    def desenhar_grao(x, y, distancia_da_borda):
        # Quanto mais longe da borda, menos chance de ter areia (efeito de dissolver)
        chance = 1.0 - (distancia_da_borda / tamanho_praia)
        
        if random.random() < chance:
            # Perto da borda é areia seca, longe é molhada
            cor = cor_areia if chance > 0.5 else cor_areia_molhada
            surf.set_at((x, y), cor)

    if lado == 'top':
        # Grama está em cima, areia começa no y=0 e desce
        for y in range(tamanho_praia):
            for x in range(largura):
                desenhar_grao(x, y, y)
            
    elif lado == 'bottom':
        # Grama está embaixo, areia começa no y=31 e sobe
        for y in range(tamanho_praia):
            for x in range(largura):
                desenhar_grao(x, 31 - y, y)

    elif lado == 'left':
        # Grama na esquerda, areia começa no x=0 e vai pra direita
        for x in range(tamanho_praia):
            for y in range(largura):
                desenhar_grao(x, y, x)

    elif lado == 'right':
        # Grama na direita, areia começa no x=31 e vai pra esquerda
        for x in range(tamanho_praia):
            for y in range(largura):
                desenhar_grao(31 - x, y, x)
            
    return surf

# ... (Mantenha as funções carregar_spritesheet e carregar_estatico iguais) ...
def carregar_spritesheet(nome_arquivo, colunas, escala=2.0):
    caminho = f"assets/{nome_arquivo}"
    lista_frames = []
    try:
        sheet = pygame.image.load(caminho).convert_alpha()
        largura_total = sheet.get_width()
        altura_total = sheet.get_height()
        largura_frame = largura_total // colunas
        novo_w = int(largura_frame * escala)
        novo_h = int(altura_total * escala)
        for i in range(colunas):
            rect = pygame.Rect(i * largura_frame, 0, largura_frame, altura_total)
            frame = sheet.subsurface(rect)
            frame = pygame.transform.scale(frame, (novo_w, novo_h))
            lista_frames.append(frame)
        return lista_frames
    except: return [criar_sprite_provisorio(config.VERMELHO)]

def carregar_estatico(nome_arquivo, escala=2.0):
    try:
        img = pygame.image.load(f"assets/{nome_arquivo}").convert_alpha()
        img = pygame.transform.scale(img, (int(img.get_width()*escala), int(img.get_height()*escala)))
        return img
    except: return criar_sprite_provisorio(config.CINZA_CLARO)

def carregar_tudo():
    print("--- Carregando Assets ---")
    
    SPRITES["blue_ground"] = criar_sprite_provisorio(config.AZUL_AGUA)
    SPRITES["grass"] = carregar_estatico("grass.png", escala=2.0)
    
    SPRITES["llama_run"] = carregar_spritesheet("llama.png", colunas=6, escala=2.0)
    SPRITES["tree"] = carregar_spritesheet("tree.png", colunas=18, escala=2.0)
    SPRITES["red_tree"] = carregar_spritesheet("RedTree.png", colunas=1, escala=2.0)
    SPRITES["rock"] = carregar_estatico("rock.png")
    SPRITES["wall"] = carregar_estatico("wall.png", escala=1.0)
    SPRITES["house"] = carregar_estatico("house.png", escala=1.0)
    SPRITES["fireball"] = carregar_estatico("fireball.png", escala=1.0)
    
    SPRITES["orc_run"] = [criar_sprite_provisorio(config.VERDE)] 
    SPRITES["troll_run"] = [criar_sprite_provisorio(config.VERMELHO)]
    SPRITES["boss_run"] = [criar_sprite_provisorio(config.ROXO)]
    
    largura_base, altura_base, margem = 32, 16, 4
    sombra = pygame.Surface((largura_base + margem, altura_base + margem), pygame.SRCALPHA)
    pygame.draw.ellipse(sombra, (0, 0, 0, 70), [margem//2, margem//2, largura_base, altura_base])
    SPRITES["shadow"] = sombra

    # --- AQUI: USAMOS O NOVO GERADOR DE PRAIA ---
    SPRITES["border_top"] = criar_borda_praia('top')
    SPRITES["border_bottom"] = criar_borda_praia('bottom')
    SPRITES["border_left"] = criar_borda_praia('left')
    SPRITES["border_right"] = criar_borda_praia('right')