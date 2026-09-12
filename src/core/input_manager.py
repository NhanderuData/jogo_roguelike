import pygame

class Actions:
    # Definimos constantes para evitar erros de digitação (strings mágicas)
    MOVE_UP = "move_up"
    MOVE_DOWN = "move_down"
    MOVE_LEFT = "move_left"
    MOVE_RIGHT = "move_right"
    ATTACK_PRIMARY = "attack_primary" 
    ATTACK_SECONDARY = "attack_secondary"
    PAUSE = "pause"
    QUIT = "quit"
    RESTART = "restart"
    START = "start"
    INVENTORY = "inventory"
    RELOAD = "reload"
    WEAPON_1 = "weapon_1"
    WEAPON_2 = "weapon_2"
    WEAPON_3 = "weapon_3"
    WEAPON_4 = "weapon_4"
    WEAPON_5 = "weapon_5"
    WEAPON_6 = "weapon_6"
    WEAPON_7 = "weapon_7"
    WEAPON_8 = "weapon_8"
    WEAPON_9 = "weapon_9"
    WEAPON_NEXT = "weapon_next"
    WEAPON_PREV = "weapon_prev"
    UNLOCK_ALL_WEAPONS = "unlock_all_weapons"
    TOGGLE_DEBUG = "toggle_debug"
    TOGGLE_MUTE = "toggle_mute"
    RESET_ZOOM = "reset_zoom"
    INTERACT = "interact"

class InputManager:
    def __init__(self):
        # Mapa de Teclas: Ação -> Lista de Teclas que a ativam
        self.key_bindings = {
            Actions.START: [pygame.K_RETURN, pygame.K_KP_ENTER],
            Actions.INTERACT:   [pygame.K_e],
            Actions.MOVE_UP:    [pygame.K_w, pygame.K_UP],
            Actions.MOVE_DOWN:  [pygame.K_s, pygame.K_DOWN],
            Actions.MOVE_LEFT:  [pygame.K_a, pygame.K_LEFT],
            Actions.MOVE_RIGHT: [pygame.K_d, pygame.K_RIGHT],
            Actions.PAUSE:      [pygame.K_ESCAPE, pygame.K_p],
            Actions.RESTART:    [pygame.K_r],
            Actions.QUIT:       [pygame.K_ESCAPE],
            Actions.INVENTORY: [pygame.K_i, pygame.K_TAB],
            Actions.RELOAD: [pygame.K_r],
            Actions.WEAPON_1: [pygame.K_1],
            Actions.WEAPON_2: [pygame.K_2],
            Actions.WEAPON_3: [pygame.K_3],
            Actions.WEAPON_4: [pygame.K_4],
            Actions.WEAPON_5: [pygame.K_5],
            Actions.WEAPON_6: [pygame.K_6],
            Actions.WEAPON_7: [pygame.K_7],
            Actions.WEAPON_8: [pygame.K_8],
            Actions.WEAPON_9: [pygame.K_9],
            Actions.WEAPON_NEXT: [pygame.K_q],
            Actions.UNLOCK_ALL_WEAPONS: [pygame.K_u],
            Actions.TOGGLE_DEBUG: [pygame.K_F3],
            Actions.TOGGLE_MUTE: [pygame.K_m],
            Actions.RESET_ZOOM: [pygame.K_BACKSPACE, pygame.K_HOME],
        }
        
        # Mapa de Mouse: Ação -> Índice do Botão (0=Esq, 1=Meio, 2=Dir)
        self.mouse_bindings = {
            Actions.ATTACK_PRIMARY: 0,   # Clique Esquerdo
            Actions.ATTACK_SECONDARY: 2, # Clique Direito
            Actions.RESET_ZOOM: 1,       # Clique Meio
        }

        # Estado atual
        self.mouse_pos = (0, 0)
        self.mouse_wheel = 0
        
        # Conjuntos para armazenar o estado das ações
        self.actions_held = set()     # Ação está sendo SEGURADA (bom para andar)
        self.actions_pressed = set()  # Ação foi pressionada NESTE FRAME (bom para atacar/pause)

    def update(self):
        """Chamado no início de cada frame pelo MainApp"""
        self.actions_pressed.clear()
        self.actions_held.clear()
        self.mouse_wheel = 0

        if not pygame.get_init() or not pygame.display.get_init():
            return
        
        # 1. Leitura do Teclado
        keys = pygame.key.get_pressed()
        for action, key_list in self.key_bindings.items():
            for k in key_list:
                if keys[k]:
                    self.actions_held.add(action)

        # 2. Leitura do Mouse
        mouse_buttons = pygame.mouse.get_pressed()
        self.mouse_pos = pygame.mouse.get_pos()
        
        for action, button_index in self.mouse_bindings.items():
            if mouse_buttons[button_index]:
                self.actions_held.add(action)

    def process_event(self, event):
        if event.type == pygame.KEYDOWN:
            for action, key_list in self.key_bindings.items():
                if event.key in key_list:
                    self.actions_pressed.add(action)
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            for action, button_index in self.mouse_bindings.items():
                if event.button == button_index + 1:
                    self.actions_pressed.add(action)
            # Roda do mouse legado
            if event.button == 4:
                self.mouse_wheel += 1
            elif event.button == 5:
                self.mouse_wheel -= 1
            elif event.button == 2:
                self.actions_pressed.add(Actions.RESET_ZOOM)

        elif event.type == pygame.MOUSEWHEEL:
            self.mouse_wheel += event.y

    def is_held(self, action):
        return action in self.actions_held

    def is_pressed(self, action):
        return action in self.actions_pressed

    def get_mouse_position(self):
        return self.mouse_pos

    def get_mouse_wheel(self) -> int:
        return self.mouse_wheel
