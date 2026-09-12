import math
import random
import pygame
from core import config
from graphics import recursos
from graphics import efeitos
from components.sprite import SpriteComponent
from components.impact import impact_profile
from map.terrain import terrain_material

# --- EFEITO VISUAL (Arco de Corte da Lâmina) ---
class EfeitoVisual:
    def __init__(self, x, y, angle, radius=48):
        self.x = x
        self.y = y
        self.angle = angle
        self.radius = max(36, radius)
        self.life = 0.15
        self.max_life = self.life

    def update(self, dt):
        self.life -= dt

    def draw(self, surface, camera_x, camera_y):
        if self.life <= 0:
            return
        cx = int((self.x + 0.5) * config.TAMANHO_TILE - camera_x)
        cy = int((self.y + 0.5) * config.TAMANHO_TILE - camera_y)

        progress = max(0.0, min(1.0, self.life / self.max_life))
        alpha = int(240 * progress)

        # Desenha arco dinâmico de lâmina / corte (slash swoosh)
        arc_span = math.radians(110)
        start_angle = self.angle - arc_span / 2
        end_angle = self.angle + arc_span / 2
        steps = 8
        outer_pts = []
        inner_pts = []
        r_outer = self.radius
        r_inner = max(8, self.radius * 0.45)
        for i in range(steps + 1):
            t = i / steps
            a = start_angle + t * (end_angle - start_angle)
            outer_pts.append((int(cx + math.cos(a) * r_outer), int(cy + math.sin(a) * r_outer)))
            inner_pts.append((int(cx + math.cos(a) * r_inner), int(cy + math.sin(a) * r_inner)))

        poly_pts = outer_pts + inner_pts[::-1]
        if len(poly_pts) >= 3:
            slash_surf = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            pygame.draw.polygon(slash_surf, (255, 255, 255, min(230, alpha)), poly_pts)
            pygame.draw.lines(slash_surf, (180, 230, 255, alpha), False, outer_pts, 3)
            surface.blit(slash_surf, (0, 0))

