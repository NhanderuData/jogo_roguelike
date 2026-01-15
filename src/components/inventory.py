# src/components/inventory.py
from core.game_data import DATA_ITEMS

class InventoryComponent:
    def __init__(self, capacity=10):
        self.capacity = capacity
        self.items = [] 
        self.municao = 0 

    def add_item(self, item_name, quantity=1):
        data = DATA_ITEMS.get(item_name, {})
        if data.get("tipo") == "municao":
            self.municao += data.get("valor", 10) * quantity
            return True

        if len(self.items) < self.capacity:
            self.items.append({"name": item_name, "qtd": quantity})
            return True
        return False

    def usar_item(self, index, entity):
        if 0 <= index < len(self.items):
            item_struct = self.items[index]
            nome = item_struct["name"]
            data = DATA_ITEMS.get(nome)
            
            if not data: return False
            
            usou = False
            
            # --- TIPO: CURA ---
            if data["tipo"] == "cura":
                if entity.combat.hp < entity.combat.hp_max:
                    entity.combat.heal(data["valor"])
                    print(f"Usou {nome}. Curou HP.")
                    usou = True
                else:
                    print("Vida cheia!")

            # --- TIPO: COMIDA (Novo) ---
            elif data["tipo"] == "comida":
                # Come se tiver fome OU se tiver vida para recuperar (cura extra)
                precisa_fome = entity.combat.fome < entity.combat.max_fome
                precisa_vida = entity.combat.hp < entity.combat.hp_max
                
                if precisa_fome or precisa_vida:
                    entity.combat.comer(data["valor"])
                    
                    # Se a comida também cura (ex: Enlatado +5hp)
                    if "cura_extra" in data:
                        entity.combat.heal(data["cura_extra"])
                        
                    print(f"Comeu {nome}. Fome restaurada.")
                    usou = True
                else:
                    print("Sem fome e vida cheia!")
            
            if usou:
                self.items.pop(index)
                return True
        return False