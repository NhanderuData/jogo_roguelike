# src/components/status.py
import logging

logger = logging.getLogger(__name__)


class StatusComponent:
    def __init__(self, entity, max_fome=100, max_sede=100):
        self.entity = entity
        
        # --- FOME ---
        self.fome = max_fome
        self.max_fome = max_fome
        self.timer_fome = 0
        
        # --- SEDE ---
        self.sede = max_sede
        self.max_sede = max_sede
        self.timer_sede = 0
        
        # --- SANGRAMENTO ---
        # Sangramento agora é um contador. Enquanto > 0, toma dano.
        self.sangramento = 0 
        self.timer_sangramento = 0
        self.energy_remaining = 0.0

    @property
    def speed_multiplier(self):
        return 1.35 if self.energy_remaining > 0 else 1.0

    def energize(self, duration):
        self.energy_remaining = max(self.energy_remaining, duration)

    def add_sangramento(self, qtd):
        """ Adiciona 'tempo' de sangramento ou intensidade """
        self.sangramento += qtd
        logger.debug("%s started bleeding", self.entity.nome)

    def curar_sangramento(self):
        self.sangramento = 0
        logger.debug("%s stopped bleeding", self.entity.nome)

    def comer(self, valor):
        self.fome += valor
        if self.fome > self.max_fome: self.fome = self.max_fome

    def beber(self, valor):
        self.sede += valor
        if self.sede > self.max_sede: self.sede = self.max_sede

    def update(self, dt):
        self.energy_remaining = max(0.0, self.energy_remaining - dt)
        self.timer_fome += dt
        if self.timer_fome >= 5.0:
            self.timer_fome -= 5.0
            if self.fome > 0:
                self.fome -= 1
            else:
                self.entity.tomar_dano(1) # Dano de fome

        # --- LÓGICA DE SEDE (Desce mais rápido que fome, ex: 3s) ---
        self.timer_sede += dt
        if self.timer_sede >= 3.0:
            self.timer_sede -= 3.0
            if self.sede > 0:
                self.sede -= 1
            else:
                self.entity.tomar_dano(1) # Dano de sede

        # --- LÓGICA DE SANGRAMENTO (Dano intermitente) ---
        if self.sangramento > 0:
            self.timer_sangramento += dt
            if self.timer_sangramento >= 2.0:
                self.timer_sangramento -= 2.0
                logger.debug("Applying bleeding damage to %s", self.entity.nome)
                self.entity.tomar_dano(2)
                self.sangramento -= 1 # O sangramento diminui sozinho lentamente ou fica fixo?
                # Se quiser que só pare com bandagem, remova a linha acima.
