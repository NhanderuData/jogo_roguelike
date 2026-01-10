import sys
import os
import pygame
from graphics import recursos
from core.state_manager import StateManager
from states.game_state import GameState
from core import config
from core.input_manager import InputManager

# Garante que o Python ache os módulos
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

class MainApp:
    def __init__(self):
        pygame.init()
        # Configuração inicial de Janela (Retirado do antigo Game.__init__)
        self.screen = pygame.display.set_mode(
            (config.LARGURA_TELA, config.ALTURA_TELA),
            pygame.FULLSCREEN | pygame.SCALED
        )
        pygame.display.set_caption("Roguelike - Architecture Refactor")
        self.clock = pygame.time.Clock()
        self.running = True
        
        # Carregamento Global de Assets (Feito uma única vez)
        recursos.carregar_tudo()
        
        self.input_manager = InputManager()
        self.state_manager = StateManager(self.input_manager)
        self.state_manager.change(GameState)

    def run(self):
        while self.running:
            
            dt = self.clock.tick(config.FPS) / 1000.0
            self.input_manager.update()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                
                self.input_manager.process_event(event)
                self.state_manager.handle_input(event)
            
            self.state_manager.update(dt)
            self.state_manager.draw(self.screen)
            
            pygame.display.flip()
            
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    try:
        app = MainApp()
        app.run()
    except Exception as e:
        print(f"Erro fatal: {e}")
        import traceback
        traceback.print_exc()
        input("Pressione Enter para fechar...")