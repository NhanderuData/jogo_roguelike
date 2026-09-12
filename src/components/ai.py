import heapq
import math
import random
import pygame
from core import config


NPC_DIALOGOS = {
    "Aldeão": [
        "Bom dia, viajante! Os dias têm sido calmos, mas cuidado ao se afastar da cidade.",
        "Os lampiões da praça mantêm as feras afastadas. Fique perto da luz ao anoitecer!",
        "Você já visitou a horta? Cenouras frescas restauram as forças e aguçam a visão no escuro.",
        "Se precisar de lenha ou ferramentas, dê uma olhada na oficina do ferreiro.",
    ],
    "Guarda da Cidade": [
        "Alto lá! Mantenha suas armas sob controle dentro dos limites urbanos.",
        "A guarda da cidade vigia os portões dia e noite. Nenhuma criatura passará por aqui!",
        "Se avistar orcs ou stalkers na floresta, avise a guarnição imediatamente.",
        "Nossos lampiões queimam óleo puro. A luz sagrada protege os cidadãos.",
    ],
    "Taberneira": [
        "Seja bem-vindo à nossa cidade! Venha descansar os pés cansados da longa viagem.",
        "Dizem que há ruínas antigas cheias de perigos além do grande rio...",
        "Um refúgio seguro e uma boa fogueira curam o cansaço de qualquer aventureiro!",
    ],
    "Alquimista": [
        "As ervas e raízes desta região possuem propriedades medicinais únicas.",
        "Cenouras aguçam a visão na escuridão, e certos cogumelos... bem, use com cautela!",
        "A sabedoria e a prudência são os maiores escudos contra a noite.",
    ],
    "Mercador": [
        "Bem-vindo à feira! Em breve terei novas provisões e caixotes de suprimentos.",
        "Cuidado com os ermos escuros, forasteiro. O comércio só floresce onde há segurança!",
        "Caixotes de vegetais frescos direto dos canteiros da horta!",
    ],
}


