# src/components/status.py
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

        # --- BUFFS & EFEITOS DE ALIMENTOS ---
        self.night_vision_timer = 0.0
        self.regen_timer = 0.0
        self.dizziness_timer = 0.0
        self.timer_regen_tick = 0.0

    @property
    def speed_multiplier(self):
        base = 1.35 if self.energy_remaining > 0 else 1.0
        if self.dizziness_timer > 0:
            base *= 0.82
        return base

    def energize(self, duration):
        self.energy_remaining = max(self.energy_remaining, duration)

    def aplicar_visao_noturna(self, duracao=45.0):
        self.night_vision_timer = max(self.night_vision_timer, float(duracao))
        logger.info("%s activated night vision for %.1fs", getattr(self.entity, "nome", "Player"), duracao)

    def aplicar_regeneracao(self, duracao=12.0):
        self.regen_timer = max(self.regen_timer, float(duracao))
        self.energy_remaining = max(self.energy_remaining, float(duracao) * 0.5)
        logger.info("%s activated gradual regeneration for %.1fs", getattr(self.entity, "nome", "Player"), duracao)

    def aplicar_tontura(self, duracao=8.0):
        self.dizziness_timer = max(self.dizziness_timer, float(duracao))
        logger.info("%s became dizzy for %.1fs", getattr(self.entity, "nome", "Player"), duracao)

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
        if self.night_vision_timer > 0:
            self.night_vision_timer = max(0.0, self.night_vision_timer - dt)
        if self.dizziness_timer > 0:
            self.dizziness_timer = max(0.0, self.dizziness_timer - dt)

        # Regeneração gradual de vida & vigor
        if self.regen_timer > 0:
            self.regen_timer = max(0.0, self.regen_timer - dt)
            self.timer_regen_tick += dt
            if self.timer_regen_tick >= 1.5:
                self.timer_regen_tick -= 1.5
                combat = getattr(self.entity, "combat", None)
                if combat and combat.hp < combat.hp_max:
                    combat.heal(2)
                    mapa = getattr(self.entity, "mapa", None)
                    if mapa and hasattr(mapa, "criar_texto_dano"):
                        mapa.criar_texto_dano(self.entity.x, self.entity.y - 0.7, "+2 HP", (90, 240, 140))

        rate_modifier = 0.5 if getattr(self.entity, "near_campfire", False) else 1.0
        self.timer_fome += dt * rate_modifier
        if self.timer_fome >= 5.0:
            self.timer_fome -= 5.0
            if self.fome > 0:
                self.fome -= 1
            else:
                self.entity.tomar_dano(1) # Dano de fome

        # --- LÓGICA DE SEDE (Desce mais rápido que fome, ex: 3s) ---
        self.timer_sede += dt * rate_modifier
        if self.timer_sede >= 3.0:
            self.timer_sede -= 3.0

        # --- LÓGICA DE SANGRAMENTO (Dano intermitente) ---
        if self.sangramento > 0:
            self.timer_sangramento += dt
            if self.timer_sangramento >= 2.0:
                self.timer_sangramento -= 2.0
                logger.debug("Applying bleeding damage to %s", self.entity.nome)
                self.entity.tomar_dano(2)
                self.sangramento -= 1
