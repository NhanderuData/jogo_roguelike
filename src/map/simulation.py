from __future__ import annotations

from entities.loot import LootDrop


class WorldSimulation:
    """Atualiza runtime do mundo sem participar da geração ou renderização."""

    def __init__(self, world):
        self.world = world

    def update(self, dt: float) -> None:
        world = self.world
        if world.jogador:
            world.jogador.update(dt, world)

        for entity in tuple(world.entidades):
            if entity is not world.jogador:
                entity.update(dt, world)

        self._resolve_deaths()
        self._update_lifetime_collection(world.projeteis, dt, world)
        self._update_lifetime_collection(world.efeitos, dt)
        self._update_lifetime_collection(world.textos, dt)

        for loot in world.items_no_chao:
            loot.update(dt)
        world.particulas.update(dt, world)

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
