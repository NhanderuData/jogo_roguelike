import pygame
import random
import logging
from core import config
from core.paths import asset_path

logger = logging.getLogger(__name__)

SPRITES = {}
_IMAGE_CACHE = {}

DECORACOES_ALTAS = frozenset({
    "nature_bush_green",
    "nature_bush_autumn",
    "nature_leaf_cluster",
    "nature_plant_tall",
    "nature_cattail",
    "nature_flower_purple",
    "nature_dry_leafy",
    "nature_dry_cattail",
    "nature_crystal_blue",
    "nature_bonfire",
    "farm_fence_top",
    "farm_fence_bottom",
    "farm_fence_left",
    "farm_fence_right",
    "house_door_front",
    "house_door_wood",
    "house_window_front",
    "house_window_shutters",
    "house_chimney",
    "house_wall_h",
    "house_wall_v",
})

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
    
    rng = random.Random(f"beach-border:{lado}")
    for i in range(largura_tile):
        # Varia -1, 0 ou +1 pixel a cada passo (dá o visual "pixel art")
        variacao = rng.choice([-1, 0, 1])
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

def _carregar_imagem(nome_arquivo):
    """Carrega e converte uma imagem uma única vez por caminho."""
    caminho = asset_path(nome_arquivo)
    cache_key = str(caminho.resolve())
    cached = _IMAGE_CACHE.get(cache_key)
    if cached is None:
        cached = pygame.image.load(caminho).convert_alpha()
        _IMAGE_CACHE[cache_key] = cached
    return cached


def carregar_spritesheet(nome_arquivo, colunas, escala=2.0):
    caminho = asset_path(nome_arquivo)
    try:
        sheet = _carregar_imagem(nome_arquivo)
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


def normalizar_frames(frames, tamanho=(64, 64)):
    """Centraliza folhas menores no mesmo canvas, mantendo os pés alinhados."""
    normalized = []
    for frame in frames:
        bounds = frame.get_bounding_rect(min_alpha=1)
        if bounds.width == 0 or bounds.height == 0:
            normalized.append(pygame.Surface(tamanho, pygame.SRCALPHA))
            continue
        cropped = frame.subsurface(bounds)
        canvas = pygame.Surface(tamanho, pygame.SRCALPHA)
        x = (tamanho[0] - cropped.get_width()) // 2
        y = tamanho[1] - cropped.get_height() - 4
        canvas.blit(cropped, (x, y))
        normalized.append(canvas)
    return normalized


def ampliar_frames(frames, escala=2):
    return [
        pygame.transform.scale(
            frame,
            (frame.get_width() * escala, frame.get_height() * escala),
        )
        for frame in frames
    ]


def vestir_personagem(frames):
    """Recolore o corpo-base com roupa sem apagar contornos e transparência."""
    dressed_frames = []
    shirt = (48, 105, 76)
    pants = (47, 55, 65)
    for source in frames:
        frame = source.copy()
        bounds = frame.get_bounding_rect(min_alpha=1)
        torso_start = bounds.top + round(bounds.height * 0.38)
        legs_start = bounds.top + round(bounds.height * 0.68)
        for y in range(torso_start, bounds.bottom):
            target = shirt if y < legs_start else pants
            for x in range(bounds.left, bounds.right):
                red, green, blue, alpha = frame.get_at((x, y))
                if alpha == 0 or max(red, green, blue) < 55:
                    continue
                light = max(0.48, min(1.15, (red + green + blue) / 420))
                frame.set_at((
                    x,
                    y,
                ), (
                    min(255, round(target[0] * light)),
                    min(255, round(target[1] * light)),
                    min(255, round(target[2] * light)),
                    alpha,
                ))
        dressed_frames.append(frame)
    return dressed_frames


def espelhar_frames(frames):
    return [pygame.transform.flip(frame, True, False) for frame in frames]


