import math
import random
import pygame
from core import config
from graphics import recursos
from graphics import efeitos
from components.sprite import SpriteComponent
from components.impact import impact_profile
from map.terrain import terrain_material

# --- EFEITO VISUAL (Risco da Espada) ---
# Mantemos simples pois é apenas visual temporário
class EfeitoVisual:
    def __init__(self, x, y, angle):
        self.x = x
        self.y = y
        self.angle = angle
        self.life = 10 / config.FPS
        self.max_life = self.life

    def update(self, dt):
        self.life -= dt

    def draw(self, surface, camera_x, camera_y):
        cx = self.x * config.TAMANHO_TILE - camera_x
        cy = self.y * config.TAMANHO_TILE - camera_y
        end_x = cx + math.cos(self.angle) * 40
        end_y = cy + math.sin(self.angle) * 40
        largura = max(1, round(5 * max(0.0, self.life / self.max_life)))
        pygame.draw.line(surface, config.BRANCO, (cx, cy), (end_x, end_y), largura)

# --- NOVO PROJÉTIL (Entidade ECS) ---
class Projetil:
    # 1. Recebe 'dono' no __init__
    def __init__(
        self, x, y, angle, origem, dono, damage=None, speed=18.0,
        critical_chance=0.0, critical_multiplier=1.5,
    ):
        self.name = "Projetil"
        self.origem = origem 
        self.dono = dono # Guarda quem atirou
        self.damage = damage
        self.critical_chance = critical_chance
        self.critical_multiplier = critical_multiplier
        self.active = True
        self.life = 100 / config.FPS
        
        # Projéteis têm movimento balístico próprio: nunca deslizam em
        # paredes como personagens e, portanto, nunca curvam em quinas.
        self.x = float(x)
        self.y = float(y)
        self.speed = speed
        self.dx = math.cos(angle)
        self.dy = math.sin(angle)
        self.angle = angle
        self.sprite = SpriteComponent(self, "shoot", layer=config.LAYER_AEREO)
        base_image = self.sprite.image
        self.rotated_image = (
            pygame.transform.rotate(base_image, -math.degrees(angle))
            if base_image else None
        )

    @property
    def image(self): return self.rotated_image

    def _rect_at(self, x, y):
        size = max(6, config.TAMANHO_TILE // 4)
        return pygame.Rect(0, 0, size, size).move(
            round(x * config.TAMANHO_TILE - size / 2),
            round(y * config.TAMANHO_TILE - size / 2),
        )

    def _terrain_hit(self, rect, mapa_obj):
        size = config.TAMANHO_TILE
        left = rect.left // size
        right = (rect.right - 1) // size
        top = rect.top // size
        bottom = (rect.bottom - 1) // size
        for ty in range(top, bottom + 1):
            for tx in range(left, right + 1):
                if not mapa_obj.is_blocked_terrain(tx, ty):
                    continue
                tile = mapa_obj.obter_tile(tx, ty) if hasattr(mapa_obj, "obter_tile") else None
                return terrain_material(tile)
        return None

    @staticmethod
    def _play_impact_sound(mapa_obj, name, volume=0.45):
        context = getattr(mapa_obj, "context", None)
        audio = getattr(context, "audio", None)
        if audio:
            audio.play(name, volume)

    def _impact_terrain(self, mapa_obj, material, x, y):
        profile = impact_profile(material)
        mapa_obj.particulas.emit(
            x, y, profile.particle, 7, (-self.dx, -self.dy)
        )
        self._play_impact_sound(mapa_obj, profile.sound, 0.38)

    def _hit_entity(self, rect, mapa_obj):
        candidates = (
            mapa_obj.nearby_entities(rect)
            if hasattr(mapa_obj, "nearby_entities")
            else mapa_obj.entidades
        )
        for ent in candidates:
            if ent is self.dono or ent.hp <= 0:
                continue
            if rect.colliderect(ent.hitbox):
                return ent
        return None

    def _damage(self, ent, mapa_obj):
        base_damage = self.damage if self.damage is not None else (
            5 if self.origem == "enemy" else 15
        )
        rng = getattr(mapa_obj, "gameplay_rng", random)
        critical = self.critical_chance > 0 and rng.random() < self.critical_chance
        damage = round(base_damage * self.critical_multiplier) if critical else base_damage
        result = ent.tomar_dano(damage, mapa_obj, critical=critical)

        absorbed = getattr(result, "absorbed", 0)
        health_damage = getattr(result, "health_damage", damage)
        profile = impact_profile(getattr(ent, "impact_material", "flesh"))
        if absorbed:
            mapa_obj.particulas.emit(ent.x, ent.y, "armor", 9, (-self.dx, -self.dy))
            self._play_impact_sound(mapa_obj, "impact_armor", 0.55)
        if health_damage:
            mapa_obj.particulas.emit(
                ent.x, ent.y, profile.particle, 9, (self.dx, self.dy)
            )
            self._play_impact_sound(mapa_obj, profile.sound)
        if critical:
            mapa_obj.particulas.emit(ent.x, ent.y, "critical", 12, (-self.dx, -self.dy))
            self._play_impact_sound(mapa_obj, "critical", 0.5)
        mapa_obj.efeitos.append(
            efeitos.ImpactoDirecional(
                ent.x + 0.5,
                ent.y + 0.5,
                self.dx,
                self.dy,
                (255, 225, 75) if critical else profile.color,
            )
        )
        ent.physics.move_by(self.dx, self.dy, min(0.28, 0.08 + damage / 100), mapa_obj)

    def _impact_static_entity(self, ent, mapa_obj):
        profile = impact_profile(getattr(ent, "impact_material", "stone"))
        mapa_obj.particulas.emit(
            ent.x, ent.y, profile.particle, 7, (-self.dx, -self.dy)
        )
        self._play_impact_sound(mapa_obj, profile.sound, 0.38)
        mapa_obj.efeitos.append(
            efeitos.ImpactoDirecional(
                ent.x + 0.5,
                ent.y + 0.5,
                self.dx,
                self.dy,
                profile.color,
            )
        )

    def update(self, dt, mapa_obj):
        distance = self.speed * max(0.0, dt)
        distance_px = distance * config.TAMANHO_TILE
        steps = max(1, math.ceil(distance_px / 4))
        step_x = self.dx * distance / steps
        step_y = self.dy * distance / steps

        for _ in range(steps):
            next_x = self.x + step_x
            next_y = self.y + step_y
            rect = self._rect_at(next_x, next_y)

            terrain_type = self._terrain_hit(rect, mapa_obj)
            if terrain_type:
                self._impact_terrain(mapa_obj, terrain_type, next_x, next_y)
                self.active = False
                return

            target = self._hit_entity(rect, mapa_obj)
            if target:
                self.x, self.y = next_x, next_y
                if getattr(target, "is_static", False):
                    self._impact_static_entity(target, mapa_obj)
                else:
                    self._damage(target, mapa_obj)
                self.active = False
                return

            # X e Y são confirmados juntos: a direção nunca muda.
            self.x, self.y = next_x, next_y

        self.sprite.update(dt)
        self.life -= dt
        if self.life <= 0: self.active = False

    def draw(self, surface, cx, cy): pass

# --- Factory Atualizada ---
def criar_projetil(
    x, y, tx, ty, origem, mapa_obj, dono, damage=None, speed=18.0, angle_offset=0.0,
    critical_chance=0.0, critical_multiplier=1.5,
):
    # Entidades usam coordenadas do canto superior esquerdo; o tiro nasce no
    # centro visual do tile e mira exatamente o ponto indicado pelo cursor.
    start_x, start_y = x + 0.5, y + 0.5
    angle = math.atan2(ty - start_y, tx - start_x) + angle_offset
    p = Projetil(
        start_x, start_y, angle, origem, dono, damage=damage, speed=speed,
        critical_chance=critical_chance, critical_multiplier=critical_multiplier,
    )
    mapa_obj.projeteis.append(p)


def criar_feedback_disparo(atacante, tx, ty, mapa_obj, intensity=1.0):
    start_x, start_y = atacante.x + 0.5, atacante.y + 0.5
    angle = math.atan2(ty - start_y, tx - start_x)
    muzzle_x = start_x + math.cos(angle) * 0.55
    muzzle_y = start_y + math.sin(angle) * 0.55
    mapa_obj.efeitos.append(efeitos.FlashDisparo(muzzle_x, muzzle_y, angle, intensity))
    mapa_obj.efeitos.append(efeitos.Capsula(start_x, start_y, angle))
    mapa_obj.particulas.emit(muzzle_x, muzzle_y, "spark", 3, (math.cos(angle), math.sin(angle)))

def executar_golpe_espada(
    atacante, tx, ty, mapa_obj, damage=None, alcance=1.0,
    critical_chance=0.0, critical_multiplier=1.5,
):
    angle = math.atan2(ty - atacante.y, tx - atacante.x)
    efeito = EfeitoVisual(atacante.x, atacante.y, angle)
    mapa_obj.efeitos.append(efeito)
    
    distancia_golpe = alcance
    hit_x = atacante.x + math.cos(angle) * distancia_golpe
    hit_y = atacante.y + math.sin(angle) * distancia_golpe
    area_golpe = pygame.Rect(
        hit_x * config.TAMANHO_TILE - 24,
        hit_y * config.TAMANHO_TILE - 24,
        48,
        48,
    )
    
    alvos = (
        mapa_obj.nearby_entities(area_golpe)
        if hasattr(mapa_obj, "nearby_entities")
        else mapa_obj.entidades
    )
    acertou = False
    
    for alvo in alvos:
        if alvo is atacante:
            continue
        if area_golpe.colliderect(alvo.hitbox):
            if getattr(alvo, "is_static", False):
                profile = impact_profile(
                    getattr(alvo, "impact_material", "stone")
                )
                mapa_obj.particulas.emit(
                    alvo.x,
                    alvo.y,
                    profile.particle,
                    7,
                    (-math.cos(angle), -math.sin(angle)),
                )
                Projetil._play_impact_sound(mapa_obj, profile.sound, 0.38)
                if hasattr(alvo, "tomar_dano") and getattr(alvo, "hp", 0) > 0:
                    base_damage = damage if damage is not None else atacante.dano * 2
                    rng = getattr(mapa_obj, "gameplay_rng", random)
                    critical = critical_chance > 0 and rng.random() < critical_chance
                    final_damage = round(base_damage * critical_multiplier) if critical else base_damage
                    alvo.tomar_dano(final_damage, mapa_obj, critical=critical)
                acertou = True
                continue
            # Usa o Dano vindo do CombatComponent do atacante
            base_damage = damage if damage is not None else atacante.dano * 2
            rng = getattr(mapa_obj, "gameplay_rng", random)
            critical = critical_chance > 0 and rng.random() < critical_chance
            final_damage = round(base_damage * critical_multiplier) if critical else base_damage
            result = alvo.tomar_dano(final_damage, mapa_obj, critical=critical)
            absorbed = getattr(result, "absorbed", 0)
            if absorbed:
                mapa_obj.particulas.emit(alvo.x, alvo.y, "armor", 9, (-math.cos(angle), -math.sin(angle)))
                Projetil._play_impact_sound(mapa_obj, "impact_armor", 0.5)
            if getattr(result, "health_damage", final_damage):
                profile = impact_profile(
                    getattr(alvo, "impact_material", "flesh")
                )
                mapa_obj.particulas.emit(
                    alvo.x,
                    alvo.y,
                    profile.particle,
                    12,
                    (math.cos(angle), math.sin(angle)),
                )
            if critical:
                mapa_obj.particulas.emit(alvo.x, alvo.y, "critical", 12, (-math.cos(angle), -math.sin(angle)))
                Projetil._play_impact_sound(mapa_obj, "critical", 0.5)
            mapa_obj.efeitos.append(
                efeitos.ImpactoDirecional(
                    alvo.x + 0.5, alvo.y + 0.5, math.cos(angle), math.sin(angle)
                )
            )
            
            # Knockback: Empurra usando o sistema de física do alvo
            alvo.physics.move_by(math.cos(angle), math.sin(angle), 0.5, mapa_obj)
            
            acertou = True
            if alvo.hp <= 0:
                pass
                #atacante.ganhar_xp(alvo.xp_reward)
                #if alvo in mapa_obj.entidades: mapa_obj.entidades.remove(alvo)
    return acertou
