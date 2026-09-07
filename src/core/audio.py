from __future__ import annotations

from array import array
import math
import random

import pygame


class SoundManager:
    """Small procedural sound bank with a silent fallback."""

    def __init__(self) -> None:
        self.enabled = False
        self.sounds: dict[str, pygame.mixer.Sound] = {}
        self.ambient_channel: pygame.mixer.Channel | None = None
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=256)
            frequency, sample_format, channels = pygame.mixer.get_init()
            if sample_format != -16:
                return
            self._build_bank(frequency, channels)
            self.enabled = True
        except pygame.error:
            self.enabled = False

    def _build_bank(self, frequency: int, channels: int) -> None:
        specs = {
            "pistol": (0.075, 210.0, 70.0, 0.55),
            "shotgun": (0.16, 125.0, 42.0, 0.9),
            "smg": (0.045, 260.0, 95.0, 0.45),
            "melee": (0.11, 430.0, 115.0, 0.2),
            "pickup": (0.12, 520.0, 880.0, 0.05),
            "reload": (0.08, 330.0, 190.0, 0.3),
            "empty": (0.045, 95.0, 80.0, 0.15),
            "hurt": (0.12, 95.0, 48.0, 0.5),
            "impact_stone": (0.055, 180.0, 75.0, 0.75),
            "impact_wood": (0.07, 145.0, 90.0, 0.55),
            "impact_metal": (0.08, 720.0, 310.0, 0.18),
            "impact_water": (0.09, 105.0, 55.0, 0.82),
            "impact_flesh": (0.065, 115.0, 58.0, 0.68),
            "impact_armor": (0.075, 920.0, 380.0, 0.22),
            "critical": (0.11, 540.0, 980.0, 0.12),
            "casing": (0.045, 1350.0, 620.0, 0.08),
            "wind": (3.0, 72.0, 88.0, 0.92),
            "bird": (0.22, 780.0, 1380.0, 0.05),
        }
        for name, spec in specs.items():
            self.sounds[name] = self._synthesize(frequency, channels, name, *spec)

    @staticmethod
    def _synthesize(
        sample_rate: int,
        channels: int,
        seed_name: str,
        duration: float,
        start_frequency: float,
        end_frequency: float,
        noise_mix: float,
    ) -> pygame.mixer.Sound:
        rng = random.Random(sum(ord(char) for char in seed_name))
        frames = max(1, int(sample_rate * duration))
        samples = array("h")
        phase = 0.0
        for index in range(frames):
            progress = index / frames
            frequency = start_frequency + (end_frequency - start_frequency) * progress
            phase += 2 * math.pi * frequency / sample_rate
            envelope = (1.0 - progress) ** 2
            tone = math.sin(phase)
            noise = rng.uniform(-1.0, 1.0)
            value = int(15000 * envelope * ((1 - noise_mix) * tone + noise_mix * noise))
            for _ in range(channels):
                samples.append(value)
        return pygame.mixer.Sound(buffer=samples.tobytes())

    def play(self, name: str, volume: float = 1.0) -> None:
        if not self.enabled:
            return
        sound = self.sounds.get(name)
        if sound:
            sound.set_volume(max(0.0, min(1.0, volume)))
            sound.play()

    def play_ambient(self, name: str, volume: float = 0.12) -> None:
        if not self.enabled:
            return
        self.stop_ambient()
        sound = self.sounds.get(name)
        if sound:
            sound.set_volume(max(0.0, min(1.0, volume)))
            self.ambient_channel = sound.play(loops=-1)

    def stop_ambient(self) -> None:
        if self.ambient_channel:
            self.ambient_channel.fadeout(300)
            self.ambient_channel = None
