import sys
sys.path.insert(0, 'src')
import os
import pygame
from core import config
from core.context import GameContext
from core.content import ContentCatalog
from core.input_manager import InputManager
from core.time_system import TimeSystem
from core import camera
from graphics import recursos
from graphics.renderer import Renderer
from graphics.ui import UI
from entities.actor import Entidade
from map.map_gen import Mapa

pygame.init()
screen = pygame.display.set_mode((config.LARGURA_TELA, config.ALTURA_TELA), pygame.NOFRAME)

recursos.carregar_tudo()
catalog = ContentCatalog.load_default()
context = GameContext(input=InputManager(), content=catalog)

relogio = TimeSystem()
relogio.tempo_total = relogio.duracao_dia * 0.70
relogio.calcular_cor()

cam = camera.Camera()
mapa = Mapa(context, seed=42)
mapa.camera = cam
mapa.time_system = relogio

ui = UI()
ui.show_banner("A NOITE CAIU... ABRIGUE-SE PERTO DO FOGO!", color=(255, 75, 75), duration=5.0)

# Posiciona o jogador perto de uma fogueira conhecida ou cria uma fogueira no acampamento
nearest_bonfire = mapa.get_nearest_bonfire(mapa.jogador.x, mapa.jogador.y)
if nearest_bonfire:
    bx, by, _ = nearest_bonfire
    mapa.jogador.x = bx + 1.5
    mapa.jogador.y = by + 0.5
else:
    # Adiciona uma fogueira perto do jogador para o teste
    fx, fy = int(mapa.jogador.x) + 3, int(mapa.jogador.y)
    mapa.bonfire_positions.add((fx, fy))
    tile = mapa.obter_tile(fx, fy)
    if tile:
        tile.decoracao = "nature_bonfire"
        tile.bloqueado = True

# Spawna 2 Stalkers Noturnos no escuro a 6 tiles de distância
stalker1 = Entidade(mapa.jogador.x + 5.5, mapa.jogador.y + 1.5, "Stalker Noturno", context)
stalker2 = Entidade(mapa.jogador.x - 5.0, mapa.jogador.y - 2.0, "Stalker Noturno", context)
mapa.entidades.append(stalker1)
mapa.entidades.append(stalker2)
mapa.spatial_index.insert(stalker1)
mapa.spatial_index.insert(stalker2)

# Simula 60 frames (1 segundo de runtime)
for _ in range(60):
    dt = 1.0 / 60.0
    ui.update(dt)
    mapa.update(dt)
    relogio.update(dt)

# Renderiza um frame
surface = pygame.Surface((config.LARGURA_TELA, config.ALTURA_TELA))
surface.fill(config.PRETO)
renderer = Renderer(camera=mapa.camera)
cor_do_ceu = relogio.obter_cor()
renderer.draw(surface, mapa, cor_do_ceu)
ui.draw(surface, mapa.jogador, audio=context.audio, time_system=relogio)

os.makedirs("scratch", exist_ok=True)
out_path = "scratch/night_showcase.png"
pygame.image.save(surface, out_path)
print(f"Showcase salvo com sucesso em {out_path}!")
print(f"Fase: {relogio.phase_label}, Jogador perto do fogo: {getattr(mapa.jogador, 'near_campfire', False)}")
print(f"Stalkers vivos: {sum(1 for e in mapa.entidades if e.nome == 'Stalker Noturno')}")
