import unittest
import pygame

from core.context import GameContext
from core.input_manager import InputManager
from core.time_system import TimeSystem, TimePhase
from core.content import ContentCatalog
from entities.actor import Entidade
from graphics import recursos
from map.map_gen import Mapa


class NightEventsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((1, 1), pygame.NOFRAME)
        recursos.carregar_tudo()
        cls.catalog = ContentCatalog.load_default()
        cls.context = GameContext(
            input=InputManager(),
            content=cls.catalog,
        )

    def test_time_system_phases_and_transitions(self):
        ts = TimeSystem()
        self.assertEqual(ts.current_phase, TimePhase.DAY)
        self.assertTrue(ts.is_day)
        self.assertFalse(ts.is_night)
        self.assertEqual(ts.day_count, 1)

        # Avança para entardecer (55%)
        ts.tempo_total = ts.duracao_dia * 0.55
        ts.calcular_cor()
        self.assertTrue(ts.is_dusk)

        # Avança para noite (70%)
        ts.tempo_total = ts.duracao_dia * 0.70
        ts.calcular_cor()
        self.assertTrue(ts.is_night)
        self.assertTrue(ts.just_became_night)
        self.assertTrue(ts.consume_event("night"))
        self.assertFalse(ts.consume_event("night")) # Já consumido

        # Avança para amanhecer (95%)
        ts.tempo_total = ts.duracao_dia * 0.95
        ts.calcular_cor()
        self.assertTrue(ts.is_dawn)
        self.assertTrue(ts.just_became_dawn)
        self.assertTrue(ts.consume_event("dawn"))

        # Completa ciclo para dia seguinte
        ts.update(ts.duracao_dia * 0.10)
        self.assertEqual(ts.day_count, 2)
        self.assertTrue(ts.is_day)

    def test_stalker_noturno_catalog_entry(self):
        catalog = self.catalog
        self.assertIn("Stalker Noturno", catalog.entities)
        stalker_def = catalog.entities["Stalker Noturno"]
        self.assertEqual(stalker_def.role, "enemy")
        self.assertEqual(stalker_def.ai_mode, "stalker")
        self.assertIn("nocturnal", stalker_def.tags)
        self.assertGreater(stalker_def.speed, 5.0)
        self.assertGreater(stalker_def.damage, 10)

    def test_bonfire_proximity_query(self):
        mapa = Mapa(self.context, seed=42)
        mapa.bonfire_positions.clear()
        mapa.bonfire_positions.add((10, 10))

        # (10.5, 10.5) é o centro da fogueira
        self.assertTrue(mapa.is_near_bonfire(10.5, 10.5, radius=1.0))
        self.assertTrue(mapa.is_near_bonfire(12.0, 10.5, radius=2.0))
        self.assertFalse(mapa.is_near_bonfire(20.0, 20.0, radius=4.0))

        nearest = mapa.get_nearest_bonfire(10.5, 12.5)
        self.assertIsNotNone(nearest)
        bx, by, dist = nearest
        self.assertAlmostEqual(bx, 10.5)
        self.assertAlmostEqual(by, 10.5)
        self.assertAlmostEqual(dist, 2.0)

    def test_enemy_flees_from_bonfire(self):
        mapa = Mapa(self.context, seed=42)
        mapa.bonfire_positions.clear()
        mapa.bonfire_positions.add((10, 10)) # Centro em (10.5, 10.5)

        # Posiciona inimigo a 2 tiles da fogueira em (12.5, 10.5)
        inimigo = Entidade(12.5, 10.5, "Stalker Noturno", self.context)
        initial_x = inimigo.x

        # Atualiza a IA
        inimigo.ai.update(mapa, 0.2)

        # O inimigo deve ter recuado para longe da fogueira (para a direita, x > initial_x)
        self.assertGreater(
            inimigo.x,
            initial_x,
            "Inimigo deve recuar para longe da fogueira",
        )

    def test_player_near_bonfire_status(self):
        mapa = Mapa(self.context, seed=42)
        mapa.bonfire_positions.clear()
        mapa.bonfire_positions.add((15, 15))

        # Jogador perto da fogueira
        mapa.jogador.x, mapa.jogador.y = 15.5, 16.0
        mapa.simulation._update_bonfire_sanctuary(0.1)
        self.assertTrue(mapa.jogador.near_campfire)

        # Jogador longe da fogueira
        mapa.jogador.x, mapa.jogador.y = 30.0, 30.0
        mapa.simulation._update_bonfire_sanctuary(0.1)
        self.assertFalse(mapa.jogador.near_campfire)


if __name__ == "__main__":
    unittest.main()
