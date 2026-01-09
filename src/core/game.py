# src/game.py
import pygame
from graphics import config
from map import map_gen
from core import camera
from graphics import ui
from graphics import recursos
from graphics.renderer import Renderer
from core.time_system import TimeSystem

class Game:
    def __init__(self):
        pygame.init()
        self.relogio = TimeSystem()
        
        # 1. Configura Telaa
        self.screen = pygame.display.set_mode(
            (config.LARGURA_TELA, config.ALTURA_TELA),  # Argumento 1: A Tupla de tamanho
            pygame.FULLSCREEN | pygame.SCALED           # Argumento 2: As Flags
        )
        pygame.display.set_caption("Roguelike - Rafael Version")
        self.clock = pygame.time.Clock()
        self.running = True

        # 2. Carrega Assets
        recursos.carregar_tudo()

        # 3. Inicializa Sistemas
        self.mapa = map_gen.Mapa()
        self.camera = camera.Camera()
        
        # O Renderer nasce aqui, recebendo a câmera!
        self.renderer = Renderer(self.camera) 
        
        self.ui = ui.UI()

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                # Converte pixel da tela para grid do mundo usando a câmera
                world_mx = (mx + self.camera.camera_x) / config.TAMANHO_TILE
                world_my = (my + self.camera.camera_y) / config.TAMANHO_TILE
                
                if event.button == 1:
                    self.mapa.jogador.atacar_espada(world_mx, world_my, self.mapa)
                elif event.button == 3:
                    self.mapa.jogador.atirar(world_mx, world_my, self.mapa, "player")

        # Movimento do Jogador
        keys = pygame.key.get_pressed()
        dx, dy = 0, 0
        if keys[pygame.K_w]: dy = -1
        if keys[pygame.K_s]: dy = 1
        if keys[pygame.K_a]: dx = -1
        if keys[pygame.K_d]: dx = 1
        
        # Normaliza diagonal
        if dx != 0 and dy != 0:
            dx *= 0.707; dy *= 0.707

        # Aplica movimento com colisão
        if dx != 0 or dy != 0:
            p = self.mapa.jogador
            nx = p.x + dx * p.speed
            if not self.mapa.is_blocked_terrain(nx, p.y): p.x = nx
            ny = p.y + dy * p.speed
            if not self.mapa.is_blocked_terrain(p.x, ny): p.y = ny
            p.moving = True
        elif self.mapa.jogador:
            self.mapa.jogador.moving = False

    def update(self):
        # Atualiza a lógica do mapa (ISSO FAZ OS INIMIGOS SE MEXEREM)
        self.mapa.update()
        
        # Atualiza a câmera para seguir o jogador
        if self.mapa.jogador:
            self.camera.update(self.mapa.jogador.x, self.mapa.jogador.y)

    def draw(self):
        self.screen.fill(config.PRETO)
        
        # --- AQUI ESTAVA O ERRO ---
        # Antes: self.camera.draw(...) -> A câmera não sabe mais desenhar!
        # Agora: Chamamos o especialista (Renderer)
        self.renderer.draw(self.screen, self.mapa)
        
        self.ui.draw(self.screen, self.mapa.jogador)
        pygame.display.flip()

    def run(self):
        while self.running:
            self.handle_input()
            self.update()
            self.draw()
            self.clock.tick(60)
        pygame.quit()