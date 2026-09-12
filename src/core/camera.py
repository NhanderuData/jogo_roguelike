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

        # Sistema de Zoom Dinâmico e Expansão de Câmera
        self.zoom = 1.0
        self.target_zoom = 1.0
        self.min_zoom = 0.25
        self.max_zoom = 2.5

    def add_trauma(self, amount):
        self.trauma = min(1.0, self.trauma + max(0.0, amount))

    def get_view_width(self) -> int:
        return int(round(config.LARGURA_TELA / max(0.05, self.zoom)))

    def get_view_height(self) -> int:
        return int(round(config.ALTURA_TELA / max(0.05, self.zoom)))

    def set_target_zoom(self, new_zoom: float) -> None:
        self.target_zoom = max(self.min_zoom, min(self.max_zoom, float(new_zoom)))

    def screen_to_world_x(self, screen_x: float) -> float:
        """Converte coordenada horizontal da tela (pixels) para coordenada de tile no mundo."""
        view_x = screen_x / max(0.05, self.zoom)
        return (self.camera_x + view_x) / config.TAMANHO_TILE

    def screen_to_world_y(self, screen_y: float) -> float:
        """Converte coordenada vertical da tela (pixels) para coordenada de tile no mundo."""
        view_y = screen_y / max(0.05, self.zoom)
        return (self.camera_y + view_y) / config.TAMANHO_TILE

    def update(self, target_x, target_y, dt, world_size=None, dizziness=0.0):
        # Transição suave do zoom
        if abs(self.zoom - self.target_zoom) > 0.001:
            blend_zoom = 1.0 - math.exp(-14.0 * max(0.0, dt))
            self.zoom += (self.target_zoom - self.zoom) * blend_zoom
        else:
            self.zoom = self.target_zoom

        # 1. Calcula onde a câmera quer ir (focar no alvo)
        target_px = (target_x + 0.5) * config.TAMANHO_TILE
        target_py = (target_y + 0.5) * config.TAMANHO_TILE
        
        view_w = self.get_view_width()
        view_h = self.get_view_height()

        # 2. Centraliza com base no tamanho atual do viewport
        desired_x = target_px - (view_w // 2)
        desired_y = target_py - (view_h // 2)
        
        # 3. Respeita os limites do mundo (Clamping)
        world_width, world_height = world_size or (
            config.LARGURA_MAPA,
            config.ALTURA_MAPA,
        )
        total_world_w = world_width * config.TAMANHO_TILE
        total_world_h = world_height * config.TAMANHO_TILE

        if total_world_w < view_w:
            desired_x = (total_world_w - view_w) // 2
            limit_x = desired_x
        else:
            limit_x = max(0, total_world_w - view_w)
            desired_x = max(0, min(desired_x, limit_x))

        if total_world_h < view_h:
            desired_y = (total_world_h - view_h) // 2
            limit_y = desired_y
        else:
            limit_y = max(0, total_world_h - view_h)
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

        if dizziness > 0:
            sway_amount = min(9.0, dizziness * 2.2)
            shake_x += math.sin(self.shake_time * 3.4) * sway_amount
            shake_y += math.cos(self.shake_time * 2.6) * sway_amount

        if total_world_w < view_w:
            self.camera_x = desired_x + shake_x
        else:
            self.camera_x = max(0, min(self.base_x + shake_x, limit_x))

        if total_world_h < view_h:
            self.camera_y = desired_y + shake_y
        else:
            self.camera_y = max(0, min(self.base_y + shake_y, limit_y))
