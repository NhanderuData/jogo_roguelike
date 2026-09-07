import pygame
import random
import logging
from core import config
from core.paths import asset_path

logger = logging.getLogger(__name__)

SPRITES = {}

def criar_sprite_provisorio(cor):
    surf = pygame.Surface((32, 32))
    surf.fill(cor)
    return surf

def criar_sprite_projetil():
    """Traçante horizontal; o renderer usa a versão rotacionada do projétil."""
    surf = pygame.Surface((22, 8), pygame.SRCALPHA)
    pygame.draw.polygon(surf, (255, 125, 35, 45), ((1, 4), (17, 1), (17, 7)))
    pygame.draw.line(surf, (255, 185, 55, 145), (4, 4), (18, 4), 3)
    pygame.draw.line(surf, (255, 250, 205), (13, 4), (21, 4), 2)
    pygame.draw.circle(surf, (255, 255, 235), (20, 4), 2)
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
    caminho = asset_path(nome_arquivo)
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
    except (FileNotFoundError, pygame.error, ValueError) as exc:
        logger.warning("Could not load sprite sheet %s: %s", caminho, exc)
        return [criar_sprite_provisorio(config.VERMELHO)]

def carregar_primeiro_frame(nome_arquivo, colunas, escala=2.0):
    frames = carregar_spritesheet(nome_arquivo, colunas, escala)
    return frames[0]

def carregar_estatico(nome_arquivo, escala=2.0):
    try:
        caminho = asset_path(nome_arquivo)
        img = pygame.image.load(caminho).convert_alpha()
        img = pygame.transform.scale(img, (int(img.get_width()*escala), int(img.get_height()*escala)))
        return img
    except (FileNotFoundError, pygame.error, ValueError) as exc:
        logger.warning("Could not load image %s: %s", nome_arquivo, exc)
        return criar_sprite_provisorio(config.CINZA_CLARO)

def aplicar_paleta_clara(surface, target_color, strength=90, brightness=18):
    result = surface.copy()
    overlay = pygame.Surface(result.get_size())
    overlay.fill(target_color)
    overlay.set_alpha(strength)
    result.blit(overlay, (0, 0))
    result.fill((brightness, brightness, brightness), special_flags=pygame.BLEND_RGB_ADD)
    return result

def criar_tile_costeiro(grass, sand):
    coast = grass.copy()
    sand_tint = sand.copy()
    sand_tint.set_alpha(135)
    coast.blit(sand_tint, (0, 0))
    return coast

def criar_borda_texturizada(texture, side, seed):
    border = pygame.Surface(texture.get_size(), pygame.SRCALPHA)
    rng = random.Random(seed)
    length = texture.get_width() if side in ("top", "bottom") else texture.get_height()
    depths = []
    depth = 5
    for _ in range(length):
        depth = max(3, min(8, depth + rng.choice((-1, 0, 0, 1))))
        depths.append(depth)

    width, height = texture.get_size()
    for y in range(height):
        for x in range(width):
            index = x if side in ("top", "bottom") else y
            if side == "top": distance = y
            elif side == "bottom": distance = height - 1 - y
            elif side == "left": distance = x
            else: distance = width - 1 - x

            edge = depths[index]
            opaque = distance < edge
            dithered = distance < edge + 2 and (x * 5 + y * 7 + seed) % 3 == 0
            if opaque or dithered:
                border.set_at((x, y), texture.get_at((x, y)))
    return border

def carregar_tudo():
    print("--- Carregando Assets ---")
    
    SPRITES["blue_ground"] = criar_sprite_provisorio(config.AZUL_AGUA)
    SPRITES["grass"] = carregar_estatico("grass.png", escala=2.0)
    SPRITES["estrada"] = criar_sprite_provisorio(config.MARROM_ESTRADA)
    SPRITES["shoot"] = criar_sprite_projetil()

    for sprite_name in (
        "weapon_pistol", "weapon_shotgun", "weapon_smg", "weapon_machete",
        "item_medkit", "item_energy_drink", "item_armor", "item_ammo_box",
    ):
        SPRITES[sprite_name] = carregar_estatico(f"sprites/{sprite_name}.png", escala=1.0)

    terrain_palette = {
        "terrain_dirt": ((170, 105, 60), 75),
        "terrain_road": (config.MARROM_ESTRADA, 90),
        "terrain_sand": (config.COR_AREIA, 115),
        "terrain_water": (config.AZUL_AGUA, 110),
        "terrain_moss": ((75, 170, 125), 85),
        "terrain_rubble": ((150, 150, 145), 70),
        "terrain_mud": ((135, 92, 55), 75),
    }
    SPRITES["terrain_grass"] = carregar_estatico("grass.png", escala=1.0)
    for sprite_name, (target_color, strength) in terrain_palette.items():
        tile = carregar_estatico(f"sprites/{sprite_name}.png", escala=0.5)
        tile = aplicar_paleta_clara(tile, target_color, strength)
        SPRITES[sprite_name] = tile
        SPRITES[f"{sprite_name}_flip_x"] = pygame.transform.flip(tile, True, False)
        SPRITES[f"{sprite_name}_flip_y"] = pygame.transform.flip(tile, False, True)

    grass = SPRITES["terrain_grass"]
    SPRITES["terrain_grass_flip_x"] = pygame.transform.flip(grass, True, False)
    SPRITES["terrain_grass_flip_y"] = pygame.transform.flip(grass, False, True)
    coast = criar_tile_costeiro(grass, SPRITES["terrain_sand"])
    SPRITES["terrain_coast"] = coast
    SPRITES["terrain_coast_flip_x"] = pygame.transform.flip(coast, True, False)
    SPRITES["terrain_coast_flip_y"] = pygame.transform.flip(coast, False, True)

    for prefix, texture in (
        ("coast_edge", coast),
        ("sand_edge", SPRITES["terrain_sand"]),
        ("moss_edge", SPRITES["terrain_moss"]),
    ):
        for index, side in enumerate(("top", "bottom", "left", "right")):
            SPRITES[f"{prefix}_{side}"] = criar_borda_texturizada(
                texture, side, seed=41 + index * 13
            )

    # Seus outros assets...
    SPRITES["llama_run"] = carregar_spritesheet("llama.png", colunas=6, escala=2.0)
    SPRITES["tree"] = carregar_primeiro_frame("tree.png", colunas=18, escala=2.0)
    SPRITES["red_tree"] = carregar_estatico("RedTree.png", escala=2.0)
    SPRITES["cipreste"] = carregar_spritesheet("Cipreste.png", colunas=1, escala=2.0)
    SPRITES["rock"] = carregar_estatico("rock.png")
    SPRITES["wall"] = SPRITES["terrain_rubble"]
    
    SPRITES["orc_run"] = [criar_sprite_provisorio(config.VERDE)] 
    SPRITES["troll_run"] = [criar_sprite_provisorio(config.VERMELHO)]
    SPRITES["boss_run"] = [criar_sprite_provisorio(config.ROXO)]
    SPRITES["deep_water"] = SPRITES["terrain_water"]
    SPRITES["sand"] = SPRITES["terrain_sand"]
    
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
