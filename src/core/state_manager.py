import pygame

class BaseState:
    """
    Classe Abstrata que define o contrato para qualquer estado do jogo
    (Menu, Jogo, Inventário, Pause, etc.)
    """
    def __init__(self, manager, registry):
        self.manager = manager
        # registry é um dicionário compartilhado para passar dados entre estados
        # (ex: passar o objeto 'jogador' do GameState para o InventoryState)
        self.registry = registry 

    def enter(self, **kwargs):
        """Chamado quando o estado entra no topo da pilha"""
        pass

    def exit(self):
        """Chamado quando o estado sai do topo"""
        pass

    def handle_input(self, event):
        """Gerencia eventos brutos do Pygame (teclado/mouse)"""
        pass

    def update(self, dt):
        """Lógica do frame (IA, física, etc)"""
        pass

    def draw(self, surface):
        """Renderização na tela"""
        pass


class StateManager:
    """
    Gerencia a pilha de estados.
    Permite 'Pause' (push) sobrepondo o 'Jogo', ou troca total (change).
    """
    def __init__(self):
        self.stack = []
        self.registry = {} # Dados persistentes entre estados (ex: Highscore, Configs)

    def push(self, state_class, **kwargs):
        """Adiciona um estado no topo (ex: Pause sobre o Jogo)"""
        new_state = state_class(self, self.registry)
        new_state.enter(**kwargs)
        self.stack.append(new_state)

    def pop(self):
        """Remove o estado do topo (ex: Fecha Pause, volta pro Jogo)"""
        if self.stack:
            top_state = self.stack.pop()
            top_state.exit()
            # Opcional: Chamar enter() ou resume() no estado que ficou no topo?
            # Por enquanto, simples é melhor.

    def change(self, state_class, **kwargs):
        """Troca o estado atual pelo novo (ex: Menu -> Jogo)"""
        while self.stack:
            self.pop()
        self.push(state_class, **kwargs)

    def handle_input(self, event):
        if self.stack:
            self.stack[-1].handle_input(event)

    def update(self, dt):
        if self.stack:
            self.stack[-1].update(dt)

    def draw(self, surface):
        # Em alguns casos, queremos desenhar o estado de baixo (ex: Pause transparente)
        # Mas para simplificar agora, desenhamos apenas o topo.
        if self.stack:
            self.stack[-1].draw(surface)