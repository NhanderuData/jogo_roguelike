# src/states/game_state.py
import pygame
import random
from core.state_manager import BaseState, Scene
from core import config
from map import map_gen
from core import camera
from graphics import ui
from graphics.renderer import Renderer
from core.time_system import TimeSystem
from core.input_manager import Actions

class GameState(BaseState):
    def __init__(self, manager, context):
        super().__init__(manager, context)
        
        self.relogio = TimeSystem()
        self.mapa = map_gen.Mapa(context)
        self.camera = camera.Camera()
        self.mapa.camera = self.camera
        self.renderer = Renderer(self.camera)
        self.ui = ui.UI()
        self.ambient_sound_timer = random.uniform(6.0, 12.0)
        
    def enter(self):
        print("Entrando no GameState")
        self.context.audio.play_ambient("wind")

    def exit(self):
        self.context.audio.stop_ambient()

    def update(self, dt):
        if self.input.is_pressed(Actions.TOGGLE_DEBUG):
            config.DEBUG_MODE = not config.DEBUG_MODE

        self.ambient_sound_timer -= dt
        if self.ambient_sound_timer <= 0:
            self.context.audio.play("bird", 0.16)
            self.ambient_sound_timer = random.uniform(8.0, 16.0)
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
            speed_boost = self.mapa.jogador.status.speed_multiplier
            self.mapa.jogador.physics.move(
                dx * speed_boost, dy * speed_boost, self.mapa, dt
            )
        else:
            # Se não houver input, garantimos que ele pare
            self.mapa.jogador.moving = False
        
        if self.input.is_pressed(Actions.PAUSE):
            self.manager.push(Scene.PAUSE)
            return
        
        if self.input.is_pressed(Actions.INVENTORY):
            # Passamos o jogador como argumento para o estado saber o que mostrar
            self.manager.push(Scene.INVENTORY, player=self.mapa.jogador)
            return

        weapon_actions = (
            Actions.WEAPON_1,
            Actions.WEAPON_2,
            Actions.WEAPON_3,
            Actions.WEAPON_4,
        )
        for slot, action in enumerate(weapon_actions):
            if self.input.is_pressed(action):
                self.mapa.jogador.weapons.select_slot(slot)

        if self.input.is_pressed(Actions.RELOAD):
            self.mapa.jogador.weapons.start_reload()

        # --- 2. COMBATE (AÇÃO ÚNICA - IS_PRESSED) ---
        screen_mx, screen_my = self.input.get_mouse_position()
        
        # Converte para coordenadas do mundo
        world_mx = (screen_mx + self.camera.camera_x) / config.TAMANHO_TILE
        world_my = (screen_my + self.camera.camera_y) / config.TAMANHO_TILE
        
        weapon = self.mapa.jogador.weapons.current
        wants_to_attack = self.input.is_pressed(Actions.ATTACK_PRIMARY)
        if weapon.kind == "ranged" and weapon.cooldown <= 0.1:
            wants_to_attack = wants_to_attack or self.input.is_held(Actions.ATTACK_PRIMARY)
        if wants_to_attack:
            self.mapa.jogador.weapons.attack(world_mx, world_my, self.mapa)

        if self.input.is_pressed(Actions.ATTACK_SECONDARY):
            self.mapa.jogador.atacar_espada(world_mx, world_my, self.mapa)
            self.context.audio.play("melee")

        if self.mapa.jogador.hp <= 0:
            print("Jogador morreu! Indo para Game Over.")
            self.manager.change(Scene.GAME_OVER)
            return

        # --- 3. ATUALIZAÇÃO DOS SISTEMAS ---
        self.mapa.update(dt)
        self.relogio.update(dt)
        if self.mapa.jogador:
            self.camera.update(self.mapa.jogador.x, self.mapa.jogador.y, dt)

        player_rect = pygame.Rect(self.mapa.jogador.x * config.TAMANHO_TILE, 
                                  self.mapa.jogador.y * config.TAMANHO_TILE, 
                                  32, 32)
        
        for loot in self.mapa.items_no_chao[:]:
            if loot.pode_pegar() and player_rect.colliderect(loot.rect):
                # Tenta adicionar ao inventário
                sucesso = self.mapa.jogador.inventory.add_item(loot.item_name)
                if sucesso:
                    self.context.audio.play("pickup")
                    self.mapa.particulas.emit(loot.x, loot.y, "pickup", 12)
                    self.mapa.criar_texto_dano(loot.x, loot.y - 1, f"+{loot.item_name}") # Reusa texto flutuante
                    self.mapa.items_no_chao.remove(loot)

    def draw(self, surface):
        surface.fill(config.PRETO)
        cor_do_ceu = self.relogio.obter_cor()
        self.renderer.draw(surface, self.mapa, cor_do_ceu)
        self.ui.draw(surface, self.mapa.jogador)
