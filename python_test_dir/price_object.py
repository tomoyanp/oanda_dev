#coding: utf-8

class PriceObject:
    def __init__(self):
        self.price_list = []

    def setPriceList(self, price_list):
        self.price_list = price_list

    def getPriceList(self):
        return self.price_list
