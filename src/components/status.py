# src/components/status.py
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

    def add_sangramento(self, qtd):
        """ Adiciona 'tempo' de sangramento ou intensidade """
        self.sangramento += qtd
        print(f"{self.entity.nome} está sangrando!")

    def curar_sangramento(self):
        self.sangramento = 0
        print(f"{self.entity.nome} estancou o sangramento.")

    def comer(self, valor):
        self.fome += valor
        if self.fome > self.max_fome: self.fome = self.max_fome

    def beber(self, valor):
        self.sede += valor
        if self.sede > self.max_sede: self.sede = self.max_sede

    def update(self, dt):
        # --- LÓGICA DE FOME (A cada ~5 segundos) ---
        self.timer_fome += 1
        if self.timer_fome > 300: # 60 FPS * 5s
            self.timer_fome = 0
            if self.fome > 0:
                self.fome -= 1
            else:
                self.entity.tomar_dano(1) # Dano de fome

        # --- LÓGICA DE SEDE (Desce mais rápido que fome, ex: 3s) ---
        self.timer_sede += 1
        if self.timer_sede > 180:
            self.timer_sede = 0
            if self.sede > 0:
                self.sede -= 1
            else:
                self.entity.tomar_dano(1) # Dano de sede

        # --- LÓGICA DE SANGRAMENTO (Dano intermitente) ---
        if self.sangramento > 0:
            self.timer_sangramento += 1
            # A cada 2 segundos toma dano se estiver sangrando
            if self.timer_sangramento > 120: 
                self.timer_sangramento = 0
                print("Dano de sangramento!")
                self.entity.tomar_dano(2)
                self.sangramento -= 1 # O sangramento diminui sozinho lentamente ou fica fixo?
                # Se quiser que só pare com bandagem, remova a linha acima.