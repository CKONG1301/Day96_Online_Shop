class BuyItem:
    def __init__(self):
        # self.title = ''
        # self.price = 0
        # self.img = ''
        self.product = 0
        self.qty = 0
        
        
class Cart:
    def __init__(self):
        super().__init__()
        self.items = []

    def add_item(self, product, qty):
        new_item = BuyItem()
        new_item.product = product
        # new_item.title = item.title
        # new_item.price = item.price
        # new_item.img = item.img
        new_item.qty = qty
        self.items.append(new_item)
        
        