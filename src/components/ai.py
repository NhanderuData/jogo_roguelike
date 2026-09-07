import heapq
import math
import random
from core import config

class AIComponent:
    def __init__(self, entity):
        self.entity = entity
        self.active = True
        self.path = []
        self.repath_timer = 0.0
        self.last_goal = None
        self.ranged_decision_timer = random.uniform(0.35, 0.8)

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
                self.repath_timer = 0.45 + random.uniform(0.0, 0.15)

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
        
    def update(self, mapa_obj, dt):
        if not self.active or self.entity.nome == "Heroi":
            return

        player = mapa_obj.jogador
        physics = self.entity.physics
        self.ranged_decision_timer = max(0.0, self.ranged_decision_timer - dt)
        
        if physics.speed == 0:
            return

        dx = player.x - self.entity.x
        dy = player.y - self.entity.y
        dist = (dx**2 + dy**2)**0.5
        
        if 0.8 < dist < 10:
            dir_x = dx / dist
            dir_y = dy / dist
            dir_x, dir_y = self._navigation_direction(mapa_obj, dir_x, dir_y, dt)
            self._move_with_local_avoidance(dir_x, dir_y, mapa_obj, dt)

        if dist < 8:
            if dist < 1.5:
    
                self.entity.atacar_espada(player.x, player.y, mapa_obj)
            
            elif dist > 3 and self.entity.nome in {"Runner", "Tank", "Troll", "REI"}:
                if self.ranged_decision_timer == 0:
                    self.entity.atirar(player.x, player.y, mapa_obj, "enemy")
                    interval = 1.25 if self.entity.nome == "Runner" else 1.8
                    self.ranged_decision_timer = interval + random.uniform(-0.15, 0.2)
