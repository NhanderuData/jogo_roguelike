# src/camera.py
import math

from core import config

class Camera:
    def __init__(self):
        self.camera_x = 0.0
        self.camera_y = 0.0
        self.base_x = 0.0
        self.base_y = 0.0
        self.follow_speed = 8.0
        self.trauma = 0.0
        self.shake_time = 0.0
        self.initialized = False

    def add_trauma(self, amount):
        self.trauma = min(1.0, self.trauma + max(0.0, amount))

    def update(self, target_x, target_y, dt):
        # 1. Calcula onde a câmera quer ir (focar no alvo)
        target_px = (target_x + 0.5) * config.TAMANHO_TILE
        target_py = (target_y + 0.5) * config.TAMANHO_TILE
        
        # 2. Centraliza
        desired_x = target_px - (config.LARGURA_TELA // 2)
        desired_y = target_py - (config.ALTURA_TELA // 2)
        
        # 3. Respeita os limites do mundo (Clamping)
        limit_x = config.LARGURA_MAPA * config.TAMANHO_TILE - config.LARGURA_TELA
        limit_y = config.ALTURA_MAPA * config.TAMANHO_TILE - config.ALTURA_TELA
        
        desired_x = max(0, min(desired_x, limit_x))
        desired_y = max(0, min(desired_y, limit_y))

        if not self.initialized:
            self.base_x, self.base_y = desired_x, desired_y
            self.initialized = True
        else:
            blend = 1.0 - math.exp(-self.follow_speed * max(0.0, dt))
            self.base_x += (desired_x - self.base_x) * blend
            self.base_y += (desired_y - self.base_y) * blend

        self.shake_time += max(0.0, dt)
        self.trauma = max(0.0, self.trauma - 1.8 * max(0.0, dt))
        amplitude = self.trauma * self.trauma * 13.0
        shake_x = math.sin(self.shake_time * 47.0) * amplitude
        shake_y = math.sin(self.shake_time * 61.0 + 1.7) * amplitude
        self.camera_x = max(0, min(self.base_x + shake_x, limit_x))
        self.camera_y = max(0, min(self.base_y + shake_y, limit_y))
