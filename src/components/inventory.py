# src/components/inventory.py
import logging

from core.content import ContentCatalog

logger = logging.getLogger(__name__)

class InventoryComponent:
    def __init__(self, content: ContentCatalog, capacity=10):
        self.content = content
        self.capacity = capacity
        self.items = [] 
        self.ammo = {"9mm": 0, "shell": 0}

    @property
    def municao(self):
        return sum(self.ammo.values())

    def ammo_count(self, ammo_type):
        return self.ammo.get(ammo_type or "", 0)

    def consume_ammo(self, ammo_type, quantity):
        available = self.ammo_count(ammo_type)
        consumed = min(available, max(0, quantity))
        self.ammo[ammo_type] = available - consumed
        return consumed

    def add_item(self, item_name, quantity=1):
        data = self.content.items.get(item_name)
        if not data:
            return False
        if data.kind == "municao":
            ammo_type = data.ammo_type or "9mm"
            self.ammo[ammo_type] = self.ammo.get(ammo_type, 0) + data.value * quantity
            return True

        for item in self.items:
            if item["name"] == item_name:
                item["qtd"] += quantity
                return True

        if len(self.items) < self.capacity:
            self.items.append({"name": item_name, "qtd": quantity})
            return True
        return False

    def usar_item(self, index, entity):
        if 0 <= index < len(self.items):
            item_struct = self.items[index]
            nome = item_struct["name"]
            data = self.content.items.get(nome)
            
            if not data: return False
            usou = False
            
            # Verifica se a entidade tem o componente de status para itens de sobrevivência
            tem_status = hasattr(entity, 'status') and entity.status is not None

            # --- TIPO: COMIDA ---
            if data.kind == "comida" and tem_status:
                if entity.status.fome < entity.status.max_fome:
                    entity.status.comer(data.value)
                    logger.info("Consumed food item %s", nome)
                    usou = True

            # --- TIPO: BEBIDA (Novo) ---
            elif data.kind == "bebida" and tem_status:
                if entity.status.sede < entity.status.max_sede:
                    entity.status.beber(data.value)
                    logger.info("Consumed drink item %s", nome)
                    usou = True

            # --- TIPO: CURA / CURA_STATUS ---
            elif data.kind in ("cura", "cura_status"):
                precisa_hp = entity.combat.hp < entity.combat.hp_max
                precisa_estancar = tem_status and entity.status.sangramento > 0
                
                if precisa_hp or precisa_estancar:
                    if precisa_hp: 
                        entity.combat.heal(data.value)
                    
                    if precisa_estancar and data.effect == "estancar":
                        entity.status.curar_sangramento()
                        
                    usou = True

            elif data.kind == "energia" and tem_status:
                entity.status.energize(data.duration)
                entity.status.beber(data.value)
                usou = True

            elif data.kind == "armadura":
                entity.combat.add_armor(data.value)
                usou = True

            elif data.kind == "arma" and entity.weapons:
                usou = entity.weapons.unlock(data.weapon_id)
            
            if usou:
                item_struct["qtd"] -= 1
                if item_struct["qtd"] <= 0:
                    self.items.pop(index)
                return True
        return False
