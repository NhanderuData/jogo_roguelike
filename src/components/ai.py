import random
from core import config

class AIComponent:
    def __init__(self, entity):
        self.entity = entity
        self.active = True
        
    def update(self, mapa_obj):
        if not self.active or self.entity.nome == "Heroi":
            return

        player = mapa_obj.jogador
        physics = self.entity.physics
        
        if physics.speed == 0:
            return

        dx = player.x - self.entity.x
        dy = player.y - self.entity.y
        dist = (dx**2 + dy**2)**0.5
        
        if 0.8 < dist < 10:
            dir_x = dx / dist
            dir_y = dy / dist
            physics.move(dir_x, dir_y, mapa_obj)

        if dist < 8:
            if dist < 1.5:
    
                self.entity.atacar_espada(player.x, player.y, mapa_obj)
            
            elif dist > 3 and ("Troll" in self.entity.nome or "REI" in self.entity.nome):
                if random.randint(0, 100) < 5:
                    self.entity.atirar(player.x, player.y, mapa_obj, "enemy")