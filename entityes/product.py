class Product:
    def __init__(self, id: int | None = None, name: str | None = None, cost: int | None = None, amount: int | None = None):
        self.id = id
        self.name = name
        self.cost = cost
        self.amount = amount