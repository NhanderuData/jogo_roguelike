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
    "farm_fence_h",
    "farm_fence_h_left",
    "farm_fence_h_mid",
    "farm_fence_h_right",
    "farm_fence_v",
    "farm_fence_corner_tl",
    "farm_fence_corner_tr",
    "farm_fence_corner_bl",
    "farm_fence_corner_br",
    "house_door_front",
    "house_door_wood",
    "house_window_front",
    "house_window_shutters",
    "house_chimney",
    "village_house_amber",
    "village_house_brick",
    "village_house_moss",
    # Props urbanos e da vila
    "town_well",
    "street_lamp",
    "market_stall",
    "blacksmith_furnace",
    "blacksmith_anvil",
    "town_workbench",
    "town_bench",
    "town_bench_large",
    "barrel_wood",
    "crate_wood",
    "sack_grain",
    "logs_firewood",
    "flower_pot",
    "signpost",
    "crate_carrots",
    "crate_beets",
    "crate_cabbage",
    "scarecrow",
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


def carregar_npc_pixel_crawler(nome):
    base = f"sprites/pixel_crawler/npc/{nome}"
    idle_frames = ampliar_frames(normalizar_frames(carregar_spritesheet(f"{base}_idle.png", 4, 1.0)))
    run_frames = ampliar_frames(normalizar_frames(carregar_spritesheet(f"{base}_run.png", 6, 1.0)))
    idle_left = espelhar_frames(idle_frames)
    run_left = espelhar_frames(run_frames)
    return {
        "idle": {
            "down": idle_frames,
            "up": idle_frames,
            "right": idle_frames,
            "left": idle_left,
        },
        "move": {
            "down": run_frames,
            "up": run_frames,
            "right": run_frames,
            "left": run_left,
        },
    }


def transformar_em_sombra(surface):
    result = surface.copy()
    w, h = result.get_size()
    for y in range(h):
        for x in range(w):
            r, g, b, a = result.get_at((x, y))
            if a == 0:
                continue
            lum = (r + g + b) / (3 * 255.0)
            shadow_r = int(14 + 18 * lum)
            shadow_g = int(10 + 14 * lum)
            shadow_b = int(26 + 32 * lum)
            result.set_at((x, y), (shadow_r, shadow_g, shadow_b, a))
    return result


def criar_variacao_sombra(anim_dict):
    result = {}
    for state, directions in anim_dict.items():
        result[state] = {}
        for direction, frames in directions.items():
            result[state][direction] = [transformar_em_sombra(f) for f in frames]
    return result


