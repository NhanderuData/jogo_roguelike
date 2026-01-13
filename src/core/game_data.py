# Dicionário que define todos os status das entidades
# Se precisar balancear o jogo, é só mexer aqui!

DATA_INIMIGOS = {
    "Heroi": {
        "hp": 100, "dano": 10, "xp": 0, "speed": 0.15,
        "sprite": "llama_run", "ai": False, "layer_topo": False
    },
    "Orc": {
        "hp": 30, "dano": 5, "xp": 15, "speed": 0.04,
        "sprite": "orc_run", "ai": True, "layer_topo": False
    },
    "Troll": {
        "hp": 80, "dano": 15, "xp": 50, "speed": 0.03,
        "sprite": "troll_run", "ai": True, "layer_topo": False
    },
    "REI TROLL": {
        "hp": 150, "dano": 20, "xp": 100, "speed": 0.05,
        "sprite": "boss_run", "ai": True, "layer_topo": False
    },
    # Objetos Estáticos (Árvores, Pedras)
    "Arvore": {
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