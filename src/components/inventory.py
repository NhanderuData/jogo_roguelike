class InventoryComponent:
    def __init__(self, capacity=10):
        self.capacity = capacity
        self.items = [] # Lista de dicionários ou objetos Item
        self.gold = 0

    def add_item(self, item_name, quantity=1):
        if len(self.items) < self.capacity:
            self.items.append({"name": item_name, "qtd": quantity})
            print(f"Item adicionado: {item_name}")
            return True
        print("Inventário cheio!")
        return False

    def remove_item(self, index):
        if 0 <= index < len(self.items):
            return self.items.pop(index)
        return None