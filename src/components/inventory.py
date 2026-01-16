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
            
            # Verifica se a entidade tem o componente de status para itens de sobrevivência
            tem_status = hasattr(entity, 'status') and entity.status is not None

            # --- TIPO: COMIDA ---
            if data["tipo"] == "comida" and tem_status:
                if entity.status.fome < entity.status.max_fome:
                    entity.status.comer(data["valor"])
                    print(f"Comeu {nome}.")
                    usou = True

            # --- TIPO: BEBIDA (Novo) ---
            elif data["tipo"] == "bebida" and tem_status:
                if entity.status.sede < entity.status.max_sede:
                    entity.status.beber(data["valor"])
                    print(f"Bebeu {nome}.")
                    usou = True

            # --- TIPO: CURA / CURA_STATUS ---
            elif data["tipo"] == "cura" or data["tipo"] == "cura_status":
                precisa_hp = entity.combat.hp < entity.combat.hp_max
                precisa_estancar = tem_status and entity.status.sangramento > 0
                
                if precisa_hp or precisa_estancar:
                    if precisa_hp: 
                        entity.combat.heal(data["valor"])
                    
                    if precisa_estancar and data.get("efeito") == "estancar":
                        entity.status.curar_sangramento()
                        
                    usou = True
            
            if usou:
                self.items.pop(index)
                return True
        return False