class AIComponent:
    def __init__(self, entity, rng=None):
        self.entity = entity
        self.rng = rng or random
        self.active = True
        self.path = []
        self.repath_timer = 0.0
        self.last_goal = None
        self.ranged_decision_timer = self.rng.uniform(0.35, 0.8)

        # Estados de Animais
        self.animal_state = "graze"
        self.animal_timer = self.rng.uniform(1.5, 3.5)
        self.animal_dir = (0.0, 0.0)
        self.panic_timer = 0.0
        self.herd_alert_cooldown = 0.0
        self.charge_timer = 0.0
        self.charge_dir = (0.0, 0.0)
        self.charge_cooldown = self.rng.uniform(1.0, 3.0)

        # Estados de Inimigos
        self.circle_timer = self.rng.uniform(1.5, 3.0)
        self.circle_sign = self.rng.choice((-1.0, 1.0))
        self.sun_burn_accumulator = 0.0
        self.stalk_timer = self.rng.uniform(2.5, 4.5)
        self.pounce_timer = 0.0
        self.investigate_pos = None
        self.investigate_timer = 0.0
        self.idle_state = "stand"
        self.idle_timer = self.rng.uniform(1.5, 4.0)
        self.idle_dir = (0.0, 0.0)
        self.current_dialog = None
        self.dialog_timer = 0.0

    def _find_path(self, mapa_obj, goal):
        start = (round(self.entity.x), round(self.entity.y))
        if start == goal:
            return []

        frontier = [(0, start)]
        came_from = {start: None}
        cost = {start: 0}
        visited = 0

        while frontier and visited < 450:
            _, current = heapq.heappop(frontier)
            visited += 1
            if current == goal:
                break

            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                neighbor = (current[0] + dx, current[1] + dy)
                if neighbor != goal and mapa_obj.is_blocked_terrain(*neighbor):
                    continue
                new_cost = cost[current] + 1
                if neighbor in cost and new_cost >= cost[neighbor]:
                    continue
                cost[neighbor] = new_cost
                priority = new_cost + abs(goal[0] - neighbor[0]) + abs(goal[1] - neighbor[1])
                heapq.heappush(frontier, (priority, neighbor))
                came_from[neighbor] = current

        if goal not in came_from:
            return []
        path = []
        current = goal
        while current != start:
            path.append(current)
            current = came_from[current]
        path.reverse()
        return path

    def _navigation_direction(self, mapa_obj, direct_x, direct_y, dt):
        physics = self.entity.physics
        self.repath_timer = max(0.0, self.repath_timer - dt)
        probe = min(0.4, max(0.15, physics.speed * dt * 2))
        blocked_ahead = physics.check_collision(
            physics.x + direct_x * probe,
            physics.y + direct_y * probe,
            mapa_obj,
        )

        player = getattr(mapa_obj, "jogador", None)
        goal = (round(player.x), round(player.y)) if player else (round(self.entity.x), round(self.entity.y))
        if blocked_ahead or self.path:
            if self.repath_timer == 0 or goal != self.last_goal:
                self.path = self._find_path(mapa_obj, goal)
                self.last_goal = goal
                self.repath_timer = 0.45 + self.rng.uniform(0.0, 0.15)

            while self.path:
                waypoint_x, waypoint_y = self.path[0]
                wx = waypoint_x - self.entity.x
                wy = waypoint_y - self.entity.y
                if math.hypot(wx, wy) >= 0.2:
                    length = math.hypot(wx, wy)
                    return wx / length, wy / length
                self.path.pop(0)
        return direct_x, direct_y

    def _apply_flocking_separation(self, mapa_obj, dir_x, dir_y, radius: float = 1.4):
        """Força de repulsão suave para evitar que monstros e animais se empilhem em linha reta."""
        if not hasattr(mapa_obj, "entidades"):
            return dir_x, dir_y

        repulse_x = 0.0
        repulse_y = 0.0
        count = 0
        my_role = getattr(self.entity, "role", None)

        for other in getattr(mapa_obj, "entidades", ()):
            if other is self.entity or getattr(other, "is_static", False) or getattr(other, "hp", 1) <= 0:
                continue
            if getattr(other, "role", None) == my_role:
                ox = self.entity.x - other.x
                oy = self.entity.y - other.y
                d_sq = ox * ox + oy * oy
                if 0.0001 < d_sq < radius * radius:
                    d = math.sqrt(d_sq)
                    weight = (radius - d) / radius
                    repulse_x += (ox / d) * weight
                    repulse_y += (oy / d) * weight
                    count += 1

        if count > 0:
            # Se o aliado estiver diretamente à frente bloqueando a rota, adiciona vetor de flanqueamento lateral
            dot = repulse_x * dir_x + repulse_y * dir_y
            if dot < -0.1:
                sign = 1.0 if (id(self.entity) % 2 == 0) else -1.0
                perp_x = -dir_y * sign
                perp_y = dir_x * sign
                repulse_x += perp_x * 0.85
                repulse_y += perp_y * 0.85

            blended_x = dir_x * 0.65 + repulse_x * 0.35
            blended_y = dir_y * 0.65 + repulse_y * 0.35
            blen = math.hypot(blended_x, blended_y)
            if blen > 0.01:
                return blended_x / blen, blended_y / blen
        return dir_x, dir_y

    def _move_with_local_avoidance(self, direction_x, direction_y, mapa_obj, dt):
        physics = self.entity.physics
        if physics.move(direction_x, direction_y, mapa_obj, dt):
            return

        # Desvio curto para entidades móveis que estejam bloqueando o caminho.
        for angle in (45, -45, 90, -90):
            radians = math.radians(angle)
            candidate_x = direction_x * math.cos(radians) - direction_y * math.sin(radians)
            candidate_y = direction_x * math.sin(radians) + direction_y * math.cos(radians)
            if physics.move(candidate_x, candidate_y, mapa_obj, dt):
                return

    def on_hear_sound(self, sound_x: float, sound_y: float):
        """Reação auditiva a disparos de arma de fogo ou ruídos próximos."""
        self.investigate_pos = (sound_x, sound_y)
        self.investigate_timer = self.rng.uniform(5.0, 8.0)
        self.idle_state = "investigate"

    def on_ally_alert(self, caller):
        """Reação a alerta de socorro de aliados próximos."""
        if getattr(self.entity, "role", None) == "animal":
            self.panic_timer = self.rng.uniform(3.5, 6.0)
            self.animal_state = "wander"
        elif getattr(self.entity, "role", None) == "enemy":
            self.investigate_pos = (caller.x, caller.y)
            self.investigate_timer = 6.0

    def _alert_nearby_herd(self, mapa_obj, radius: float = 7.0):
        """Propaga alarme para animais do mesmo rebanho em pânico."""
        if not hasattr(mapa_obj, "entidades") or self.herd_alert_cooldown > 0:
            return
        self.herd_alert_cooldown = 3.5
        radius_sq = radius * radius
        for other in mapa_obj.entidades:
            if (
                other is not self.entity
                and getattr(other, "role", None) == "animal"
                and getattr(other, "nome", None) == self.entity.nome
            ):
                dx = other.x - self.entity.x
                dy = other.y - self.entity.y
                if dx * dx + dy * dy <= radius_sq and getattr(other, "ai", None):
                    other.ai.panic_timer = self.rng.uniform(3.5, 6.0)

    def _update_animal(self, mapa_obj, dt):
        player = getattr(mapa_obj, "jogador", None)
        physics = self.entity.physics
        if physics.speed == 0:
            return

        combat = getattr(self.entity, "combat", None)
        hp = getattr(combat, "hp", 100)
        hp_max = getattr(combat, "hp_max", 100)
        is_hurt = hp < hp_max

        self.panic_timer = max(0.0, self.panic_timer - dt)
        self.herd_alert_cooldown = max(0.0, self.herd_alert_cooldown - dt)
        self.charge_cooldown = max(0.0, self.charge_cooldown - dt)

        dx = player.x - self.entity.x if player else 0.0
        dy = player.y - self.entity.y if player else 0.0
        dist = math.hypot(dx, dy) if player else 999.0

        ai_mode = getattr(self.entity, "ai_mode", "flee")

        # 1. Territorial agressivo (Javali, Touro, Raposa):
        if ai_mode == "territorial" and (is_hurt or dist < 2.5):
            self._alert_nearby_herd(mapa_obj)
            # Investida violenta (Charge)
            if self.charge_timer > 0:
                self.charge_timer -= dt
                cx, cy = self.charge_dir
                self._move_with_local_avoidance(cx, cy, mapa_obj, dt * 1.8)
                if dist < 1.4 and player:
                    self.entity.atacar_espada(player.x, player.y, mapa_obj)
                return

            # Gatilho de investida
            if self.charge_cooldown <= 0 and 1.5 < dist < 6.5:
                self.charge_timer = 1.0
                self.charge_cooldown = self.rng.uniform(3.5, 5.0)
                c_dist = max(0.01, dist)
                self.charge_dir = (dx / c_dist, dy / c_dist)
                if hasattr(mapa_obj, "particulas"):
                    mapa_obj.particulas.emit(self.entity.x, self.entity.y, "dust", 5)
                self._move_with_local_avoidance(self.charge_dir[0], self.charge_dir[1], mapa_obj, dt * 1.8)
                return

            # Perseguição agressiva normal
            if dist > 0.01:
                dir_x = dx / dist
                dir_y = dy / dist
                dir_x, dir_y = self._apply_flocking_separation(mapa_obj, dir_x, dir_y)
                self._move_with_local_avoidance(dir_x, dir_y, mapa_obj, dt)
            if dist < 1.4 and player:
                self.entity.atacar_espada(player.x, player.y, mapa_obj)
            return

        # 2. Fuga quando em perigo ou sob alerta de manada
        is_fleeing = (
            (ai_mode == "flee" and (dist < 4.8 or is_hurt or self.panic_timer > 0))
            or (ai_mode == "territorial" and dist < 4.0 and not is_hurt)
        )
        if is_fleeing:
            if is_hurt:
                self._alert_nearby_herd(mapa_obj)
            if dist > 0.01:
                flee_x = -dx / dist
                flee_y = -dy / dist
            else:
                flee_x = self.rng.choice([-1.0, 1.0])
                flee_y = self.rng.choice([-1.0, 1.0])

            # Dispersão com os companheiros para não correrem colados
            flee_x, flee_y = self._apply_flocking_separation(mapa_obj, flee_x, flee_y)
            self._move_with_local_avoidance(flee_x, flee_y, mapa_obj, dt * 1.18)
            return

        # 3. Pastagem pacífica / Perambulação relaxada
        self.animal_timer -= dt
        if self.animal_timer <= 0:
            if self.rng.random() < 0.6:
                self.animal_state = "graze"
                self.animal_timer = self.rng.uniform(2.0, 5.0)
                self.animal_dir = (0.0, 0.0)
            else:
                self.animal_state = "wander"
                self.animal_timer = self.rng.uniform(1.0, 2.5)
                angle = self.rng.uniform(0, 2 * math.pi)
                self.animal_dir = (math.cos(angle), math.sin(angle))

        if self.animal_state == "wander":
            wx, wy = self.animal_dir
            if wx != 0 or wy != 0:
                wx, wy = self._apply_flocking_separation(mapa_obj, wx, wy)
                self._move_with_local_avoidance(wx, wy, mapa_obj, dt * 0.45)
        else:
            self.entity.moving = False

    def falar(self, mapa_obj=None) -> str:
        """Gera fala amigável e contextuada com a profissão/tipo do NPC."""
        dialogos = NPC_DIALOGOS.get(
            getattr(self.entity, "nome", ""),
            [
                "Olá, viajante! Tenha um bom dia em nossa cidade.",
                "Que a luz dos lampiões guie seus passos em segurança.",
                "Fique perto das tochas quando o sol se pôr!",
            ],
        )
        self.current_dialog = self.rng.choice(dialogos)
        self.dialog_timer = 5.0
        if mapa_obj and hasattr(mapa_obj, "particulas"):
            mapa_obj.particulas.emit(self.entity.x, self.entity.y - 0.5, "dust", 3)
        return self.current_dialog

    def _update_npc(self, mapa_obj, dt):
        player = getattr(mapa_obj, "jogador", None)
        physics = self.entity.physics
        if physics.speed == 0:
            return

        if self.dialog_timer > 0:
            self.dialog_timer = max(0.0, self.dialog_timer - dt)
            if self.dialog_timer == 0:
                self.current_dialog = None

        ai_mode = getattr(self.entity, "ai_mode", "citizen")

        # 1. GUARDA DA CIDADE: Patrulha e combate defensivo ativo
        if ai_mode == "guard":
            closest_enemy = None
            min_enemy_dist = 8.5
            if hasattr(mapa_obj, "entidades"):
                for other in mapa_obj.entidades:
                    if other is not self.entity and getattr(other, "role", None) == "enemy":
                        combat = getattr(other, "combat", None)
                        if combat and not getattr(combat, "dead", False):
                            d = math.hypot(other.x - self.entity.x, other.y - self.entity.y)
                            if d < min_enemy_dist:
                                min_enemy_dist = d
                                closest_enemy = other

            if closest_enemy:
                edx = closest_enemy.x - self.entity.x
                edy = closest_enemy.y - self.entity.y
                if min_enemy_dist > 0.01:
                    dir_x = edx / min_enemy_dist
                    dir_y = edy / min_enemy_dist
                    self._move_with_local_avoidance(dir_x, dir_y, mapa_obj, dt * 1.1)

                if min_enemy_dist < 1.3:
                    if hasattr(self.entity, "atacar_espada"):
                        self.entity.atacar_espada(closest_enemy.x + 0.5, closest_enemy.y + 0.5, mapa_obj)
                    else:
                        c = getattr(closest_enemy, "combat", None)
                        if c:
                            c.take_damage(getattr(getattr(self.entity, "combat", None), "damage", 18), mapa_obj)
                return

        # 2. CIDADÃOS E ALDEÕES:
        # Quando o jogador se aproxima (raio < 1.8 tiles), o NPC para e olha para ele
        if player:
            p_dx = player.x - self.entity.x
            p_dy = player.y - self.entity.y
            p_dist = math.hypot(p_dx, p_dy)
            if p_dist < 1.8:
                self.entity.moving = False
                sprite = getattr(self.entity, "sprite", None)
                if sprite and hasattr(sprite, "set_direction"):
                    sprite.set_direction(p_dx, p_dy)
                return

        # Perambulação urbana serena
        self.idle_timer -= dt
        if self.idle_timer <= 0:
            if self.rng.random() < 0.6:
                self.idle_state = "stand"
                self.idle_timer = self.rng.uniform(2.5, 5.0)
                self.idle_dir = (0.0, 0.0)
            else:
                self.idle_state = "walk"
                self.idle_timer = self.rng.uniform(1.2, 3.0)
                ang = self.rng.uniform(0, 2 * math.pi)
                self.idle_dir = (math.cos(ang), math.sin(ang))

        if self.idle_state == "walk":
            wx, wy = self.idle_dir
            speed_mult = 0.5 if ai_mode == "guard" else 0.35
            self._move_with_local_avoidance(wx, wy, mapa_obj, dt * speed_mult)
        else:
            self.entity.moving = False

    def _handle_fire_avoidance(self, mapa_obj, player, dt) -> bool:
        if not hasattr(mapa_obj, "get_nearest_bonfire"):
            return False

        nearest_fire = mapa_obj.get_nearest_bonfire(self.entity.x, self.entity.y)
        if not nearest_fire:
            return False

        fire_x, fire_y, dist_to_fire = nearest_fire

        # 1. Queimadura direta se pisar na fogueira
        if dist_to_fire <= 1.4:
            combat = getattr(self.entity, "combat", None)
            if combat:
                combat.take_damage(max(2, int(20 * dt)), mapa_obj)
            flee_x = (self.entity.x - fire_x) / max(0.01, dist_to_fire)
            flee_y = (self.entity.y - fire_y) / max(0.01, dist_to_fire)
            self._move_with_local_avoidance(flee_x, flee_y, mapa_obj, dt * 1.5)
            return True

        # 2. Medo da luz direta da fogueira
        if dist_to_fire <= 4.2:
            flee_x = (self.entity.x - fire_x) / max(0.01, dist_to_fire)
            flee_y = (self.entity.y - fire_y) / max(0.01, dist_to_fire)
            flee_tangent_x = -flee_y * 0.35 * self.circle_sign
            flee_tangent_y = flee_x * 0.35 * self.circle_sign
            fx = flee_x + flee_tangent_x
            fy = flee_y + flee_tangent_y
            flen = math.hypot(fx, fy)
            if flen > 0.01:
                self._move_with_local_avoidance(fx / flen, fy / flen, mapa_obj, dt * 1.15)
            return True

        # 3. Jogador abrigado dentro do raio seguro da fogueira
        if player and mapa_obj.is_near_bonfire(player.x, player.y, radius=3.8):
            dx = player.x - self.entity.x
            dy = player.y - self.entity.y
            dist_to_player = math.hypot(dx, dy)

            if dist_to_fire > 5.5 and dist_to_player > 5.0:
                dir_x = dx / max(0.01, dist_to_player)
                dir_y = dy / max(0.01, dist_to_player)
                self._move_with_local_avoidance(dir_x, dir_y, mapa_obj, dt)
                return True
            else:
                self.circle_timer -= dt
                if self.circle_timer <= 0:
                    self.circle_timer = self.rng.uniform(1.5, 3.5)
                    self.circle_sign *= -1.0

                tangent_x = -(self.entity.y - fire_y) / max(0.01, dist_to_fire) * self.circle_sign
                tangent_y = (self.entity.x - fire_x) / max(0.01, dist_to_fire) * self.circle_sign

                radial_adjust = 0.0
                if dist_to_fire < 4.5:
                    radial_adjust = 0.5
                elif dist_to_fire > 5.4:
                    radial_adjust = -0.5

                radial_x = (self.entity.x - fire_x) / max(0.01, dist_to_fire) * radial_adjust
                radial_y = (self.entity.y - fire_y) / max(0.01, dist_to_fire) * radial_adjust

                mx = tangent_x + radial_x
                my = tangent_y + radial_y
                mlen = math.hypot(mx, my)
                if mlen > 0.01:
                    self._move_with_local_avoidance(mx / mlen, my / mlen, mapa_obj, dt * 0.8)
                return True

        return False

    def _handle_sunlight(self, mapa_obj, dt) -> bool:
        time_system = getattr(mapa_obj, "time_system", None)
        if not time_system or not getattr(time_system, "is_day", False):
            return False
        if "nocturnal" not in getattr(self.entity, "tags", ()):
            return False

        self.sun_burn_accumulator += dt
        if self.sun_burn_accumulator >= 0.5:
            self.sun_burn_accumulator -= 0.5
            combat = getattr(self.entity, "combat", None)
            if combat:
                combat.take_damage(10, mapa_obj)
            if hasattr(mapa_obj, "particulas"):
                mapa_obj.particulas.emit(self.entity.x, self.entity.y, "hit", 4)
            if hasattr(mapa_obj, "criar_texto_dano"):
                mapa_obj.criar_texto_dano(self.entity.x, self.entity.y - 0.8, "! SOL !", (255, 180, 50))
        return True

    def update(self, mapa_obj, dt):
        if not self.active:
            return

        if getattr(self.entity, "role", None) == "animal":
            self._update_animal(mapa_obj, dt)
            return

        if getattr(self.entity, "role", None) == "npc":
            self._update_npc(mapa_obj, dt)
            return

        self._handle_sunlight(mapa_obj, dt)
        combat = getattr(self.entity, "combat", None)
        if combat and getattr(combat, "dead", False):
            return

        player = getattr(mapa_obj, "jogador", None)
        physics = self.entity.physics
        self.ranged_decision_timer = max(0.0, self.ranged_decision_timer - dt)

        if physics.speed == 0:
            return

        if self._handle_fire_avoidance(mapa_obj, player, dt):
            return

        if not player:
            return

        dx = player.x - self.entity.x
        dy = player.y - self.entity.y
        dist = math.hypot(dx, dy)
        attack_mode = getattr(self.entity, "ai_mode", "melee")

        # 1. Distância Longa (> 13 tiles): Patrulha / Investigação de sons
        if dist >= 13.0:
            if self.investigate_timer > 0 and self.investigate_pos:
                self.investigate_timer -= dt
                ix, iy = self.investigate_pos
                idx = ix - self.entity.x
                idy = iy - self.entity.y
                idist = math.hypot(idx, idy)
                if idist > 0.8:
                    dir_x = idx / idist
                    dir_y = idy / idist
                    dir_x, dir_y = self._navigation_direction(mapa_obj, dir_x, dir_y, dt)
                    self._move_with_local_avoidance(dir_x, dir_y, mapa_obj, dt * 0.75)
                else:
                    self.investigate_pos = None
            else:
                # Perambulação / Patrulha relaxada (não fica estátua)
                self.idle_timer -= dt
                if self.idle_timer <= 0:
                    if self.rng.random() < 0.65:
                        self.idle_state = "stand"
                        self.idle_timer = self.rng.uniform(2.0, 4.5)
                        self.idle_dir = (0.0, 0.0)
                    else:
                        self.idle_state = "walk"
                        self.idle_timer = self.rng.uniform(1.2, 2.8)
                        ang = self.rng.uniform(0, 2 * math.pi)
                        self.idle_dir = (math.cos(ang), math.sin(ang))

                if self.idle_state == "walk":
                    wx, wy = self.idle_dir
                    self._move_with_local_avoidance(wx, wy, mapa_obj, dt * 0.35)
                else:
                    self.entity.moving = False
            return

        # 2. Táticas Especializadas de Perseguição e Combate
        # A) STALKER NOTURNO: Espreita nas sombras e dá bote súbito
        if attack_mode == "stalker":
            if self.pounce_timer > 0:
                self.pounce_timer -= dt
                dir_x = dx / dist
                dir_y = dy / dist
                dir_x, dir_y = self._navigation_direction(mapa_obj, dir_x, dir_y, dt)
                dir_x, dir_y = self._apply_flocking_separation(mapa_obj, dir_x, dir_y)
                self._move_with_local_avoidance(dir_x, dir_y, mapa_obj, dt * 1.55)
            elif 4.8 < dist < 9.5:
                # Ronda lateral em volta do jogador esperando a brecha
                self.stalk_timer -= dt
                if self.stalk_timer <= 0:
                    self.pounce_timer = self.rng.uniform(1.4, 2.0)
                    self.stalk_timer = self.rng.uniform(3.0, 5.0)
                    if hasattr(mapa_obj, "criar_texto_dano"):
                        mapa_obj.criar_texto_dano(self.entity.x, self.entity.y - 0.8, "! BOTE !", (255, 60, 60))
                else:
                    tangent_x = -dy / dist * self.circle_sign
                    tangent_y = dx / dist * self.circle_sign
                    radial = 0.0
                    if dist < 5.5: radial = -0.35
                    elif dist > 7.5: radial = 0.35
                    dir_x = tangent_x * 0.75 + (dx / dist) * radial
                    dir_y = tangent_y * 0.75 + (dy / dist) * radial
                    dlen = math.hypot(dir_x, dir_y)
                    if dlen > 0.01:
                        self._move_with_local_avoidance(dir_x / dlen, dir_y / dlen, mapa_obj, dt * 0.95)
            elif 0.8 < dist:
                dir_x = dx / dist
                dir_y = dy / dist
                dir_x, dir_y = self._navigation_direction(mapa_obj, dir_x, dir_y, dt)
                dir_x, dir_y = self._apply_flocking_separation(mapa_obj, dir_x, dir_y)
                self._move_with_local_avoidance(dir_x, dir_y, mapa_obj, dt * 1.25)

            if dist < 1.6:
                self.entity.atacar_espada(player.x, player.y, mapa_obj)
            return

        # B) RUNNER / ATIRADOR HÍBRIDO: Kiting tático (recua e atira)
        if attack_mode in {"ranged", "hybrid"} and 1.4 < dist < 3.8:
            retreat_x = -dx / dist
            retreat_y = -dy / dist
            self.circle_timer -= dt
            if self.circle_timer <= 0:
                self.circle_timer = self.rng.uniform(1.0, 2.2)
                self.circle_sign *= -1.0
            strafe_x = -retreat_y * self.circle_sign * 0.55
            strafe_y = retreat_x * self.circle_sign * 0.55
            kx = retreat_x * 0.7 + strafe_x * 0.3
            ky = retreat_y * 0.7 + strafe_y * 0.3
            klen = math.hypot(kx, ky)
            if klen > 0.01:
                kx, ky = self._apply_flocking_separation(mapa_obj, kx / klen, ky / klen)
                self._move_with_local_avoidance(kx, ky, mapa_obj, dt * 0.88)

            if self.ranged_decision_timer == 0:
                self.entity.atirar(player.x, player.y, mapa_obj, "enemy")
                self.ranged_decision_timer = (
                    self.entity.ranged_interval
                    + self.rng.uniform(-0.15, 0.2)
                )
            return

        # C) AVANÇO PADRÃO COM FLOCKING SEPARATION (Walkers, Tanks e aproximação normal)
        if 0.8 < dist < 12.0:
            dir_x = dx / dist
            dir_y = dy / dist
            dir_x, dir_y = self._navigation_direction(mapa_obj, dir_x, dir_y, dt)
            dir_x, dir_y = self._apply_flocking_separation(mapa_obj, dir_x, dir_y)
            self._move_with_local_avoidance(dir_x, dir_y, mapa_obj, dt)

        # Ataques corpo a corpo e tiros
        if dist < 8.0:
            if dist < 1.6 and attack_mode in {"melee", "hybrid", "stalker"}:
                self.entity.atacar_espada(player.x, player.y, mapa_obj)
            elif dist > 2.5 and attack_mode in {"ranged", "hybrid"}:
                if self.ranged_decision_timer == 0:
                    self.entity.atirar(player.x, player.y, mapa_obj, "enemy")
                    self.ranged_decision_timer = (
                        self.entity.ranged_interval
                        + self.rng.uniform(-0.15, 0.2)
                    )
