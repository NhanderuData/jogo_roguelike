import pygame
from core import config
from graphics import recursos

class SpriteComponent:
    def __init__(self, entity, sprite_key, layer=config.LAYER_CORPO):
        self.entity = entity
        self.layer = layer
        
        # Carregamento de Sprite
        self.frames = recursos.SPRITES.get(sprite_key, [])
        self.image = self.frames[0] if self.frames else None
        
        # Animação
        self.frame_index = 0.0
        self.anim_speed = config.VELOCIDADE_ANIMACAO
        
        # Ajustes visuais (Offsets)
        self.offset_x = 0
        self.offset_y = 0
        self.scale_sombra = 1.0
        
        # --- CORREÇÃO AQUI ---
        self.sombra_cache = None 
        # ---------------------

        self.configurar_offsets(sprite_key)

    def configurar_offsets(self, key):
        # Configurações específicas por tipo de sprite
        if "tree" in key:
            self.scale_sombra = 1.4
            self.offset_x = -2
        elif "troll" in key:
            self.scale_sombra = 2.0
        elif "boss" in key:
            self.scale_sombra = 3.0
        elif "rock" in key:
            self.scale_sombra = 0.8

    def animar(self):
        # Verifica se a entidade está se movendo (flag na física)
        is_moving = getattr(self.entity, 'moving', False)
        
        if is_moving and self.frames and len(self.frames) > 1:
            self.frame_index += self.anim_speed
            if self.frame_index >= len(self.frames): 
                self.frame_index = 0
            self.image = self.frames[int(self.frame_index)]
        elif self.frames:
            self.frame_index = 0
            self.image = self.frames[0]

    def update(self, dt):
        self.animar()