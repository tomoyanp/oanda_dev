# coding: utf-8

class StartEndAlgo:
    def __init__(self):
        self.ask_price_list = []
        self.bid_price_list = []

    def setPriceList(self, price_obj):

        if len(self.ask_price_list) == 60:
            self.ask_price_list.pop(0)
            self.bid_price_list.pop(0)

        self.ask_price_list.append(price_obj.getAskingPrice())
        self.bid_price_list.append(price_obj.getSellingPrice())

    def getAskingPriceList(self):
        return self.ask_price_list

    def getBidPriceList(self):
        return self.bid_price_list
