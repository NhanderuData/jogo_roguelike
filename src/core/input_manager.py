import pygame

class Actions:
    # Definimos constantes para evitar erros de digitação (strings mágicas)
    MOVE_UP = "move_up"
    MOVE_DOWN = "move_down"
    MOVE_LEFT = "move_left"
    MOVE_RIGHT = "move_right"
    ATTACK_PRIMARY = "attack_primary"   # Espada
    ATTACK_SECONDARY = "attack_secondary" # Magia
    PAUSE = "pause"
    QUIT = "quit"

class InputManager:
    def __init__(self):
        # Mapa de Teclas: Ação -> Lista de Teclas que a ativam
        self.key_bindings = {
            Actions.MOVE_UP:    [pygame.K_w, pygame.K_UP],
            Actions.MOVE_DOWN:  [pygame.K_s, pygame.K_DOWN],
            Actions.MOVE_LEFT:  [pygame.K_a, pygame.K_LEFT],
            Actions.MOVE_RIGHT: [pygame.K_d, pygame.K_RIGHT],
            Actions.PAUSE:      [pygame.K_ESCAPE, pygame.K_p],
            Actions.QUIT:       [pygame.K_ESCAPE] # Exemplo
        }
        
        # Mapa de Mouse: Ação -> Índice do Botão (0=Esq, 1=Meio, 2=Dir)
        self.mouse_bindings = {
            Actions.ATTACK_PRIMARY: 0,   # Clique Esquerdo
            Actions.ATTACK_SECONDARY: 2  # Clique Direito
        }

        # Estado atual
        self.mouse_pos = (0, 0)
        
        # Conjuntos para armazenar o estado das ações
        self.actions_held = set()     # Ação está sendo SEGURADA (bom para andar)
        self.actions_pressed = set()  # Ação foi pressionada NESTE FRAME (bom para atacar/pause)

    def update(self):
        """Chamado no início de cada frame pelo MainApp"""
        self.actions_pressed.clear()
        self.actions_held.clear()
        
        # 1. Leitura do Teclado
        keys = pygame.key.get_pressed()
        for action, key_list in self.key_bindings.items():
            for k in key_list:
                if keys[k]:
                    self.actions_held.add(action)
                    # Nota: Para 'pressed' (input único), usaremos o event loop do Pygame no process_event
                    # Mas para movimento, 'held' é o que importa.

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

    def is_held(self, action):
        return action in self.actions_held

    def is_pressed(self, action):
        return action in self.actions_pressed

    def get_mouse_position(self):
        return self.mouse_pos