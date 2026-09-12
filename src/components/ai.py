import heapq
import math
import random
from core import config

class AIComponent:
    def __init__(self, entity, rng=None):
        self.entity = entity
        self.rng = rng or random
        self.active = True
        self.path = []
        self.repath_timer = 0.0
        self.last_goal = None
        self.ranged_decision_timer = self.rng.uniform(0.35, 0.8)
        self.animal_state = "graze"
        self.animal_timer = self.rng.uniform(1.5, 3.5)
        self.animal_dir = (0.0, 0.0)
        self.circle_timer = self.rng.uniform(1.5, 3.0)
        self.circle_sign = self.rng.choice((-1.0, 1.0))
        self.sun_burn_accumulator = 0.0

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

        goal = (round(mapa_obj.jogador.x), round(mapa_obj.jogador.y))
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

    def _update_animal(self, mapa_obj, dt):
        player = getattr(mapa_obj, "jogador", None)
        physics = self.entity.physics
        if physics.speed == 0:
            return

        combat = getattr(self.entity, "combat", None)
        hp = getattr(combat, "hp", 100)
        hp_max = getattr(combat, "hp_max", 100)
        is_hurt = hp < hp_max

        dx = player.x - self.entity.x if player else 0.0
        dy = player.y - self.entity.y if player else 0.0
        dist = math.hypot(dx, dy) if player else 999.0

        ai_mode = getattr(self.entity, "ai_mode", "flee")

        # 1. Territorial agressivo: ataca se ferido ou se o jogador invadir seu raio (dist < 2.2)
        if ai_mode == "territorial" and (is_hurt or dist < 2.2):
            if dist > 0.8:
                dir_x = dx / dist
                dir_y = dy / dist
                self._move_with_local_avoidance(dir_x, dir_y, mapa_obj, dt)
            if dist < 1.4:
                self.entity.atacar_espada(player.x, player.y, mapa_obj)
            return

        # 2. Fuga quando em perigo (ai_mode == flee e dist < 4.8 ou is_hurt)
        if (ai_mode == "flee" and (dist < 4.8 or is_hurt)) or (ai_mode == "territorial" and dist < 4.0 and not is_hurt):
            if dist > 0.01:
                flee_x = -dx / dist
                flee_y = -dy / dist
            else:
                flee_x = self.rng.choice([-1.0, 1.0])
                flee_y = self.rng.choice([-1.0, 1.0])
            self._move_with_local_avoidance(flee_x, flee_y, mapa_obj, dt * 1.1)
            return

        # 3. Pastagem pacífica / Perambulação relaxada
        self.animal_timer -= dt
        if self.animal_timer <= 0:
            # 60% chance pastando (idle), 40% chance andando devagar
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
                self._move_with_local_avoidance(wx, wy, mapa_obj, dt * 0.45)
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

            # Se ainda está fora da zona de ronda, aproxima-se até o limiar
            if dist_to_fire > 5.5 and dist_to_player > 5.0:
                dir_x = dx / max(0.01, dist_to_player)
                dir_y = dy / max(0.01, dist_to_player)
                self._move_with_local_avoidance(dir_x, dir_y, mapa_obj, dt)
                return True
            else:
                # Na borda da luz: ronda ameaçadoramente em arco/círculo
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
            mapa_obj.particulas.emit(self.entity.x, self.entity.y, "hit", 4)
            mapa_obj.criar_texto_dano(self.entity.x, self.entity.y - 0.8, "! SOL !", (255, 180, 50))
        return True

    def update(self, mapa_obj, dt):
        if not self.active:
            return

        if getattr(self.entity, "role", None) == "animal":
            self._update_animal(mapa_obj, dt)
            return

        self._handle_sunlight(mapa_obj, dt)
        combat = getattr(self.entity, "combat", None)
        if combat and combat.dead:
            return

        player = mapa_obj.jogador
        physics = self.entity.physics
        self.ranged_decision_timer = max(0.0, self.ranged_decision_timer - dt)
        
        if physics.speed == 0:
            return

        if self._handle_fire_avoidance(mapa_obj, player, dt):
            return

        dx = player.x - self.entity.x
        dy = player.y - self.entity.y
        dist = (dx**2 + dy**2)**0.5

        speed_factor = 1.25 if self.entity.ai_mode == "stalker" else 1.0
        
        if 0.8 < dist < 12:
            dir_x = dx / dist
            dir_y = dy / dist
            dir_x, dir_y = self._navigation_direction(mapa_obj, dir_x, dir_y, dt)
            self._move_with_local_avoidance(dir_x, dir_y, mapa_obj, dt * speed_factor)

        attack_mode = self.entity.ai_mode
        if dist < 8:
            if dist < 1.6 and attack_mode in {"melee", "hybrid", "stalker"}:
                self.entity.atacar_espada(player.x, player.y, mapa_obj)
            elif dist > 3 and attack_mode in {"ranged", "hybrid"}:
                if self.ranged_decision_timer == 0:
                    self.entity.atirar(player.x, player.y, mapa_obj, "enemy")
                    self.ranged_decision_timer = (
                        self.entity.ranged_interval
                        + self.rng.uniform(-0.15, 0.2)
                    )
