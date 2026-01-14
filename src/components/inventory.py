# src/components/inventory.py
from core.game_data import DATA_ITEMS

class InventoryComponent:
    def __init__(self, capacity=10):
        self.capacity = capacity
        self.items = [] # Lista de dicionários
        self.municao = 0 # Contador separado para facilitar shooters

    def add_item(self, item_name, quantity=1):
        # Lógica especial para munição (acumula direto)
        data = DATA_ITEMS.get(item_name, {})
        if data.get("tipo") == "municao":
            self.municao += data.get("valor", 10) * quantity
            print(f"Munição adicionada! Total: {self.municao}")
            return True

        if len(self.items) < self.capacity:
            self.items.append({"name": item_name, "qtd": quantity})
            print(f"Item adicionado: {item_name}")
            return True
        print("Inventário cheio!")
        return False

    def usar_item(self, index, entity):
        if 0 <= index < len(self.items):
            item_struct = self.items[index]
            nome = item_struct["name"]
            data = DATA_ITEMS.get(nome)
            
            if not data: return False
            
            usou = False
            # Efeito: CURA
            if data["tipo"] == "cura":
                if entity.combat.hp < entity.combat.hp_max:
                    cura = data["valor"]
                    entity.combat.heal(cura)
                    print(f"Usou {nome}. Curou {cura} HP.")
                    usou = True
                else:
                    print("Vida já está cheia.")
            
            # Se usou, remove do inventário
            if usou:
                self.items.pop(index)
                return True
        return False