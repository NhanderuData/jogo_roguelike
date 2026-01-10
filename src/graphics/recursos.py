import pygame
import random
from . import config

SPRITES = {}

def criar_sprite_provisorio(cor):
    surf = pygame.Surface((32, 32))
    surf.fill(cor)
    return surf

# --- GERADOR DE PRAIA (ESTILO MINECRAFT/ZELDA) ---
def criar_borda_praia(lado):
    surf = pygame.Surface((32, 32), pygame.SRCALPHA)
    
    # Cores (Ajustadas para o seu Azul Novo)
    cor_areia = (240, 230, 140)         # Parte de dentro
    cor_borda = (210, 180, 140)         # "Contorno" molhado (1px)
    
    largura_tile = 32
    # Define o quão "fundo" a areia entra na água (Min 4px, Max 10px)
    altura_media = 6 
    
    # --- 1. GERA UM "MAPA DE ALTURA" 1D ---
    # Isso cria uma linha que sobe e desce suavemente (random walk)
    alturas = []
    h_atual = altura_media
    
    for i in range(largura_tile):
        # Varia -1, 0 ou +1 pixel a cada passo (dá o visual "pixel art")
        variacao = random.choice([-1, 0, 1])
        h_atual += variacao
        
        # Mantém a altura dentro de limites aceitáveis para não cortar
        h_atual = max(3, min(h_atual, 12))
        alturas.append(h_atual)
        
    # --- 2. DESENHA A BORDA SÓLIDA ---
    if lado == 'top':
        # Areia vem de CIMA. Desenhamos de 0 até a altura.
        for x in range(largura_tile):
            h = alturas[x]
            # Desenha a areia sólida
            pygame.draw.line(surf, cor_areia, (x, 0), (x, h))
            # Desenha 1px de borda escura na ponta
            surf.set_at((x, h), cor_borda)
            
    elif lado == 'bottom':
        # Areia vem de BAIXO. Desenhamos de 31 até (31 - altura).
        for x in range(largura_tile):
            h = alturas[x]
            pygame.draw.line(surf, cor_areia, (x, 31), (x, 31 - h))
            surf.set_at((x, 31 - h), cor_borda)

    elif lado == 'left':
        # Areia vem da ESQUERDA.
        for y in range(largura_tile):
            w = alturas[y] # Aqui a altura vira largura
            pygame.draw.line(surf, cor_areia, (0, y), (w, y))
            surf.set_at((w, y), cor_borda)

    elif lado == 'right':
        # Areia vem da DIREITA.
        for y in range(largura_tile):
            w = alturas[y]
            pygame.draw.line(surf, cor_areia, (31, y), (31 - w, y))
            surf.set_at((31 - w, y), cor_borda)
            
    return surf

# ... (Mantenha o resto do arquivo igual: carregar_spritesheet, carregar_estatico, carregar_tudo) ...
# Apenas certifique-se de que a função carregar_tudo está chamando a nova criar_borda_praia:

def carregar_spritesheet(nome_arquivo, colunas, escala=2.0):
    caminho = f"assets/{nome_arquivo}"
    try:
        sheet = pygame.image.load(caminho).convert_alpha()
        # ... (seu código de recorte existente) ...
        largura_total = sheet.get_width()
        altura_total = sheet.get_height()
        largura_frame = largura_total // colunas
        novo_w = int(largura_frame * escala)
        novo_h = int(altura_total * escala)
        lista_frames = []
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
    SPRITES["estrada"] = criar_sprite_provisorio(config.MARROM_ESTRADA)
    SPRITES["shoot"] = carregar_estatico("shoot.png", escala=2.0)
    
    # Seus outros assets...
    SPRITES["llama_run"] = carregar_spritesheet("llama.png", colunas=6, escala=2.0)
    SPRITES["tree"] = carregar_spritesheet("tree.png", colunas=18, escala=2.0)
    SPRITES["red_tree"] = carregar_spritesheet("RedTree.png", colunas=1, escala=2.0)
    SPRITES["cipreste"] = carregar_spritesheet("Cipreste.png", colunas=1, escala=2.0)
    SPRITES["rock"] = carregar_estatico("rock.png")
    SPRITES["wall"] = carregar_estatico("wall.png", escala=1.0)
    SPRITES["house"] = carregar_estatico("house.png", escala=1.0)
    
    SPRITES["orc_run"] = [criar_sprite_provisorio(config.VERDE)] 
    SPRITES["troll_run"] = [criar_sprite_provisorio(config.VERMELHO)]
    SPRITES["boss_run"] = [criar_sprite_provisorio(config.ROXO)]
    SPRITES["deep_water"] = criar_sprite_provisorio(config.AZUL_PROFUNDO)
    SPRITES["sand"] = criar_sprite_provisorio(config.COR_AREIA)
    
    # Sombra
    largura_base, altura_base, margem = 32, 16, 4
    sombra = pygame.Surface((largura_base + margem, altura_base + margem), pygame.SRCALPHA)
    pygame.draw.ellipse(sombra, (0, 0, 0, 70), [margem//2, margem//2, largura_base, altura_base])
    SPRITES["shadow"] = sombra

    # AS BORDAS (Agora sólidas e bonitas)
    SPRITES["border_top"] = criar_borda_praia('top')
    SPRITES["border_bottom"] = criar_borda_praia('bottom')
    SPRITES["border_left"] = criar_borda_praia('left')
    SPRITES["border_right"] = criar_borda_praia('right')