def carregar_personagem_pixel_crawler():
    base = "sprites/pixel_crawler/player"
    def load(name, columns):
        frames = carregar_spritesheet(f"{base}_{name}.png", columns, 1.0)
        return ampliar_frames(vestir_personagem(normalizar_frames(frames)))

    idle_down = load("idle_down", 4)
    idle_up = load("idle_up", 4)
    idle_right = load("idle_side", 4)
    run_down = load("run_down", 6)
    run_up = load("run_up", 6)
    run_right = load("run_side", 6)
    return {
        "idle": {
            "down": idle_down,
            "up": idle_up,
            "right": idle_right,
            "left": espelhar_frames(idle_right),
        },
        "move": {
            "down": run_down,
            "up": run_up,
            "right": run_right,
            "left": espelhar_frames(run_right),
        },
    }


def carregar_inimigo_pixel_crawler(nome):
    base = f"sprites/pixel_crawler/{nome}"
    idle_right = ampliar_frames(normalizar_frames(carregar_spritesheet(f"{base}_idle.png", 4, 1.0)))
    run_right = ampliar_frames(normalizar_frames(carregar_spritesheet(f"{base}_run.png", 6, 1.0)))
    return {
        "idle": {
            "right": idle_right,
            "left": espelhar_frames(idle_right),
        },
        "move": {
            "right": run_right,
            "left": espelhar_frames(run_right),
        },
    }

def carregar_primeiro_frame(nome_arquivo, colunas, escala=2.0):
    frames = carregar_spritesheet(nome_arquivo, colunas, escala)
    return frames[0]

def carregar_estatico(nome_arquivo, escala=2.0):
    try:
        img = _carregar_imagem(nome_arquivo)
        img = pygame.transform.scale(img, (int(img.get_width()*escala), int(img.get_height()*escala)))
        return img
    except (FileNotFoundError, pygame.error, ValueError) as exc:
        logger.warning("Could not load image %s: %s", nome_arquivo, exc)
        return criar_sprite_provisorio(config.CINZA_CLARO)


