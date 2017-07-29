# coding: utf-8

class StartEndAlgo:
    def __init__(self, threshold):
        self.ask_price_list = []
        self.bid_price_list = []
        self.threshold = threshold

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

    def decideTrade(self):
        # trade_flag is pass or ask or bid
        if len(self.ask_price_list) != 60:
            trade_flag = "pass"
        else:
            ask_diff = self.ask_price_list[60] - self.ask_price_list[0]
            bid_diff = self.bid_price_list[0] - self.bid_price_list[60]
            if ask_diff > threshold:
                trade_flag = "ask"
            elif bid_diff > threshold:
                trade_flag = "bid"
            else:
                trade_flag = "pass"

        return trade_flag
