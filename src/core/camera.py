# src/camera.py
from core import config

class Camera:
    def __init__(self):
        self.camera_x = 0
        self.camera_y = 0

    def update(self, target_x, target_y):
        # 1. Calcula onde a câmera quer ir (focar no alvo)
        target_px = target_x * config.TAMANHO_TILE
        target_py = target_y * config.TAMANHO_TILE
        
        # 2. Centraliza
        self.camera_x = target_px - (config.LARGURA_TELA // 2)
        self.camera_y = target_py - (config.ALTURA_TELA // 2)
        
        # 3. Respeita os limites do mundo (Clamping)
        limit_x = config.LARGURA_MAPA * config.TAMANHO_TILE - config.LARGURA_TELA
        limit_y = config.ALTURA_MAPA * config.TAMANHO_TILE - config.ALTURA_TELA
        
        self.camera_x = max(0, min(self.camera_x, limit_x))
        self.camera_y = max(0, min(self.camera_y, limit_y))