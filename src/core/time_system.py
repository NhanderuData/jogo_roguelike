# src/core/time_system.py
import pygame
from core import config

class TimeSystem:
    def __init__(self):
        self.tempo_total = 0.0
        self.duracao_dia = 60.0 # Dia dura 60 segundos
        self.cor_ambiente = (0, 0, 0, 0) # RGBA (0 alpha = transparente)
        
        # Cores para cada fase
        self.COR_NOITE = (10, 10, 30)
        self.COR_AMANHECER = (255, 100, 50) # Laranja
        self.COR_DIA = (255, 255, 255) # Transparente na prática

    def update(self, dt):
        self.tempo_total += dt
        if self.tempo_total >= self.duracao_dia:
            self.tempo_total -= self.duracao_dia
            
        self.calcular_cor()

    def calcular_cor(self):
        # 0% a 100% do dia
        progresso = self.tempo_total / self.duracao_dia 
        alpha = 0
        if 0.5 < progresso <= 0.6: # Entardecer
            fator = (progresso - 0.5) * 10 # 0 a 1
            alpha = int(fator * 180)
        elif 0.6 < progresso <= 0.9: # Noite
            alpha = 180
        elif 0.9 < progresso <= 1.0: # Amanhecer
            fator = (1.0 - progresso) * 10 # 1 a 0 (Invertido)
            alpha = int(fator * 180)
            
        self.cor_ambiente = (10, 10, 35, alpha)

    def obter_cor(self):
        return self.cor_ambiente