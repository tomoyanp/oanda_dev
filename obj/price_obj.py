# coding: utf-8

class PriceObj:
    def __init__(self, instrument, price_time, asking_price, selling_price):
        self.instrument = instrument
        self.price_time = price_time
        self.asking_price = asking_price
        self.selling_price = selling_price


    def getInstrument(self):
        return self.instrument

    def getPriceTime(self):
        return self.price_time

    def getAskingPrice(self):
        return self.asking_price

    def getSellingPrice(self):
        return self.selling_price