# --- NOVO PROJÉTIL (Entidade ECS) ---
class Projetil:
    # 1. Recebe 'dono' no __init__
    def __init__(
        self, x, y, angle, origem, dono, damage=None, speed=18.0,
        critical_chance=0.0, critical_multiplier=1.5,
        projectile_type="bullet",
    ):
        self.name = "Projetil"
        self.origem = origem 
        self.dono = dono # Guarda quem atirou
        self.damage = damage
        self.critical_chance = critical_chance
        self.critical_multiplier = critical_multiplier
        self.projectile_type = projectile_type
        self.active = True
        self.life = 0.45 if projectile_type == "flame" else (100 / config.FPS)
        self.hit_entities = set()
        
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
        size = int(config.TAMANHO_TILE * 0.75) if self.projectile_type == "flame" else max(6, config.TAMANHO_TILE // 4)
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
                tile = (
                    mapa_obj.obter_tile(tx, ty)
                    if hasattr(mapa_obj, "obter_tile")
                    else None
                )
                # A água bloqueia personagens, mas não projéteis em voo.
                if tile and tile.tipo == "deep_water":
                    continue
                if not mapa_obj.is_blocked_terrain(tx, ty):
                    continue
                tile_hb = (
                    mapa_obj.get_tile_hitbox(tx, ty)
                    if hasattr(mapa_obj, "get_tile_hitbox")
                    else None
                )
                if tile_hb and not rect.colliderect(tile_hb):
                    continue
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
            if ent is self.dono or getattr(ent, "hp", 1) <= 0:
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

    def _criar_explosao(self, mapa_obj, cx, cy):
        blast_radius = 2.8
        if hasattr(mapa_obj, "efeitos") and mapa_obj.efeitos is not None:
            mapa_obj.efeitos.append(
                efeitos.ExplosaoAnimada(cx, cy, radius_tiles=blast_radius, damage=self.damage or 140)
            )
        if hasattr(mapa_obj, "particulas") and mapa_obj.particulas:
            mapa_obj.particulas.emit(cx, cy, "fire", 24)
            mapa_obj.particulas.emit(cx, cy, "smoke", 18)
            mapa_obj.particulas.emit(cx, cy, "spark", 16)
        if hasattr(mapa_obj, "context") and getattr(mapa_obj.context, "audio", None):
            mapa_obj.context.audio.play("explosion")
        if hasattr(mapa_obj, "camera") and mapa_obj.camera:
            mapa_obj.camera.add_trauma(0.48)

        # Destrói / colhe vegetação e plantações na área da detonação
        if hasattr(mapa_obj, "colher_decoracao"):
            r_int = int(math.ceil(blast_radius))
            for bx in range(int(cx) - r_int, int(cx) + r_int + 1):
                for by in range(int(cy) - r_int, int(cy) + r_int + 1):
                    if math.hypot(bx + 0.5 - cx, by + 0.5 - cy) <= blast_radius:
                        mapa_obj.colher_decoracao(bx, by, self.dono)

        for other in getattr(mapa_obj, "entidades", ()):
            if other is self.dono:
                continue
            dist = math.hypot(other.x + 0.5 - cx, other.y + 0.5 - cy)
            if dist <= blast_radius:
                factor = max(0.3, 1.0 - (dist / blast_radius) * 0.7)
                dmg = max(10, int((self.damage or 140) * factor))
                c = getattr(other, "combat", None)
                if c and not getattr(c, "dead", False):
                    c.take_damage(dmg, mapa_obj)
                    if hasattr(c, "apply_burn"):
                        c.apply_burn(3.0)
                    if hasattr(mapa_obj, "criar_texto_dano"):
                        mapa_obj.criar_texto_dano(other.x, other.y, dmg, (255, 120, 30))
                # Empurrão físico radial (Knockback)
                phys = getattr(other, "physics", None)
                if phys and dist > 0.05:
                    push_x = (other.x + 0.5 - cx) / dist
                    push_y = (other.y + 0.5 - cy) / dist
                    knockback_force = min(0.65, 0.2 + factor * 0.4)
                    phys.move_by(push_x, push_y, knockback_force, mapa_obj)

    def update(self, dt, mapa_obj):
        # Disparo contínuo de plumas de chamas para o lança-chamas
        if self.projectile_type == "flame" and hasattr(mapa_obj, "efeitos") and mapa_obj.efeitos is not None:
            mapa_obj.efeitos.append(efeitos.EfeitoChama(self.x, self.y, self.angle, self.speed))

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
                if self.projectile_type == "rocket":
                    self._criar_explosao(mapa_obj, next_x, next_y)
                self.active = False
                return

            if self.projectile_type == "flame":
                # Lança-chamas perfurante: incendeia múltiplos inimigos e vegetações sem ser bloqueado
                if hasattr(mapa_obj, "colher_decoracao"):
                    mapa_obj.colher_decoracao(int(math.floor(next_x)), int(math.floor(next_y)), self.dono)

                candidates = (
                    mapa_obj.nearby_entities(rect)
                    if hasattr(mapa_obj, "nearby_entities")
                    else mapa_obj.entidades
                )
                for ent in candidates:
                    if ent is self.dono or getattr(ent, "hp", 1) <= 0 or ent in self.hit_entities:
                        continue
                    if rect.colliderect(ent.hitbox):
                        self.hit_entities.add(ent)
                        if getattr(ent, "is_static", False):
                            self._impact_static_entity(ent, mapa_obj)
                        else:
                            self._damage(ent, mapa_obj)
                            c = getattr(ent, "combat", None)
                            if c and hasattr(c, "apply_burn"):
                                c.apply_burn(3.5)
            else:
                target = self._hit_entity(rect, mapa_obj)
                if target:
                    self.x, self.y = next_x, next_y
                    if getattr(target, "is_static", False):
                        self._impact_static_entity(target, mapa_obj)
                    else:
                        self._damage(target, mapa_obj)
                    if self.projectile_type == "rocket":
                        self._criar_explosao(mapa_obj, next_x, next_y)
                    self.active = False
                    return

            # X e Y são confirmados juntos: a direção nunca muda.
            self.x, self.y = next_x, next_y

        if self.projectile_type == "flame" and hasattr(mapa_obj, "particulas") and mapa_obj.particulas:
            mapa_obj.particulas.emit(self.x, self.y, "fire", 2)
        elif self.projectile_type == "rocket" and hasattr(mapa_obj, "particulas") and mapa_obj.particulas:
            mapa_obj.particulas.emit(self.x, self.y, "smoke", 1)

        self.sprite.update(dt)
        self.life -= dt
        if self.life <= 0: self.active = False

    def draw(self, surface, cx, cy): pass

# --- Factory Atualizada ---
def criar_projetil(
    x, y, tx, ty, origem, mapa_obj, dono, damage=None, speed=18.0, angle_offset=0.0,
    critical_chance=0.0, critical_multiplier=1.5,
    projectile_type="bullet",
):
    # Entidades usam coordenadas do canto superior esquerdo; o tiro nasce no
    # centro visual do tile e mira exatamente o ponto indicado pelo cursor.
    start_x, start_y = x + 0.5, y + 0.5
    angle = math.atan2(ty - start_y, tx - start_x) + angle_offset
    p = Projetil(
        start_x, start_y, angle, origem, dono, damage=damage, speed=speed,
        critical_chance=critical_chance, critical_multiplier=critical_multiplier,
        projectile_type=projectile_type,
    )
    mapa_obj.projeteis.append(p)
    if origem == "player" and hasattr(mapa_obj, "alert_enemies"):
        mapa_obj.alert_enemies(start_x, start_y, radius=18.0)


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
    start_x = atacante.x + 0.5
    start_y = atacante.y + 0.5
    angle = math.atan2(ty - start_y, tx - start_x)
    efeito = EfeitoVisual(atacante.x, atacante.y, angle, radius=int(alcance * config.TAMANHO_TILE))
    mapa_obj.efeitos.append(efeito)

    distancia_golpe = alcance
    hit_x = start_x + math.cos(angle) * distancia_golpe
    hit_y = start_y + math.sin(angle) * distancia_golpe
    area_golpe = pygame.Rect(
        int(hit_x * config.TAMANHO_TILE - 28),
        int(hit_y * config.TAMANHO_TILE - 28),
        56,
        56,
    )

    broadphase_rect = pygame.Rect(
        int((start_x - alcance - 0.5) * config.TAMANHO_TILE),
        int((start_y - alcance - 0.5) * config.TAMANHO_TILE),
        int((alcance * 2 + 1.0) * config.TAMANHO_TILE),
        int((alcance * 2 + 1.0) * config.TAMANHO_TILE),
    )
    alvos = (
        mapa_obj.nearby_entities(broadphase_rect)
        if hasattr(mapa_obj, "nearby_entities")
        else mapa_obj.entidades
    )
    acertou = False

    # Ceifa/colheita de plantações e cogumelos pelo golpe
    if hasattr(mapa_obj, "colher_decoracao"):
        for step in (0.4, 0.8, distancia_golpe):
            cx = start_x + math.cos(angle) * step
            cy = start_y + math.sin(angle) * step
            for tx in (int(math.floor(cx)), int(round(cx))):
                for ty in (int(math.floor(cy)), int(round(cy))):
                    if mapa_obj.colher_decoracao(tx, ty, atacante):
                        acertou = True

    for alvo in alvos:
        if alvo is atacante or getattr(alvo, "hp", 0) <= 0:
            continue

        alvo_cx = getattr(alvo, "x", 0) + 0.5
        alvo_cy = getattr(alvo, "y", 0) + 0.5
        dist = math.hypot(alvo_cx - start_x, alvo_cy - start_y)
        
        # Conexão abrangente: cone frontal OU queima-roupa OU colisão de hitbox
        atingiu = False
        if dist <= alcance + 0.45:
            diff_angle = abs((math.atan2(alvo_cy - start_y, alvo_cx - start_x) - angle + math.pi) % (2 * math.pi) - math.pi)
            if diff_angle <= math.radians(80) or dist <= 0.85:
                atingiu = True
        if not atingiu and hasattr(alvo, "hitbox") and area_golpe.colliderect(alvo.hitbox):
            atingiu = True

        if atingiu:
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
