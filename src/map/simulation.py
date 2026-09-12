from __future__ import annotations

import math
from entities.actor import Entidade
from entities.loot import LootDrop


class WorldSimulation:
    """Atualiza runtime do mundo sem participar da geração ou renderização."""

    def __init__(self, world):
        self.world = world
        self.night_spawn_timer = 6.0
        self.bonfire_buff_timer = 0.0

    def update(self, dt: float) -> None:
        world = self.world
        if world.jogador:
            world.jogador.update(dt, world)

        for entity in tuple(world.entidades):
            if entity is not world.jogador:
                entity.update(dt, world)

        self._update_night_events(dt)
        self._update_bonfire_sanctuary(dt)
        self._resolve_deaths()
        self._update_lifetime_collection(world.projeteis, dt, world)
        self._update_lifetime_collection(world.efeitos, dt)
        self._update_lifetime_collection(world.textos, dt)

        for loot in world.items_no_chao:
            loot.update(dt)
        world.particulas.update(dt, world)
        if hasattr(world, "atualizar_regeneracao_safras"):
            world.atualizar_regeneracao_safras()

    def _update_night_events(self, dt: float) -> None:
        world = self.world
        time_system = getattr(world, "time_system", None)
        if not time_system:
            return

        if getattr(time_system, "is_night", False):
            self.night_spawn_timer -= dt
            if self.night_spawn_timer <= 0:
                self.night_spawn_timer = world.gameplay_rng.uniform(10.0, 16.0)
                current_stalkers = sum(
                    1 for e in world.entidades if "nocturnal" in getattr(e, "tags", ())
                )
                if current_stalkers < 5 and world.jogador:
                    spawn_count = min(2, 5 - current_stalkers)
                    for _ in range(spawn_count):
                        angle = world.gameplay_rng.uniform(0, 2 * math.pi)
                        dist = world.gameplay_rng.uniform(16.0, 24.0)
                        sx = int(world.jogador.x + math.cos(angle) * dist)
                        sy = int(world.jogador.y + math.sin(angle) * dist)
                        if 0 <= sx < world.largura and 0 <= sy < world.altura:
                            if not world.is_blocked_terrain(sx, sy):
                                stalker = Entidade(
                                    sx, sy, "Stalker Noturno", world.context, rng=world.gameplay_rng
                                )
                                world.entidades.append(stalker)
                                world.spatial_index.insert(stalker)
                                world.particulas.emit(sx, sy, "hit", 8)
                    world.context.audio.play("night_howl", 0.35)

    def _update_bonfire_sanctuary(self, dt: float) -> None:
        world = self.world
        player = getattr(world, "jogador", None)
        if not player:
            return

        is_near = hasattr(world, "is_near_bonfire") and world.is_near_bonfire(player.x, player.y, radius=3.8)
        player.near_campfire = is_near

        if is_near:
            self.bonfire_buff_timer += dt
            if self.bonfire_buff_timer >= 4.0:
                self.bonfire_buff_timer -= 4.0
                combat = getattr(player, "combat", None)
                if combat and combat.hp < combat.hp_max:
                    combat.heal(1)
                    if hasattr(world, "criar_texto_dano"):
                        world.criar_texto_dano(player.x, player.y - 0.8, "+1 HP", (80, 240, 120))


    def _resolve_deaths(self) -> None:
        world = self.world
        for entity in tuple(world.entidades):
            if entity is world.jogador or entity.hp > 0:
                continue

            definition = world.content.entities.get(entity.nome)
            if definition and definition.loot:
                if world.gameplay_rng.random() < definition.loot_chance:
                    item_name = world.gameplay_rng.choice(definition.loot)
                    world.items_no_chao.append(
                        LootDrop(entity.x, entity.y, item_name, world.content)
                    )

            tile = world.obter_tile(round(entity.x), round(entity.y)) if hasattr(world, "obter_tile") else None
            if tile and (getattr(entity, "is_static", False) or "tree" in getattr(entity, "tags", ())):
                tile.bloqueado = False

            tree_positions = getattr(world, "_tree_positions", None)
            if tree_positions is not None:
                tree_positions.discard((round(entity.x), round(entity.y)))

            if world.jogador:
                world.jogador.ganhar_xp(entity.xp_reward)

            particle_type = (
                "wood"
                if getattr(entity, "impact_material", None) == "wood" or "tree" in getattr(entity, "tags", ())
                else "hit"
            )
            world.particulas.emit(entity.x, entity.y, particle_type, 14)
            world.spatial_index.remove(entity)
            world.entidades.remove(entity)

    @staticmethod
    def _update_lifetime_collection(collection, dt, *args) -> None:
        survivors = []
        for item in collection:
            item.update(dt, *args)
            if getattr(item, "active", True) and getattr(item, "life", 1) > 0:
                survivors.append(item)
        collection[:] = survivors