def carregar_regiao_atlas(nome_arquivo, rect, escala=2.0):
    """Recorta uma região do atlas e amplia com escala inteira, sem suavização."""
    try:
        caminho = asset_path(nome_arquivo)
        atlas = _carregar_imagem(nome_arquivo)
        region = pygame.Rect(rect)
        if not atlas.get_rect().contains(region):
            raise ValueError(f"região {rect} fora do atlas {atlas.get_size()}")
        image = atlas.subsurface(region).copy()
        if escala != 1.0:
            image = pygame.transform.scale(
                image,
                (round(image.get_width() * escala), round(image.get_height() * escala)),
            )
        return image
    except (FileNotFoundError, pygame.error, ValueError) as exc:
        logger.warning("Could not load atlas region %s %s: %s", nome_arquivo, rect, exc)
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
    logger.info("Loading game assets")
    SPRITES.clear()
    
    SPRITES["shoot"] = criar_sprite_projetil()

    for sprite_name in (
        "weapon_pistol", "weapon_shotgun", "weapon_smg", "weapon_machete",
        "item_medkit", "item_energy_drink", "item_armor", "item_ammo_box",
    ):
        SPRITES[sprite_name] = carregar_estatico(f"sprites/{sprite_name}.png", escala=1.0)

    # Chão natural recortado do atlas de 16 px do Pixel Crawler. A areia
    # permanece a textura já usada pelo deserto, como solicitado.
    nature_tile_regions = {
        "terrain_grass": (
            "floors.png",
            ((32, 160, 16, 16), (16, 160, 16, 16), (48, 160, 16, 16)),
        ),
        "terrain_dirt": (
            "floors.png",
            ((192, 160, 16, 16), (176, 160, 16, 16), (208, 160, 16, 16)),
        ),
        # O antigo bioma azul agora usa a neve do próprio pacote.
        "terrain_moss": (
            "floors.png",
            ((32, 352, 16, 16), (16, 352, 16, 16), (48, 352, 16, 16)),
        ),
        "terrain_mud": (
            "floors.png",
            ((192, 176, 16, 16), (176, 176, 16, 16), (208, 176, 16, 16)),
        ),
        "terrain_rubble": (
            "floors.png",
            ((272, 0, 16, 16), (256, 0, 16, 16), (288, 0, 16, 16)),
        ),
        "terrain_water": (
            "water.png",
            (
                (80, 0, 16, 16),
                (176, 0, 16, 16),
                (272, 0, 16, 16),
                (368, 0, 16, 16),
            ),
        ),
    }
    nature_base = "sprites/pixel_crawler/nature"
    for sprite_name, (atlas_name, regions) in nature_tile_regions.items():
        variants = [
            carregar_regiao_atlas(
                f"{nature_base}/{atlas_name}", rect, escala=2.0
            )
            for rect in regions
        ]
        SPRITES[f"{sprite_name}_variants"] = variants
        SPRITES[sprite_name] = variants[0]
        SPRITES[f"{sprite_name}_flip_x"] = pygame.transform.flip(
            variants[0], True, False
        )
        SPRITES[f"{sprite_name}_flip_y"] = pygame.transform.flip(
            variants[0], False, True
        )

    # Cada bloco horizontal de 96 px no atlas é um frame de 100 ms, formado
    # por uma grade 3x3 de tiles que já medem 32 px. Recortar apenas 16 px e
    # ampliar seleciona só um quadrante da peça (alguns cantos ficam parecendo
    # blocos lisos de água), interrompendo visualmente o contorno da lagoa.
    pond_edge_offsets = {
        "north": (32, 64),
        "south": (32, 0),
        "west": (64, 32),
        "east": (0, 32),
        "north_west": (64, 64),
        "north_east": (0, 64),
        "south_west": (64, 0),
        "south_east": (0, 0),
    }
    for edge_name, (offset_x, offset_y) in pond_edge_offsets.items():
        SPRITES[f"terrain_pond_edge_{edge_name}_frames"] = [
            carregar_regiao_atlas(
                f"{nature_base}/water.png",
                (offset_x + frame * 96, offset_y, 32, 32),
            )
            for frame in range(4)
        ]

    terrain_palette = {
        "terrain_sand": (config.COR_AREIA, 115),
    }
    for sprite_name, (target_color, strength) in terrain_palette.items():
        tile = carregar_estatico(f"sprites/{sprite_name}.png", escala=0.5)
        tile = aplicar_paleta_clara(tile, target_color, strength)
        SPRITES[sprite_name] = tile
        SPRITES[f"{sprite_name}_flip_x"] = pygame.transform.flip(tile, True, False)
        SPRITES[f"{sprite_name}_flip_y"] = pygame.transform.flip(tile, False, True)

    # Estradas rurais compartilham a textura de terra do atlas. Pontes usam
    # madeira nativa do tileset de dungeon, rotacionada conforme a travessia.
    SPRITES["terrain_road_variants"] = SPRITES["terrain_dirt_variants"]
    SPRITES["terrain_road"] = SPRITES["terrain_dirt"]
    SPRITES["terrain_road_flip_x"] = SPRITES["terrain_dirt_flip_x"]
    SPRITES["terrain_road_flip_y"] = SPRITES["terrain_dirt_flip_y"]
    bridge_vertical = carregar_regiao_atlas(
        f"{nature_base}/dungeon_tiles.png", (240, 0, 16, 16), escala=2.0
    )
    SPRITES["terrain_bridge_vertical"] = bridge_vertical
    SPRITES["terrain_bridge_horizontal"] = pygame.transform.rotate(
        bridge_vertical, 90
    )
    SPRITES["terrain_bridge"] = bridge_vertical

    grass = SPRITES["terrain_grass"]
    SPRITES["terrain_grass_flip_x"] = pygame.transform.flip(grass, True, False)
    SPRITES["terrain_grass_flip_y"] = pygame.transform.flip(grass, False, True)
    SPRITES["grass"] = grass
    SPRITES["blue_ground"] = SPRITES["terrain_moss"]
    SPRITES["estrada"] = SPRITES["terrain_road"]
    coast = criar_tile_costeiro(grass, SPRITES["terrain_sand"])
    SPRITES["terrain_coast"] = coast
    SPRITES["terrain_coast_flip_x"] = pygame.transform.flip(coast, True, False)
    SPRITES["terrain_coast_flip_y"] = pygame.transform.flip(coast, False, True)

    for prefix, texture in (
        ("coast_edge", coast),
        ("sand_edge", SPRITES["terrain_sand"]),
        ("moss_edge", SPRITES["terrain_moss"]),
        ("dirt_edge", SPRITES["terrain_dirt"]),
        ("rubble_edge", SPRITES["terrain_rubble"]),
    ):
        for index, side in enumerate(("top", "bottom", "left", "right")):
            SPRITES[f"{prefix}_{side}"] = criar_borda_texturizada(
                texture, side, seed=41 + index * 13
            )

    # Personagem e inimigos do Pixel Crawler Free Pack (Anokolisa).
    SPRITES["player_survivor"] = carregar_personagem_pixel_crawler()
    SPRITES["enemy_skeleton"] = carregar_inimigo_pixel_crawler("skeleton")
    SPRITES["enemy_orc_rogue"] = carregar_inimigo_pixel_crawler("orc_rogue")
    SPRITES["enemy_orc_warrior"] = carregar_inimigo_pixel_crawler("orc_warrior")

    # Árvores Size_04 nativas: mais detalhe real que apenas ampliar as pequenas.
    SPRITES["tree"] = carregar_regiao_atlas(
        f"{nature_base}/trees_broad_large.png", (0, 0, 80, 128), escala=2.0
    )
    SPRITES["red_tree"] = carregar_regiao_atlas(
        f"{nature_base}/trees_broad_large.png", (0, 128, 80, 128), escala=2.0
    )
    SPRITES["tree_oak"] = carregar_regiao_atlas(
        f"{nature_base}/trees_broad_large.png", (80, 0, 80, 128), escala=2.0
    )
    SPRITES["tree_willow"] = carregar_regiao_atlas(
        f"{nature_base}/trees_conifer_large.png", (0, 0, 64, 112), escala=2.0
    )
    SPRITES["tree_dead"] = carregar_regiao_atlas(
        f"{nature_base}/trees_broad_large.png", (160, 0, 80, 128), escala=2.0
    )
    SPRITES["tree_frozen"] = carregar_regiao_atlas(
        f"{nature_base}/trees_broad_large.png", (240, 0, 80, 128), escala=2.0
    )
    SPRITES["tree_fir"] = carregar_regiao_atlas(
        f"{nature_base}/trees_conifer_large.png", (0, 112, 64, 112), escala=2.0
    )
    SPRITES["cipreste"] = SPRITES["tree_fir"]
    SPRITES["rock"] = carregar_regiao_atlas(
        f"{nature_base}/rocks.png", (128, 16, 32, 32), escala=2.0
    )
    SPRITES["rock_brown"] = carregar_regiao_atlas(
        f"{nature_base}/rocks.png", (32, 16, 32, 32), escala=2.0
    )

    decoration_regions = {
        "nature_bush_green": ("vegetation.png", (0, 0, 32, 32)),
        "nature_bush_autumn": ("vegetation.png", (144, 0, 32, 32)),
        "nature_sprout": ("vegetation.png", (32, 144, 16, 16)),
        "nature_leaf_cluster": ("vegetation.png", (80, 144, 32, 32)),
        "nature_plant_tall": ("vegetation.png", (112, 160, 32, 32)),
        "nature_cattail": ("vegetation.png", (144, 160, 16, 32)),
        "nature_flower_purple": ("vegetation.png", (192, 160, 16, 32)),
        "nature_mushroom": ("vegetation.png", (48, 336, 16, 16)),
        "nature_fallen_leaves": ("vegetation.png", (64, 352, 48, 16)),
        "nature_flower_white": ("vegetation.png", (48, 384, 16, 16)),
        "nature_flower_blue": ("vegetation.png", (48, 400, 16, 16)),
        "nature_flower_yellow": ("vegetation.png", (48, 416, 16, 16)),
        "nature_dry_sprout": ("vegetation.png", (32, 240, 16, 16)),
        "nature_dry_leafy": ("vegetation.png", (80, 240, 32, 32)),
        "nature_dry_cattail": ("vegetation.png", (144, 256, 16, 32)),
        "nature_twig": ("vegetation.png", (240, 0, 16, 16)),
        "nature_stump": ("vegetation.png", (240, 128, 16, 16)),
        "nature_pebble_brown": ("rocks.png", (64, 64, 16, 16)),
        "nature_pebble_gray": ("rocks.png", (160, 64, 16, 16)),
        "nature_ore_orange": ("rocks.png", (96, 112, 16, 16)),
        "nature_crystal_blue": ("rocks.png", (144, 272, 32, 32)),
        "farm_carrot": ("farm.png", (80, 16, 16, 16)),
        "farm_beet": ("farm.png", (80, 48, 16, 16)),
        "farm_cabbage": ("farm.png", (80, 80, 16, 16)),
        "farm_cauliflower": ("farm.png", (80, 144, 16, 16)),
        "farm_onion": ("farm.png", (80, 208, 16, 16)),
        "farm_fence_top": ("building_props.png", (16, 176, 48, 32)),
        "farm_fence_bottom": ("building_props.png", (16, 240, 48, 32)),
        "farm_fence_left": ("building_props.png", (0, 192, 32, 32)),
        "farm_fence_right": ("building_props.png", (48, 192, 32, 32)),
        # Partes de casa para compor vilas
        "house_door_front": ("building_props.png", (0, 0, 32, 48)),
        "house_door_wood": ("building_props.png", (64, 0, 32, 48)),
        "house_window_front": ("building_props.png", (0, 48, 32, 32)),
        "house_window_shutters": ("building_props.png", (64, 48, 32, 32)),
        "house_chimney": ("building_props.png", (0, 80, 16, 32)),
        "house_wall_h": ("building_props.png", (96, 80, 32, 16)),
        "house_wall_v": ("building_props.png", (128, 64, 16, 32)),
        "house_bench": ("building_props.png", (32, 128, 80, 32)),
        "house_chest": ("building_props.png", (112, 112, 32, 32)),
    }
    for sprite_name, (atlas_name, rect) in decoration_regions.items():
        SPRITES[sprite_name] = carregar_regiao_atlas(
            f"{nature_base}/{atlas_name}", rect, escala=2.0
        )

    SPRITES["nature_bonfire_frames"] = carregar_spritesheet(
        f"{nature_base}/bonfire_sheet.png", colunas=4, escala=2.0
    )
    SPRITES["nature_bonfire"] = SPRITES["nature_bonfire_frames"][0]

    SPRITES["nature_bush"] = SPRITES["nature_bush_green"]

    # Outros assets legados ainda usados por entidades não naturais.
    SPRITES["llama_run"] = carregar_spritesheet("llama.png", colunas=6, escala=2.0)
    SPRITES["wall"] = SPRITES["terrain_rubble"]
    
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


def validar_sprites_conteudo(content):
    """Falha cedo quando JSON aponta para uma chave visual inexistente."""
    references = {
        definition.sprite
        for catalog in (content.items, content.entities, content.weapons)
        for definition in catalog.values()
    }
    missing = sorted(reference for reference in references if reference not in SPRITES)
    if missing:
        raise RuntimeError(
            "Content references unknown sprites: " + ", ".join(missing)
        )
