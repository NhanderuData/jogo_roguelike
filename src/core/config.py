# src/graphics/config.py
import pygame

# Tela
LARGURA_TELA = 1500
ALTURA_TELA = 920
FPS = 60
TAMANHO_TILE = 32

# Mundo
TAMANHO_CHUNK = 30
CHUNKS_X = 5
CHUNKS_Y = 5
LARGURA_MAPA = TAMANHO_CHUNK * CHUNKS_X
ALTURA_MAPA = TAMANHO_CHUNK * CHUNKS_Y

# Cores
PRETO = (0, 0, 0)
BRANCO = (255, 255, 255)
CINZA_CLARO = (100, 100, 100)
CINZA_ESCURO = (40, 40, 40)
VERMELHO = (200, 50, 50)
VERDE = (50, 200, 50)
AZUL = (50, 50, 200)
AMARELO = (255, 255, 0)
ROXO = (160, 32, 240)
LARANJA = (255, 140, 0)
MARROM_ESTRADA = (160, 82, 45)
AZUL_PROFUNDO = (30, 80, 150)  # Azul mais escuro
COR_AREIA = (240, 230, 140)    # Amarelo queimado

# --- COR DA ÁGUA ATUALIZADA ---
AZUL_AGUA = (60, 160, 240) # Azul estilo "Minecraft" / Zelda
MARROM_CASA = (139, 69, 19)

# Gameplay
# Quadros de animação por segundo.
VELOCIDADE_ANIMACAO = 9.0

CHAO = 0
PAREDE = 1
ARVORE = 2
AGUA = 3
CASA = 4
ROCHA = 5
TAPETE = 6

# --- CONFIGURAÇÃO VISUAL DOS TILES ---
# Dicionário que guarda: Escala da Sombra e Ajuste Y (Altura)
# Se o tile não estiver aqui, ele não tem sombra.
VISUAL_TILES = {
    ARVORE: { "escala": 1.4, "ajuste_y": 0 },
    ROCHA:  { "escala": 0.8, "ajuste_y": 0 },
    # No futuro:
    # CASA: { "escala": 3.0, "ajuste_y": 10 },
}

LAYER_CHAO = 0       # Terra, Grama
LAYER_DECORACAO = 1  # Tapetes, poças, flores baixas
LAYER_SOMBRA = 2     # Sombras dos personagens
LAYER_CORPO = 3      # Personagens, Inimigos, Troncos de árvore
LAYER_TOPO = 4       # Copa das árvores, telhados (passar por baixo)
LAYER_AEREO = 5      # Pássaros, projéteis voando alto
LAYER_FX = 6         # Partículas, explosões
LAYER_UI = 7         # Barras de vida, texto
