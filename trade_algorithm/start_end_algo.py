# coding: utf-8

class StartEndAlgo:
    def __init__(self, threshold, stl_threshold):
        self.ask_price_list = []
        self.bid_price_list = []
        self.threshold = threshold
        self.stl_threshold = threshold
        self.order_flag = False
        self.order_price = 0
        self.order_kind = ""

    def setPriceList(self, price_obj):

        if len(self.ask_price_list) == 60:
            self.ask_price_list.pop(0)
            self.bid_price_list.pop(0)

        self.ask_price_list.append(price_obj.getAskingPrice())
        self.bid_price_list.append(price_obj.getSellingPrice())

    def setOrderPrice(self, order_price):
        self.order_price = order_price

    def getOrderFlag(self):
        return self.order_flag

    def getAskingPriceList(self):
        return self.ask_price_list

    def getBidPriceList(self):
        return self.bid_price_list

    def getOrderKind(self):
        return self.order_kind

    def decideTrade(self):
        # trade_flag is pass or ask or bid
        if len(self.ask_price_list) != 60:
            trade_flag = "pass"
        else:
            ask_diff = self.ask_price_list[59] - self.ask_price_list[0]
            bid_diff = self.bid_price_list[0] - self.bid_price_list[59]
            if ask_diff > threshold:
                trade_flag = "ask"
                self.order_kind = trade_flag
                self.order_flag = True
            elif bid_diff > threshold:
                trade_flag = "bid"
                self.order_flag = True
                self.order_kind = trade_flag
            else:
                trade_flag = "pass"

        return trade_flag

    def decideStl(self):
        stl_flag = False
        current_bid_price = self.bid_price_list[59]
        current_ask_price = self.ask_price_list[59]

        # 買いか売りかで比較する価格の切り替え
        if self.order_kind == "ask":
            if self.order_price < current_ask_price:
                if current_ask_price - self.order_price > self.stl_threshold:
                    stl_flag = True
            else:
                if self.order_price - current_ask_price > self.stl_threshold:
                    stl_flag = True
        else:
            if self.order_price < current_bid_price:
                if current_bid_price - self.order_price > self.stl_threshold:
                    stl_flag = True
            else:
                if self.order_price - current_bid_price > self.stl_threshold:
                    stl_flag = True

        return stl_flag
