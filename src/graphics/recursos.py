# src/recursos.py
import pygame
from . import config

SPRITES = {}

def criar_sprite_provisorio(cor):
    surf = pygame.Surface((32, 32))
    surf.fill(cor)
    return surf

# --- A FÁBRICA UNIVERSAL DE SPRITES ---
def carregar_spritesheet(nome_arquivo, colunas, escala=2.0):
    """
    Corta qualquer imagem em tira (strip) horizontal.
    nome_arquivo: ex: 'tree.png'
    colunas: quantos quadros tem na tira (ex: 16 para árvore, 6 para lhama)
    escala: quanto aumentar o tamanho (padrão dobra o tamanho)
    """
    caminho = f"assets/{nome_arquivo}"
    lista_frames = []
    try:
        sheet = pygame.image.load(caminho).convert_alpha()
        
        # Matemática automática
        largura_total = sheet.get_width()
        altura_total = sheet.get_height()
        largura_frame = largura_total // colunas
        
        # Tamanho final desejado
        novo_w = int(largura_frame * escala)
        novo_h = int(altura_total * escala)

        for i in range(colunas):
            # O retângulo de corte desliza para a direita
            rect = pygame.Rect(i * largura_frame, 0, largura_frame, altura_total)
            
            # Corta
            frame = sheet.subsurface(rect)
            
            # Aumenta
            frame = pygame.transform.scale(frame, (novo_w, novo_h))
            lista_frames.append(frame)
            
        print(f"[OK] Spritesheet carregado: {nome_arquivo} ({colunas} frames)")
        return lista_frames

    except Exception as e:
        print(f"[ERRO] Falha ao carregar {nome_arquivo}: {e}")
        return [criar_sprite_provisorio(config.VERMELHO)]

def carregar_estatico(nome_arquivo, escala=2.0):
    """Para imagens que não se mexem (Pedra, Parede, Itens)"""
    try:
        img = pygame.image.load(f"assets/{nome_arquivo}").convert_alpha()
        img = pygame.transform.scale(img, (int(img.get_width()*escala), int(img.get_height()*escala)))
        return img
    except: return criar_sprite_provisorio(config.CINZA_CLARO)

def carregar_tudo():
    print("--- Carregando Assets ---")
    
    # --- ANIMAÇÕES (Usa a função universal) ---
    # Lhama: 6 quadros
    SPRITES["llama_run"] = carregar_spritesheet("llama.png", colunas=6, escala=2.0)
    
    # Árvore: 16 quadros
    SPRITES["tree"] = carregar_spritesheet("tree.png", colunas=18, escala=2.0)
    SPRITES["red_tree"] = carregar_spritesheet("RedTree.png",colunas=1,escala=2.0)
    SPRITES["grass"] = carregar_estatico("grass.png", escala=2.0)
    
    # --- ESTÁTICOS ---
    SPRITES["rock"] = carregar_estatico("rock.png")
    SPRITES["wall"] = carregar_estatico("wall.png", escala=1.0)
    SPRITES["house"] = carregar_estatico("house.png", escala=1.0)
    SPRITES["fireball"] = carregar_estatico("fireball.png", escala=1.0)
    
    # Placeholders para inimigos (por enquanto)
    SPRITES["orc_run"] = [criar_sprite_provisorio(config.VERDE)] 
    SPRITES["troll_run"] = [criar_sprite_provisorio(config.VERMELHO)]
    SPRITES["boss_run"] = [criar_sprite_provisorio(config.ROXO)]
    
    # --- GERADOR DE SOMBRA (CORRIGIDO COM MARGEM) ---
    largura_base = 32
    altura_base = 16
    margem = 4 # Adiciona 4px de espaço extra total (2px de cada lado)
    
    # 1. Cria uma superfície MAIOR (36x20) transparente
    sombra = pygame.Surface((largura_base + margem, altura_base + margem), pygame.SRCALPHA)
    
    # 2. Desenha a elipse no MEIO, pulando a margem (x=2, y=2)
    # Isso garante que a borda suave (anti-aliasing) caiba inteira sem cortar
    pygame.draw.ellipse(sombra, (0, 0, 0, 70), [margem//2, margem//2, largura_base, altura_base])
    
    SPRITES["shadow"] = sombra