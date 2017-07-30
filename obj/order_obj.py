# coding: utf-8


class OrderObj:
    def __init__(self):
        pass

    def setOrderId(self, order_id):
        self.order_id = order_id

    def setPrice(self, price):
        self.price = price

    def getOrderId(self):
        return self.order_id

    def getPrice(self):
        return self.price
