import unittest

from graphics.particles import ParticleSystem


class ParticleSystemTests(unittest.TestCase):
    def test_particle_count_is_capped(self):
        particles = ParticleSystem()

        particles.emit(0, 0, "leaf", ParticleSystem.MAX_PARTICLES + 50)

        self.assertEqual(len(particles.particles), ParticleSystem.MAX_PARTICLES)

    def test_expired_particles_are_removed(self):
        particles = ParticleSystem()
        particles.emit(0, 0, "hit", 4)

        class Map:
            jogador = None

        particles.update(5.0, Map())

        self.assertEqual(particles.particles, [])


if __name__ == "__main__":
    unittest.main()
