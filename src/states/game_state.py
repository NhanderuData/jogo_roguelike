import pygame
from core.state_manager import BaseState
from core import config
from map import map_gen
from core import camera
from graphics import ui
from graphics.renderer import Renderer
from core.time_system import TimeSystem
# Importe outros módulos necessários conforme seu game.py original

class GameState(BaseState):
    def __init__(self, manager, registry):
        super().__init__(manager, registry)
        # Inicialização que antes estava no __init__ do Game()
        self.relogio = TimeSystem()
        self.mapa = map_gen.Mapa()
        self.camera = camera.Camera()
        self.renderer = Renderer(self.camera)
        self.ui = ui.UI()
        
    def enter(self):
        # Se quiser tocar música ou resetar algo ao entrar
        print("Entrando no GameState")

    def handle_input(self, event):
        # Lógica de input que estava no handle_input do Game()
        # NOTA: Isso será substituído pelo InputManager no futuro passo 2
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = pygame.mouse.get_pos()
            world_mx = (mx + self.camera.camera_x) / config.TAMANHO_TILE
            world_my = (my + self.camera.camera_y) / config.TAMANHO_TILE
            
            if event.button == 1:
                self.mapa.jogador.atacar_espada(world_mx, world_my, self.mapa)
            elif event.button == 3:
                self.mapa.jogador.atirar(world_mx, world_my, self.mapa, "player")

    def update(self, dt):
        # Lógica de movimento contínuo (teclado pressionado)
        # Idealmente moveremos isso para InputManager depois
        keys = pygame.key.get_pressed()
        dx, dy = 0, 0
        if keys[pygame.K_w]: dy = -1
        if keys[pygame.K_s]: dy = 1
        if keys[pygame.K_a]: dx = -1
        if keys[pygame.K_d]: dx = 1
        
        if dx != 0 and dy != 0:
            dx *= 0.707; dy *= 0.707

        if dx != 0 or dy != 0:
            p = self.mapa.jogador
            nx = p.x + dx * p.speed
            if not self.mapa.is_blocked_terrain(nx, p.y): p.x = nx
            ny = p.y + dy * p.speed
            if not self.mapa.is_blocked_terrain(p.x, ny): p.y = ny
            p.moving = True
        elif self.mapa.jogador:
            self.mapa.jogador.moving = False

        # Updates dos sistemas
        self.mapa.update()
        self.relogio.update(dt)
        if self.mapa.jogador:
            self.camera.update(self.mapa.jogador.x, self.mapa.jogador.y)

    def draw(self, surface):
        surface.fill(config.PRETO)
        cor_do_ceu = self.relogio.obter_cor()
        self.renderer.draw(surface, self.mapa, cor_do_ceu)
        self.ui.draw(surface, self.mapa.jogador)