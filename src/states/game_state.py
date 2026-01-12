# src/states/game_state.py
import pygame
from states.game_over_state import GameOverState
from core.state_manager import BaseState
from core import config
from map import map_gen
from core import camera
from graphics import ui
from graphics.renderer import Renderer
from core.time_system import TimeSystem
from core.input_manager import Actions
from states.pause_state import PauseState
from states.inventory_state import InventoryState

class GameState(BaseState):
    def __init__(self, manager, registry, input_manager):
        super().__init__(manager, registry, input_manager)
        
        self.relogio = TimeSystem()
        self.mapa = map_gen.Mapa()
        self.camera = camera.Camera()
        self.renderer = Renderer(self.camera)
        self.ui = ui.UI()
        
    def enter(self):
        print("Entrando no GameState")

    def handle_input(self, event):
        # A lógica bruta saiu daqui, pois o InputManager processa antes.
        pass

    def update(self, dt):
        # --- 1. MOVIMENTO (CONTÍNUO - IS_HELD) ---
        dx, dy = 0, 0
        
        # O InputManager verifica as teclas
        if self.input.is_held(Actions.MOVE_UP):    dy = -1
        if self.input.is_held(Actions.MOVE_DOWN):  dy = 1
        if self.input.is_held(Actions.MOVE_LEFT):  dx = -1
        if self.input.is_held(Actions.MOVE_RIGHT): dx = 1
        
        # Verifica se há intenção de movimento
        if dx != 0 or dy != 0:
            # Chamamos o physics.move, que já lida com colisão E normalização de diagonal
            self.mapa.jogador.physics.move(dx, dy, self.mapa)
        else:
            # Se não houver input, garantimos que ele pare
            self.mapa.jogador.moving = False
        
        if self.input.is_pressed(Actions.PAUSE):
            self.manager.push(PauseState)
            return

        # --- 2. COMBATE (AÇÃO ÚNICA - IS_PRESSED) ---
        screen_mx, screen_my = self.input.get_mouse_position()
        
        # Converte para coordenadas do mundo
        world_mx = (screen_mx + self.camera.camera_x) / config.TAMANHO_TILE
        world_my = (screen_my + self.camera.camera_y) / config.TAMANHO_TILE
        
        # Verifica ataques
        if self.input.is_pressed(Actions.ATTACK_PRIMARY):
            self.mapa.jogador.atacar_espada(world_mx, world_my, self.mapa)
            
        if self.input.is_pressed(Actions.ATTACK_SECONDARY):
            self.mapa.jogador.atirar(world_mx, world_my, self.mapa, "player")

        if self.mapa.jogador.hp <= 0:
            print("Jogador morreu! Indo para Game Over.")
            self.manager.change(GameOverState)

        # --- 3. ATUALIZAÇÃO DOS SISTEMAS ---
        self.mapa.update()
        self.relogio.update(dt)
        if self.mapa.jogador:
            self.camera.update(self.mapa.jogador.x, self.mapa.jogador.y)

    def draw(self, surface):
        surface.fill(config.PRETO)
        cor_do_ceu = self.relogio.obter_cor()
        self.renderer.draw(surface, self.mapa, cor_do_ceu)
        self.ui.draw(surface, self.mapa.jogador)