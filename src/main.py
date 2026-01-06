import sys
import os
from core.game import Game

sys.path.append(os.path.join(os.path.dirname(__file__), "src"))
# Agora importamos o Game da pasta core.engine (ajuste se seu arquivo for core.py)

if __name__ == "__main__":
    try:
        jogo = Game()
        jogo.run()
    except Exception as e:
        print(f"Erro ao rodar o jogo: {e}")
        input("Pressione Enter para fechar...") # Mantém o terminal aberto se der erro
    sys.exit()