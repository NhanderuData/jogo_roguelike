# src/core/game_data.py

# --- TABELA DE ITENS (NOVA) ---
# Define o que cada item faz, sua cor e valor
DATA_ITEMS = {
    "Medkit": {
        "tipo": "cura", 
        "valor": 50, 
        "cor": (255, 255, 255), # Branco
        "sprite": "shoot" # Placeholder
    },
    "Enlatado": {
        "tipo": "comida", 
        "valor": 15, 
        "cor": (200, 100, 50), # Marrom/Laranja
        "sprite": "rock"
    },
    "Munição 9mm": {
        "tipo": "municao", 
        "valor": 10, 
        "cor": (255, 255, 0), # Amarelo
        "sprite": "shoot"
    },
    "Bandagem": {
        "tipo": "cura", 
        "valor": 25, 
        "cor": (200, 200, 200), # Cinza Claro
        "sprite": "paper" # Placeholder (usará quadrado se não existir)
    }
}

# --- TABELA DE INIMIGOS (ZUMBIFICADA) ---
DATA_INIMIGOS = {
    "Survivor": { # O Jogador
        "hp": 100, "dano": 5, "xp": 0, "speed": 0.12,
        "sprite": "llama_run", "ai": False, "layer_topo": False
    },
    "Walker": { # Zumbi Comum (Lento)
        "hp": 40, "dano": 10, "xp": 10, "speed": 0.03,
        "sprite": "orc_run", "ai": True, "layer_topo": False,
        "loot": ["Enlatado", "Bandagem"], 
        "chance_loot": 1.0 # 30% de chance de dropar
    },
    "Runner": { # Zumbi Rápido
        "hp": 25, "dano": 8, "xp": 20, "speed": 0.09,
        "sprite": "troll_run", "ai": True, "layer_topo": False,
        "loot": ["Munição 9mm"], 
        "chance_loot": 1.0
    },
    "Tank": { # Zumbi Forte (Chefe)
        "hp": 150, "dano": 25, "xp": 100, "speed": 0.04,
        "sprite": "boss_run", "ai": True, "layer_topo": False,
        "loot": ["Medkit", "Munição 9mm"], 
        "chance_loot": 1.0
    },
    # Objetos Estáticos
    "Carro Quebrado": { # Antiga Rocha
        "hp": 200, "dano": 0, "xp": 0, "speed": 0,
        "sprite": "rock", "ai": False, "layer_topo": False
    },
    "Arvore": { # Mantido para compatibilidade com mapa antigo se precisar
        "hp": 50, "dano": 0, "xp": 5, "speed": 0,
        "sprite": "tree", "ai": False, "layer_topo": True
    },
    "RedTree": {
        "hp": 60, "dano": 0, "xp": 5, "speed": 0,
        "sprite": "red_tree", "ai": False, "layer_topo": True
    },
    "Cipreste": {
        "hp": 40, "dano": 0, "xp": 5, "speed": 0,
        "sprite": "cipreste", "ai": False, "layer_topo": True
    }
}