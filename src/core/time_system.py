# src/core/time_system.py
from enum import Enum
import pygame
from core import config


class TimePhase(str, Enum):
    DAY = "dia"
    DUSK = "entardecer"
    NIGHT = "noite"
    DAWN = "amanhecer"


class TimeSystem:
    def __init__(self):
        self.tempo_total = 0.0
        self.duracao_dia = 90.0
        self.max_night_alpha = 75
        self.cor_ambiente = (0, 0, 0, 0) # RGBA (0 alpha = transparente)
        self.day_count = 1
        self._previous_phase = TimePhase.DAY
        self.current_phase = TimePhase.DAY
        self.just_became_night = False
        self.just_became_dawn = False
        
        # Cores para cada fase
        self.COR_NOITE = (10, 10, 30)
        self.COR_AMANHECER = (255, 100, 50) # Laranja
        self.COR_DIA = (255, 255, 255) # Transparente na prática

    @property
    def progress(self) -> float:
        return max(0.0, min(1.0, self.tempo_total / self.duracao_dia))

    @property
    def is_night(self) -> bool:
        return self.current_phase == TimePhase.NIGHT

    @property
    def is_day(self) -> bool:
        return self.current_phase == TimePhase.DAY

    @property
    def is_dusk(self) -> bool:
        return self.current_phase == TimePhase.DUSK

    @property
    def is_dawn(self) -> bool:
        return self.current_phase == TimePhase.DAWN

    @property
    def phase_label(self) -> str:
        labels = {
            TimePhase.DAY: "Dia",
            TimePhase.DUSK: "Entardecer",
            TimePhase.NIGHT: "Noite",
            TimePhase.DAWN: "Amanhecer",
        }
        return labels.get(self.current_phase, "Dia")

    def update(self, dt):
        self.tempo_total += dt
        if self.tempo_total >= self.duracao_dia:
            self.tempo_total -= self.duracao_dia
            self.day_count += 1
            
        self.calcular_cor()

    def calcular_cor(self):
        progresso = self.progress
        alpha = 0
        nova_fase = TimePhase.DAY

        if 0.5 < progresso <= 0.6: # Entardecer
            nova_fase = TimePhase.DUSK
            fator = (progresso - 0.5) * 10 # 0 a 1
            alpha = int(fator * self.max_night_alpha)
        elif 0.6 < progresso <= 0.9: # Noite
            nova_fase = TimePhase.NIGHT
            alpha = self.max_night_alpha
        elif 0.9 < progresso <= 1.0: # Amanhecer
            nova_fase = TimePhase.DAWN
            fator = (1.0 - progresso) * 10 # 1 a 0 (Invertido)
            alpha = int(fator * self.max_night_alpha)
        else:
            nova_fase = TimePhase.DAY
            alpha = 0

        # Disparadores de transição de fase
        if nova_fase == TimePhase.NIGHT and self._previous_phase != TimePhase.NIGHT:
            self.just_became_night = True
        elif (nova_fase in (TimePhase.DAWN, TimePhase.DAY)) and self._previous_phase == TimePhase.NIGHT:
            self.just_became_dawn = True

        self._previous_phase = nova_fase
        self.current_phase = nova_fase
        self.cor_ambiente = (28, 38, 64, alpha)

    def consume_event(self, event_name: str) -> bool:
        if event_name == "night" and self.just_became_night:
            self.just_became_night = False
            return True
        if event_name == "dawn" and self.just_became_dawn:
            self.just_became_dawn = False
            return True
        return False

    def obter_cor(self):
        return self.cor_ambiente
