import pygame
from core import config
from graphics import recursos

class SpriteComponent:
    def __init__(self, entity, sprite_key, layer=config.LAYER_CORPO):
        self.entity = entity
        self.layer = layer
        self.direction = "down"
        self.horizontal_direction = "right"
        self.animation_key = None
        
        raw_data = recursos.SPRITES.get(sprite_key, [])
        self.animations = raw_data if isinstance(raw_data, dict) else None

        if self.animations:
            self.frames = self._directional_frames("idle")
        elif isinstance(raw_data, list):
            self.frames = raw_data
        else:
            self.frames = [raw_data]

        self.image = self.frames[0] if self.frames else None
        
        # Animação
        self.frame_index = 0.0
        self.anim_speed = config.VELOCIDADE_ANIMACAO
        
        # Ajustes visuais (Offsets)
        self.offset_x = 0
        self.offset_y = 0
        self.scale_sombra = 1.0
        self.sombra_cache = None 
        self.dano_timer = 0.0

        self.configurar_offsets(sprite_key)

    def _directional_frames(self, state):
        directions = self.animations.get(state, {})
        return (
            directions.get(self.direction)
            or directions.get(self.horizontal_direction)
            or directions.get("right")
            or directions.get("down")
            or next(iter(directions.values()), [])
        )

    def set_direction(self, dx, dy):
        if abs(dx) > abs(dy):
            self.direction = "right" if dx > 0 else "left"
            self.horizontal_direction = self.direction
        elif dy:
            self.direction = "down" if dy > 0 else "up"

    def configurar_offsets(self, key):
        # Configurações específicas por tipo de sprite
        if key in ("tree_willow", "tree_fir", "cipreste"):
            self.scale_sombra = 0.65
            self.offset_x = 1
            self.offset_y = 0
        elif "tree" in key:
            self.scale_sombra = 0.65
            self.offset_x = 4
            self.offset_y = 0
        elif "troll" in key:
            self.scale_sombra = 2.0
        elif "boss" in key:
            self.scale_sombra = 3.0
        elif "rock" in key:
            self.scale_sombra = 0.8

    def animar(self, dt):
        # Verifica se a entidade está se movendo (flag na física)
        is_moving = getattr(self.entity, 'moving', False)

        if self.animations:
            state = "move" if is_moving else "idle"
            key = (state, self.direction)
            if key != self.animation_key:
                self.animation_key = key
                self.frames = self._directional_frames(state)
                self.frame_index = 0.0
            if self.frames:
                speed = self.anim_speed if is_moving else self.anim_speed * 0.5
                self.frame_index = (self.frame_index + speed * dt) % len(self.frames)
                self.image = self.frames[int(self.frame_index)]
            return

        if is_moving and self.frames and len(self.frames) > 1:
            self.frame_index = (self.frame_index + self.anim_speed * dt) % len(self.frames)
            self.image = self.frames[int(self.frame_index)]
        elif self.frames:
            self.frame_index = 0
            self.image = self.frames[0]

    def update(self, dt):
        self.dano_timer = max(0.0, self.dano_timer - dt)
        self.animar(dt)
