# coding: utf-8

from datetime import datetime

class TradeAlgo:
    def __init__(self, trade_threshold, optional_threshold):
        self.ask_price_list = []
        self.bid_price_list = []
        self.trade_threshold = trade_threshold
        self.optional_threshold = optional_threshold
        self.order_price = 0

        self.order_flag = False
        self.order_kind = ""
#        self.price_list_size = price_list_size
        self.start_follow_time = 000000
        self.end_follow_time = 235959
        # 前日が陽線引けかどうかのフラグ
#        self.before_flag = before_flag

    def setResponse(self, response):
        for line in response:
            self.ask_price_list.append(line[0])
            self.bid_price_list.append(line[1])

    def getOrderFlag(self):
        return self.order_flag

    def setOrderPrice(self, price):
        self.order_price = price

    def getAskingPriceList(self):
        return self.ask_price_list

    def getBidPriceList(self):
        return self.bid_price_list

    def getOrderKind(self):
        return self.order_kind

    def decideTrade(self):
        try:
            # trade_flag is pass or ask or bid
            now = datetime.now()
            now = now.strftime("%H%M%S")
            now = int(now)
            list_max = len(self.ask_price_list) - 1
            ask_diff = self.ask_price_list[list_max] - self.ask_price_list[0]
            bid_diff = self.bid_price_list[0] - self.bid_price_list[list_max]

            # 15:00 ~ 235959の間は順張りとしてフラグに当てる
#            if ask_diff > self.trade_threshold and self.before_flag == "buy":
            if ask_diff > self.trade_threshold:
                trade_flag = "buy"
                self.order_kind = trade_flag
#            self.order_flag = True
#            elif bid_diff > self.trade_threshold and self.before_flag == "bid":
            elif bid_diff > self.trade_threshold:
                trade_flag = "sell"
                self.order_kind = trade_flag
#            self.order_flag = True
            else:
                trade_flag = "pass"

            return trade_flag

        except:
            raise

    # 損切り、利確はオーダー時に出している
    # ここでは、急に逆方向に動いた時に決済出来るようにしている
    def decideStl(self):
        try:
            list_max = len(self.ask_price_list) - 1
            ask_diff = self.ask_price_list[list_max] - self.ask_price_list[0]
            bid_diff = self.bid_price_list[0] - self.bid_price_list[list_max]

            stl_flag = False
            if self.order_kind == "buy":
                if bid_diff > self.trade_threshold:
                    stl_flag = True
 
            elif self.order_kind == "sell":
                if ask_diff > self.optional_threshold:
                    stl_flag = True

            return stl_flag
        except:
            raise

'''
    def decideStl(self):
        stl_flag = False
        list_max = len(self.ask_price_list) - 1
        current_bid_price = self.bid_price_list[list_max]
        current_ask_price = self.ask_price_list[list_max]

        # 買いか売りかで比較する価格の切り替え
        if self.order_kind == "sell":
            if self.order_price < current_ask_price:
                if current_ask_price - self.order_price > self.stop_threshold:
                    stl_flag = True
                    self.order_flag = False
            else:
                if self.order_price - current_ask_price > self.stl_threshold:
                    stl_flag = True
                    self.order_flag = False
        else:
            if self.order_price < current_bid_price:
                if current_bid_price - self.order_price > self.stl_threshold:
                    stl_flag = True
                    self.order_flag = False
            else:
                if self.order_price - current_bid_price > self.stop_threshold:
                    stl_flag = True
                    self.order_flag = False

        return stl_flag
'''