def carregar_animais_fazenda():
    animais = {}
    farm_configs = {
        "animal_bull": ("bull.png", (64, 64), 2.6),
        "animal_calf": ("calf.png", (64, 64), 2.6),
        "animal_chick": ("chick.png", (16, 16), 2.0),
        "animal_lamb": ("lamb.png", (32, 32), 1.8),
        "animal_piglet": ("piglet.png", (32, 32), 2.3),
        "animal_rooster": ("rooster.png", (32, 32), 1.6),
        "animal_sheep": ("sheep.png", (32, 32), 2.1),
        "animal_turkey": ("turkey.png", (32, 32), 1.8),
    }
    for key, (filename, (fw, fh), scale) in farm_configs.items():
        try:
            full_path = f"sprites/animals/farm/{filename}"
            sheet = _carregar_imagem(full_path)
            cols = min(6, sheet.get_width() // fw)
            rows = min(8, sheet.get_height() // fh)
            max_b = 0
            for r in range(rows):
                for c in range(cols):
                    sub = sheet.subsurface(pygame.Rect(c * fw, r * fh, fw, fh))
                    bb = sub.get_bounding_rect()
                    if bb.w > 0 and bb.h > 0:
                        max_b = max(max_b, bb.bottom)
            crop_h = min(fh, max_b + 1)
            target_w = int(fw * scale)
            target_h = int(crop_h * scale)

            def get_row(row, count):
                frames = []
                for col in range(count):
                    sub = sheet.subsurface(pygame.Rect(col * fw, row * fh, fw, crop_h))
                    if scale != 1.0 or crop_h != fh:
                        sub = pygame.transform.scale(sub, (target_w, target_h))
                    frames.append(sub)
                return frames

            animais[key] = {
                "idle": {
                    "down": get_row(4, 4),
                    "up": get_row(5, 4),
                    "left": get_row(6, 4),
                    "right": get_row(7, 4),
                },
                "move": {
                    "down": get_row(0, 6),
                    "up": get_row(1, 6),
                    "left": get_row(2, 6),
                    "right": get_row(3, 6),
                },
            }
        except Exception as exc:
            logger.warning("Could not load farm animal %s: %s", key, exc)
    return animais


def carregar_animais_caca():
    animais = {}
    hunt_configs = {
        "animal_boar": ("boar", "boar_idle.png", "boar_walk.png", 2.4),
        "animal_deer": ("deer", "deer_idle.png", "deer_walk.png", 2.6),
        "animal_fox": ("fox", "fox_idle.png", "fox_walk.png", 2.0),
        "animal_hare": ("hare", "hare_idle.png", "hare_walk.png", 1.7),
        "animal_black_grouse": ("black_grouse", "black_grouse_idle.png", "black_grouse_walk.png", 1.7),
    }
    fw, fh = 32, 32
    for key, (folder, idle_file, walk_file, scale) in hunt_configs.items():
        try:
            full_path_idle = f"sprites/animals/hunt/{folder}/{idle_file}"
            full_path_walk = f"sprites/animals/hunt/{folder}/{walk_file}"
            sheet_idle = _carregar_imagem(full_path_idle)
            sheet_walk = _carregar_imagem(full_path_walk)

            max_b = 0
            for sheet in (sheet_idle, sheet_walk):
                cols = sheet.get_width() // fw
                rows = sheet.get_height() // fh
                for r in range(rows):
                    for c in range(cols):
                        sub = sheet.subsurface(pygame.Rect(c * fw, r * fh, fw, fh))
                        bb = sub.get_bounding_rect()
                        if bb.w > 0 and bb.h > 0:
                            max_b = max(max_b, bb.bottom)
            crop_h = min(fh, max_b + 1)
            target_w = int(fw * scale)
            target_h = int(crop_h * scale)

            def load_action(sheet):
                cols = sheet.get_width() // fw
                dirs = {}
                for r, dir_name in enumerate(["down", "up", "left", "right"]):
                    frames = []
                    for c in range(cols):
                        sub = sheet.subsurface(pygame.Rect(c * fw, r * fh, fw, crop_h))
                        if scale != 1.0 or crop_h != fh:
                            sub = pygame.transform.scale(sub, (target_w, target_h))
                        frames.append(sub)
                    dirs[dir_name] = frames
                return dirs

            animais[key] = {
                "idle": load_action(sheet_idle),
                "move": load_action(sheet_walk),
            }
        except Exception as exc:
            logger.warning("Could not load hunt animal %s: %s", key, exc)
    return animais


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


POND_EDGE_OFFSETS = {
    "north": (32, 64),
    "south": (32, 0),
    "west": (64, 32),
    "east": (0, 32),
    "north_west": (48, 48),
    "north_east": (16, 48),
    "south_west": (48, 16),
    "south_east": (16, 16),
    "inner_north_west": (48, 64),
    "inner_north_east": (16, 64),
    "inner_south_west": (48, 0),
    "inner_south_east": (16, 0),
}


def carregar_bordas_lagoa(nature_base):
    """Carrega os autotiles 16px da lagoa na escala 2x do mundo."""
    return {
        f"terrain_pond_edge_{edge_name}_frames": [
            carregar_regiao_atlas(
                f"{nature_base}/water.png",
                (offset_x + frame * 96, offset_y, 16, 16),
                escala=2.0,
            )
            for frame in range(4)
        ]
        for edge_name, (offset_x, offset_y) in POND_EDGE_OFFSETS.items()
    }


ROCK_REGIONS = {
    "rock": (176, 16, 16, 16),
    "rock_brown": (80, 16, 16, 16),
}


def carregar_rochas(nature_base):
    """Carrega rochas de um tile, alinhadas à mesma grade 2x do terreno."""
    return {
        sprite_name: carregar_regiao_atlas(
            f"{nature_base}/rocks.png", rect, escala=2.0
        )
        for sprite_name, rect in ROCK_REGIONS.items()
    }


def criar_casa_vila(porta, janela, chamine, paleta, seed=0, janela_esquerda=False):
    """Compõe uma casa completa em pixel art usando peças do atlas original.

    O desenho nasce na resolução nativa de 16 px do pacote e só então é
    ampliado por dois. Isso mantém contornos, telhas e detalhes alinhados à
    mesma grade dos demais sprites do jogo.
    """
    largura, altura = 96, 88
    casa = pygame.Surface((largura, altura), pygame.SRCALPHA)
    rng = random.Random(f"village-house:{seed}")

    contorno = paleta["contorno"]
    madeira = paleta["madeira"]
    parede = paleta["parede"]
    parede_clara = paleta["parede_clara"]
    parede_escura = paleta["parede_escura"]
    fundacao = paleta["fundacao"]
    telhado = paleta["telhado"]
    telhado_claro = paleta["telhado_claro"]
    telhado_escuro = paleta["telhado_escuro"]

    # Sombra de contato e corpo da fachada. A fundação ganha blocos irregulares
    # em vez de repetir o tile de ruína usado pela implementação antiga.
    pygame.draw.ellipse(casa, (18, 13, 10, 85), (5, 73, 87, 12))
    pygame.draw.rect(casa, contorno, (7, 44, 82, 38))
    pygame.draw.rect(casa, parede, (9, 46, 78, 33))
    pygame.draw.rect(casa, parede_escura, (9, 74, 78, 5))
    pygame.draw.line(casa, madeira, (9, 51), (87, 51), 2)
    pygame.draw.line(casa, madeira, (9, 73), (87, 73), 2)
    for x in (9, 28, 67, 85):
        pygame.draw.rect(casa, madeira, (x, 48, 3, 28))

    for _ in range(32):
        x = rng.randint(13, 83)
        y = rng.randint(54, 71)
        cor = parede_clara if rng.random() < 0.55 else parede_escura
        casa.set_at((x, y), cor)

    x = 9
    linha = 0
    while x < 87:
        bloco = rng.choice((7, 8, 9, 10))
        pygame.draw.line(casa, contorno, (x, 78), (min(87, x + bloco), 78))
        if linha % 2:
            casa.set_at((x, 76), parede_escura)
        x += bloco
        linha += 1
    pygame.draw.line(casa, fundacao, (10, 80), (86, 80), 2)

    # A chaminé fica atrás da água do telhado; a parte inferior é escondida
    # pela cobertura, dando profundidade sem criar outra camada de render.
    casa.blit(chamine, (62, -8))

    pontos_telhado = (
        (2, 49), (10, 16), (47, 3), (85, 16),
        (94, 49), (89, 55), (7, 55),
    )
    pygame.draw.polygon(casa, contorno, pontos_telhado)
    pygame.draw.polygon(casa, telhado, (
        (6, 48), (13, 19), (47, 7), (82, 19),
        (90, 48), (86, 51), (10, 51),
    ))
    pygame.draw.line(casa, telhado_claro, (14, 18), (47, 7), 2)
    pygame.draw.line(casa, telhado_escuro, (47, 7), (82, 19), 2)
    pygame.draw.line(casa, telhado_escuro, (8, 51), (88, 51), 3)

    # Telhas escalonadas, com pequenas falhas determinísticas para que as três
    # casas compartilhem linguagem visual sem parecerem cópias exatas.
    for indice, y in enumerate(range(20, 49, 5)):
        margem = max(6, 13 - (y - 20) // 4)
        pygame.draw.line(
            casa,
            telhado_escuro,
            (margem, y),
            (largura - margem - 1, y),
        )
        inicio = margem + 3 + (indice % 2) * 4
        for x in range(inicio, largura - margem - 2, 8):
            if rng.random() < 0.16:
                continue
            pygame.draw.line(casa, telhado_escuro, (x, y), (x - 1, y + 3))
        if indice in (1, 4):
            brilho_x = rng.randint(margem + 6, largura - margem - 10)
            pygame.draw.line(casa, telhado_claro, (brilho_x, y - 1), (brilho_x + 5, y - 1))

    # Frontão central e vigas deixam a silhueta legível como casa mesmo vista
    # entre árvores altas.
    pygame.draw.polygon(casa, contorno, ((23, 53), (48, 28), (73, 53)))
    pygame.draw.polygon(casa, parede, ((27, 51), (48, 33), (69, 51)))
    pygame.draw.line(casa, madeira, (48, 31), (48, 53), 3)
    pygame.draw.line(casa, madeira, (25, 52), (48, 29), 2)
    pygame.draw.line(casa, madeira, (48, 29), (71, 52), 2)
    pygame.draw.line(casa, madeira, (22, 53), (74, 53), 3)

    janela_x = 3 if janela_esquerda else 61
    casa.blit(janela, (janela_x, 48))
    casa.blit(porta, (32, 36))

    # Degrau de pedra sob a porta e duas marcas curtas de desgaste na soleira.
    pygame.draw.rect(casa, contorno, (36, 81, 24, 4))
    pygame.draw.rect(casa, fundacao, (38, 81, 20, 2))
    pygame.draw.line(casa, parede_clara, (42, 82), (47, 82))
    pygame.draw.line(casa, parede_escura, (51, 83), (56, 83))

    return pygame.transform.scale(casa, (largura * 2, altura * 2))


def criar_poco_vila():
    w, h = 32, 32
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.ellipse(surf, (15, 12, 10, 80), (2, 22, 28, 10))
    stone_dark = (55, 52, 50)
    stone_mid = (110, 105, 100)
    stone_light = (160, 155, 150)
    pygame.draw.ellipse(surf, stone_dark, (4, 16, 24, 14))
    pygame.draw.ellipse(surf, stone_mid, (5, 17, 22, 12))
    pygame.draw.ellipse(surf, (20, 70, 120), (7, 19, 18, 8))
    pygame.draw.ellipse(surf, (40, 120, 180), (8, 20, 16, 6))
    pygame.draw.line(surf, (100, 180, 240), (11, 21), (15, 21), 1)
    pygame.draw.arc(surf, stone_light, (4, 16, 24, 14), 3.14, 0, 2)
    wood_dark = (60, 35, 20)
    wood_mid = (120, 75, 40)
    pygame.draw.rect(surf, wood_dark, (6, 6, 3, 14))
    pygame.draw.rect(surf, wood_mid, (7, 6, 1, 14))
    pygame.draw.rect(surf, wood_dark, (23, 6, 3, 14))
    pygame.draw.rect(surf, wood_mid, (24, 6, 1, 14))
    pygame.draw.rect(surf, wood_dark, (5, 5, 22, 3))
    pygame.draw.rect(surf, wood_mid, (6, 6, 20, 1))
    pygame.draw.line(surf, (180, 160, 120), (16, 8), (16, 15), 1)
    pygame.draw.rect(surf, wood_dark, (14, 15, 5, 4))
    pygame.draw.rect(surf, wood_mid, (15, 16, 3, 2))
    roof_dark = (70, 30, 20)
    roof_mid = (140, 60, 40)
    roof_light = (180, 90, 60)
    pygame.draw.polygon(surf, roof_dark, ((3, 6), (16, 0), (29, 6)))
    pygame.draw.polygon(surf, roof_mid, ((5, 5), (16, 1), (27, 5)))
    pygame.draw.line(surf, roof_light, (6, 5), (16, 1), 1)
    return pygame.transform.scale(surf, (w * 2, h * 2))


def criar_poste_lampiao():
    w, h = 16, 32
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.ellipse(surf, (15, 12, 10, 80), (3, 26, 10, 6))
    iron_dark = (30, 28, 32)
    iron_mid = (65, 62, 70)
    iron_light = (110, 105, 120)
    pygame.draw.rect(surf, iron_dark, (6, 27, 4, 4))
    pygame.draw.rect(surf, iron_mid, (7, 28, 2, 2))
    pygame.draw.rect(surf, iron_dark, (7, 8, 2, 20))
    pygame.draw.line(surf, iron_light, (7, 8), (7, 27), 1)
    pygame.draw.line(surf, iron_dark, (6, 8), (3, 8), 1)
    pygame.draw.line(surf, iron_dark, (3, 9), (3, 11), 1)
    pygame.draw.rect(surf, iron_dark, (1, 10, 5, 2))
    pygame.draw.rect(surf, (255, 200, 60), (2, 12, 3, 4))
    surf.set_at((3, 13), (255, 255, 200))
    pygame.draw.rect(surf, iron_dark, (1, 11, 5, 6), 1)
    surf.set_at((3, 17), iron_dark)
    return pygame.transform.scale(surf, (w * 2, h * 2))


def criar_barraca_mercado(cor_toldo=(185, 45, 40)):
    w, h = 32, 32
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.ellipse(surf, (15, 12, 10, 80), (2, 22, 28, 10))
    wood_dark = (60, 35, 20)
    wood_mid = (120, 75, 40)
    wood_light = (160, 105, 60)
    pygame.draw.rect(surf, wood_dark, (4, 18, 24, 11))
    pygame.draw.rect(surf, wood_mid, (5, 19, 22, 9))
    pygame.draw.line(surf, wood_light, (5, 19), (26, 19), 1)
    pygame.draw.rect(surf, (200, 100, 30), (7, 16, 5, 4))
    pygame.draw.rect(surf, (60, 160, 50), (14, 16, 5, 4))
    pygame.draw.rect(surf, (180, 40, 60), (21, 16, 4, 4))
    pygame.draw.line(surf, wood_dark, (4, 5), (4, 18), 1)
    pygame.draw.line(surf, wood_dark, (27, 5), (27, 18), 1)
    stripe1 = cor_toldo
    stripe2 = (240, 235, 220)
    canopy_rect = pygame.Rect(2, 2, 28, 9)
    pygame.draw.rect(surf, stripe1, canopy_rect)
    for x in range(2, 30, 6):
        pygame.draw.rect(surf, stripe2, (x, 2, 3, 9))
    pygame.draw.line(surf, (40, 20, 15), (2, 2), (29, 2), 1)
    pygame.draw.line(surf, (40, 20, 15), (2, 11), (29, 11), 1)
    for x in range(2, 29, 4):
        surf.set_at((x + 1, 12), stripe1 if (x // 4) % 2 == 0 else stripe2)
        surf.set_at((x + 2, 12), stripe1 if (x // 4) % 2 == 0 else stripe2)
    return pygame.transform.scale(surf, (w * 2, h * 2))


def criar_barril():
    w, h = 16, 16
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.ellipse(surf, (15, 12, 10, 70), (2, 10, 12, 5))
    wood_dark = (55, 30, 15)
    wood_mid = (115, 70, 35)
    wood_light = (160, 105, 55)
    iron = (60, 65, 70)
    pygame.draw.ellipse(surf, wood_dark, (2, 1, 12, 14))
    pygame.draw.ellipse(surf, wood_mid, (3, 2, 10, 12))
    pygame.draw.line(surf, wood_light, (4, 4), (4, 11), 1)
    pygame.draw.line(surf, iron, (2, 4), (13, 4), 1)
    pygame.draw.line(surf, iron, (2, 11), (13, 11), 1)
    return pygame.transform.scale(surf, (w * 2, h * 2))


def criar_caixote():
    w, h = 16, 16
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.ellipse(surf, (15, 12, 10, 70), (1, 10, 14, 5))
    wood_dark = (65, 40, 20)
    wood_mid = (130, 85, 45)
    wood_light = (175, 120, 65)
    pygame.draw.rect(surf, wood_dark, (1, 2, 14, 13))
    pygame.draw.rect(surf, wood_mid, (2, 3, 12, 11))
    pygame.draw.rect(surf, wood_dark, (2, 3, 12, 11), 1)
    pygame.draw.line(surf, wood_dark, (3, 4), (12, 12), 1)
    pygame.draw.line(surf, wood_light, (3, 3), (12, 3), 1)
    return pygame.transform.scale(surf, (w * 2, h * 2))


def criar_saca():
    w, h = 16, 16
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.ellipse(surf, (15, 12, 10, 70), (1, 10, 14, 5))
    cloth_dark = (100, 85, 55)
    cloth_mid = (170, 150, 105)
    cloth_light = (210, 190, 140)
    pygame.draw.ellipse(surf, cloth_dark, (2, 3, 12, 12))
    pygame.draw.ellipse(surf, cloth_mid, (3, 4, 10, 10))
    pygame.draw.rect(surf, cloth_dark, (6, 1, 4, 3))
    pygame.draw.line(surf, (140, 50, 40), (6, 3), (9, 3), 1)
    pygame.draw.line(surf, cloth_light, (5, 6), (7, 10), 1)
    return pygame.transform.scale(surf, (w * 2, h * 2))


def criar_lenha():
    w, h = 16, 16
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.ellipse(surf, (15, 12, 10, 70), (1, 11, 14, 4))
    bark = (55, 35, 20)
    wood = (175, 140, 95)
    pygame.draw.rect(surf, bark, (2, 9, 12, 4))
    pygame.draw.ellipse(surf, wood, (1, 9, 4, 4))
    pygame.draw.rect(surf, bark, (3, 6, 11, 4))
    pygame.draw.ellipse(surf, wood, (2, 6, 4, 4))
    pygame.draw.rect(surf, bark, (4, 3, 9, 4))
    pygame.draw.ellipse(surf, wood, (3, 3, 4, 4))
    return pygame.transform.scale(surf, (w * 2, h * 2))


def criar_vaso_flores():
    w, h = 16, 16
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.ellipse(surf, (15, 12, 10, 70), (2, 11, 12, 4))
    clay_dark = (110, 45, 25)
    clay_mid = (170, 75, 45)
    clay_light = (210, 110, 70)
    pygame.draw.polygon(surf, clay_dark, ((3, 6), (13, 6), (11, 14), (5, 14)))
    pygame.draw.polygon(surf, clay_mid, ((4, 7), (12, 7), (10, 13), (6, 13)))
    pygame.draw.rect(surf, clay_dark, (2, 5, 12, 2))
    pygame.draw.line(surf, clay_light, (3, 5), (12, 5), 1)
    pygame.draw.ellipse(surf, (35, 110, 40), (2, 1, 12, 6))
    surf.set_at((4, 2), (240, 60, 80))
    surf.set_at((8, 1), (240, 220, 60))
    surf.set_at((11, 2), (180, 80, 220))
    return pygame.transform.scale(surf, (w * 2, h * 2))


def criar_placa():
    w, h = 16, 16
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.ellipse(surf, (15, 12, 10, 70), (5, 12, 6, 4))
    wood_dark = (60, 35, 20)
    wood_mid = (120, 75, 40)
    wood_light = (160, 105, 60)
    pygame.draw.rect(surf, wood_dark, (7, 6, 2, 9))
    pygame.draw.polygon(surf, wood_dark, ((2, 2), (11, 2), (14, 5), (11, 8), (2, 8)))
    pygame.draw.polygon(surf, wood_mid, ((3, 3), (10, 3), (13, 5), (10, 7), (3, 7)))
    pygame.draw.line(surf, wood_light, (3, 3), (10, 3), 1)
    pygame.draw.line(surf, wood_dark, (4, 5), (9, 5), 1)
    return pygame.transform.scale(surf, (w * 2, h * 2))


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

def criar_canto_texturizado(texture, corner, seed):
    w, h = texture.get_size()
    border = pygame.Surface((w, h), pygame.SRCALPHA)
    rng = random.Random(seed)
    radius = 7.0
    for y in range(h):
        for x in range(w):
            cx = 0 if "left" in corner else (w - 1)
            cy = 0 if "top" in corner else (h - 1)
            dist = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
            if dist < radius:
                border.set_at((x, y), texture.get_at((x, y)))
            elif dist < radius + 2.5 and (x * 7 + y * 11 + seed) % 2 == 0:
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

    # Cada bloco horizontal de 96 px é um frame de 100 ms. Suas margens usam
    # os mesmos autotiles nativos de 16 px do restante do cenário.
    SPRITES.update(carregar_bordas_lagoa(nature_base))

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
        ("grass_edge", grass),
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
        for index, corner in enumerate(("top_left", "top_right", "bottom_left", "bottom_right")):
            SPRITES[f"{prefix}_{corner}"] = criar_canto_texturizado(
                texture, corner, seed=99 + index * 17
            )

    # Personagem e inimigos do Pixel Crawler Free Pack (Anokolisa).
    SPRITES["player_survivor"] = carregar_personagem_pixel_crawler()
    SPRITES["enemy_skeleton"] = carregar_inimigo_pixel_crawler("skeleton")
    SPRITES["enemy_orc_rogue"] = carregar_inimigo_pixel_crawler("orc_rogue")
    SPRITES["enemy_orc_warrior"] = carregar_inimigo_pixel_crawler("orc_warrior")
    SPRITES["enemy_night_stalker"] = criar_variacao_sombra(SPRITES["enemy_orc_rogue"])

    # Animais da Fazenda e de Caça (CraftPix Packs)
    SPRITES.update(carregar_animais_fazenda())
    SPRITES.update(carregar_animais_caca())

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
    SPRITES.update(carregar_rochas(nature_base))

    decoration_regions = {
        "nature_bush_green": ("vegetation.png", (0, 0, 32, 32)),
        "nature_bush_autumn": ("vegetation.png", (144, 0, 32, 32)),
        "nature_sprout": ("vegetation.png", (32, 144, 16, 16)),
        "nature_leaf_cluster": ("vegetation.png", (80, 144, 32, 32)),
        "nature_plant_tall": ("vegetation.png", (112, 160, 32, 32)),
        "nature_cattail": ("vegetation.png", (144, 160, 16, 32)),
        "nature_flower_purple": ("vegetation.png", (192, 160, 16, 32)),
        "nature_mushroom": ("vegetation.png", (48, 336, 16, 16)),
        "nature_mushroom_toxic": ("vegetation.png", (16, 352, 16, 16)),
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
        "farm_fence_top": ("building_props.png", (16, 176, 48, 16)),
        "farm_fence_bottom": ("building_props.png", (16, 240, 48, 16)),
        "farm_fence_left": ("building_props.png", (0, 208, 16, 16)),
        "farm_fence_right": ("building_props.png", (64, 208, 16, 16)),
        "farm_fence_h": ("building_props.png", (32, 176, 16, 16)),
        "farm_fence_h_left": ("building_props.png", (16, 176, 16, 16)),
        "farm_fence_h_mid": ("building_props.png", (32, 176, 16, 16)),
        "farm_fence_h_right": ("building_props.png", (48, 176, 16, 16)),
        "farm_fence_v": ("building_props.png", (0, 208, 16, 16)),
        "farm_fence_corner_tl": ("building_props.png", (0, 192, 16, 16)),
        "farm_fence_corner_tr": ("building_props.png", (64, 192, 16, 16)),
        "farm_fence_corner_bl": ("building_props.png", (0, 224, 16, 16)),
        "farm_fence_corner_br": ("building_props.png", (64, 224, 16, 16)),
        # Partes de casa para compor vilas
        "house_door_front": ("building_props.png", (0, 16, 32, 48)),
        "house_door_wood": ("building_props.png", (96, 16, 32, 48)),
        "house_window_front": ("building_props.png", (64, 64, 32, 32)),
        "house_window_shutters": ("building_props.png", (128, 64, 32, 32)),
        "house_chimney": ("building_props.png", (0, 64, 32, 64)),
        "house_bench": ("building_props.png", (80, 160, 64, 16)),
        "house_chest": ("building_props.png", (112, 128, 32, 32)),
    }
    for sprite_name, (atlas_name, rect) in decoration_regions.items():
        SPRITES[sprite_name] = carregar_regiao_atlas(
            f"{nature_base}/{atlas_name}", rect, escala=2.0
        )

    # Casas de vila são sprites completos: telhado, frontão, fachada e
    # fundação pertencem à mesma silhueta. Portas, janelas e chaminé continuam
    # vindo do atlas do Pixel Crawler para manter a linguagem do restante do
    # cenário.
    building_atlas = f"{nature_base}/building_props.png"
    portas = {
        "plank": carregar_regiao_atlas(building_atlas, (96, 16, 32, 48), escala=1.0),
        "banded": carregar_regiao_atlas(building_atlas, (128, 16, 32, 48), escala=1.0),
        "steel": carregar_regiao_atlas(building_atlas, (160, 16, 32, 48), escala=1.0),
    }
    janelas = {
        "arch": carregar_regiao_atlas(building_atlas, (64, 64, 32, 32), escala=1.0),
        "green": carregar_regiao_atlas(building_atlas, (128, 64, 32, 32), escala=1.0),
        "wood": carregar_regiao_atlas(building_atlas, (64, 96, 32, 32), escala=1.0),
    }
    chamine = carregar_regiao_atlas(
        building_atlas, (0, 64, 32, 32), escala=1.0
    )
    estilos_casa = {
        "village_house_amber": (
            portas["plank"],
            janelas["arch"],
            {
                "contorno": (45, 30, 23),
                "madeira": (88, 49, 27),
                "parede": (194, 158, 103),
                "parede_clara": (226, 194, 128),
                "parede_escura": (145, 111, 73),
                "fundacao": (111, 105, 88),
                "telhado": (133, 86, 40),
                "telhado_claro": (180, 124, 57),
                "telhado_escuro": (79, 47, 29),
            },
            11,
            False,
        ),
        "village_house_brick": (
            portas["banded"],
            janelas["wood"],
            {
                "contorno": (48, 29, 26),
                "madeira": (82, 43, 28),
                "parede": (205, 171, 116),
                "parede_clara": (232, 204, 151),
                "parede_escura": (157, 118, 83),
                "fundacao": (107, 101, 91),
                "telhado": (146, 68, 44),
                "telhado_claro": (193, 99, 55),
                "telhado_escuro": (82, 39, 33),
            },
            23,
            True,
        ),
        "village_house_moss": (
            portas["steel"],
            janelas["green"],
            {
                "contorno": (38, 36, 27),
                "madeira": (72, 50, 30),
                "parede": (171, 158, 119),
                "parede_clara": (205, 191, 145),
                "parede_escura": (121, 116, 82),
                "fundacao": (91, 96, 78),
                "telhado": (91, 111, 47),
                "telhado_claro": (139, 150, 62),
                "telhado_escuro": (52, 68, 34),
            },
            37,
            False,
        ),
    }
    for nome, (porta, janela, paleta, seed, janela_esquerda) in estilos_casa.items():
        SPRITES[nome] = criar_casa_vila(
            porta,
            janela,
            chamine,
            paleta,
            seed=seed,
            janela_esquerda=janela_esquerda,
        )

    # Props da Cidade e Vilarejo
    SPRITES["town_well"] = criar_poco_vila()
    SPRITES["street_lamp"] = criar_poste_lampiao()
    SPRITES["market_stall"] = criar_barraca_mercado()
    SPRITES["barrel_wood"] = criar_barril()
    SPRITES["crate_wood"] = criar_caixote()
    SPRITES["sack_grain"] = criar_saca()
    SPRITES["logs_firewood"] = criar_lenha()
    SPRITES["flower_pot"] = criar_vaso_flores()
    SPRITES["signpost"] = criar_placa()
    SPRITES["town_bench"] = carregar_regiao_atlas(f"{nature_base}/building_props.png", (16, 160, 32, 16), escala=2.0)
    SPRITES["town_bench_large"] = carregar_regiao_atlas(f"{nature_base}/building_props.png", (80, 160, 64, 16), escala=2.0)
    SPRITES["blacksmith_furnace"] = carregar_regiao_atlas("sprites/pixel_crawler/town/furnace.png", (0, 96, 32, 32), escala=2.0)
    SPRITES["blacksmith_anvil"] = carregar_regiao_atlas("sprites/pixel_crawler/town/anvil.png", (224, 0, 32, 32), escala=2.0)
    SPRITES["town_workbench"] = carregar_regiao_atlas("sprites/pixel_crawler/town/workbench.png", (64, 64, 32, 32), escala=2.0)
    SPRITES["crate_carrots"] = carregar_regiao_atlas(f"{nature_base}/farm.png", (144, 0, 16, 16), escala=2.0)
    SPRITES["crate_beets"] = carregar_regiao_atlas(f"{nature_base}/farm.png", (144, 32, 16, 16), escala=2.0)
    SPRITES["crate_cabbage"] = carregar_regiao_atlas(f"{nature_base}/farm.png", (144, 64, 16, 16), escala=2.0)
    SPRITES["scarecrow"] = carregar_regiao_atlas(f"{nature_base}/farm.png", (224, 32, 16, 32), escala=2.0)

    # NPCs Urbanos (Pixel Crawler)
    SPRITES["npc_peasant"] = carregar_npc_pixel_crawler("peasant")
    SPRITES["npc_guard"] = carregar_npc_pixel_crawler("knight")
    SPRITES["npc_tavern"] = carregar_npc_pixel_crawler("tavern")
    SPRITES["npc_mage"] = carregar_npc_pixel_crawler("wizzard")
    SPRITES["npc_merchant"] = carregar_npc_pixel_crawler("rogue")

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
