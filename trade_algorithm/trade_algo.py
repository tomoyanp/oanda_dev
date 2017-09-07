# coding: utf-8

from datetime import datetime
import os
current_path = os.path.abspath(os.path.dirname(__file__))

class TradeAlgo:
    def __init__(self, trade_threshold, optional_threshold):
        self.ask_price_list = []
        self.bid_price_list = []
        self.insert_time_list = []
        self.trade_threshold = trade_threshold
        self.optional_threshold = optional_threshold
        self.order_price = 0
        now = datetime.now()
        filename = now.strftime("%Y%m%d%H%M%S")
        self.tradelog_file = open("%s/trade_%s.log" %(current_path, filename), "w")
        self.stllog_file = open("%s/settlement_%s.log" %(current_path, filename), "w")
        self.order_flag = False
        self.order_kind = ""
#        self.price_list_size = price_list_size
        self.start_follow_time = 000000
        self.end_follow_time = 235959
        # 前日が陽線引けかどうかのフラグ
#        self.before_flag = before_flag

################################################
# listは、要素数が大きいほうが古い。
# 小さいほうが新しい
###############################################

    def setResponse(self, response):
        self.ask_price_list = []
        self.bid_price_list = []
        self.insert_time_list = []
        for line in response:
            self.ask_price_list.append(line[0])
            self.bid_price_list.append(line[1])
            self.insert_time_list.append(line[2])

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


    def calcThreshold(self, stop_loss, take_profit, trade_flag):
        list_max = len(self.ask_price_list) - 1
        threshold_list = {}
        if trade_flag == "buy":
            threshold_list["stoploss"] = self.ask_price_list[list_max] - stop_loss
            threshold_list["takeprofit"] = self.ask_price_list[list_max] + take_profit
        else:
            threshold_list["stoploss"] = self.bid_price_list[list_max] + stop_loss
            threshold_list["takeprofit"] = self.bid_price_list[list_max] - take_profit

        return threshold_list


    def decideTrade(self):
        try:
            # trade_flag is pass or ask or bid
            now = datetime.now()
            now = now.strftime("%H%M%S")
            now = int(now)
            #list_max = len(self.ask_price_list) - 1
            #ask_diff = self.ask_price_list[list_max] - self.ask_price_list[0]
            #bid_diff = self.bid_price_list[0] - self.bid_price_list[list_max]

            ask_mx = max(self.ask_price_list)
            ask_min = min(self.ask_price_list)
            ask_mx_index = self.ask_price_list.index(ask_mx)
            ask_min_index = self.ask_price_list.index(ask_min)

            bid_mx = max(self.bid_price_list)
            bid_min = min(self.bid_price_list)
            bid_mx_index = self.bid_price_list.index(bid_mx)
            bid_min_index = self.bid_price_list.index(bid_min)

            self.stllog_file.write("====================================================================\n")
            self.stllog_file.write("INFO:%s\n" % now)
            self.stllog_file.write("INFO:DECIDE TRADE\n")
            self.stllog_file.write("INFO:ask_max=%s, index=%s, insert_time=%s\n" %(ask_mx, ask_mx_index, self.insert_time_list[ask_mx_index]))
            self.stllog_file.write("INFO:ask_min=%s, index=%s, insert_time=%s\n" %(ask_min, ask_min_index, self.insert_time_list[ask_min_index]))

#            self.tradelog_file.write("====================================================================\n")
#            self.tradelog_file.write("INFO:DECIDE TRADE\n")
#            self.tradelog_file.write("INFO:TRADE FLAG=BID\n")
#            self.tradelog_file.write("INFO:bid_price_list[0]=%s, insert_time_list[0]=%s\n" %(self.bid_price_list[0], self.insert_time_list[0]))
#            self.tradelog_file.write("INFO:bid_price_list[list_max]=%s, insert_time_list[list_max]=%s\n" %(self.bid_price_list[list_max], self.insert_time_list[list_max]))
            # 15:00 ~ 235959の間は順張りとしてフラグに当てる
#            if ask_diff > self.trade_threshold and self.before_flag == "buy":
#            if ask_diff > self.trade_threshold:
            if (ask_mx - ask_min) > self.trade_threshold and ask_mx_index > ask_min_index:
                trade_flag = "buy"
                self.stllog_file.write("====================================================================\n")
                self.stllog_file.write("EMERGENCY:DECIDE TRADE\n")
                self.stllog_file.write("EMERGENCY:TRADE FLAG=BUY\n")
                self.order_kind = trade_flag
                self.order_flag = True
#            elif bid_diff > self.trade_threshold and self.before_flag == "bid":
#            elif bid_diff > self.trade_threshold:
            if (bid_mx - bid_min) > self.trade_threshold and bid_mx_index < bid_min_index:
                trade_flag = "sell"
                self.order_kind = trade_flag
                self.stllog_file.write("====================================================================\n")
                self.stllog_file.write("EMERGENCY:DECIDE TRADE\n")
                self.stllog_file.write("EMERGENCY:TRADE FLAG=BID\n")
                self.order_flag = True
            else:
                trade_flag = "pass"

            return trade_flag

        except:
            raise

    # 損切り、利確はオーダー時に出している
    # ここでは、急に逆方向に動いた時に決済出来るようにしている
    def decideStl(self):
        try:
            #list_max = len(self.ask_price_list) - 1
            #ask_diff = self.ask_price_list[list_max] - self.ask_price_list[0]
            #bid_diff = self.bid_price_list[0] - self.bid_price_list[list_max]

            ask_mx = max(self.ask_price_list)
            ask_min = min(self.ask_price_list)
            ask_mx_index = self.ask_price_list.index(ask_mx)
            ask_min_index = self.ask_price_list.index(ask_min)

            bid_mx = max(self.bid_price_list)
            bid_min = min(self.bid_price_list)
            bid_mx_index = self.bid_price_list.index(bid_mx)
            bid_min_index = self.bid_price_list.index(bid_min)

            now = datetime.now()
            now = now.strftime("%Y-%m-%d %H:%M:%S")
            self.stllog_file.write("====================================================================\n")
            self.stllog_file.write("INFO:%s\n" % now)
            self.stllog_file.write("INFO:DECIDE SETTLEMENT\n")
            self.stllog_file.write("INFO:ask_max=%s, index=%s, insert_time=%s\n" %(ask_mx, ask_mx_index, self.insert_time_list[ask_mx_index]))
            self.stllog_file.write("INFO:ask_min=%s, index=%s, insert_time=%s\n" %(ask_min, ask_min_index, self.insert_time_list[ask_min_index]))

            stl_flag = False
            if self.order_kind == "buy":
                #if bid_diff > self.trade_threshold:
                if (bid_mx - bid_min) > self.optional_threshold and bid_mx_index < bid_min_index:
                    self.stllog_file.write("====================================================================\n")
                    self.stllog_file.write("EMERGENCY:DECIDE SETTLEMENT\n")
                    self.stllog_file.write("EMERGENCY:STL FLAG=BID\n")
                    self.order_flag = False
                    stl_flag = True

            elif self.order_kind == "sell":
                #if ask_diff > self.optional_threshold:
                if (ask_mx - ask_min) > self.optional_threshold and ask_mx_index > ask_min_index:
                    self.stllog_file.write("====================================================================\n")
                    self.stllog_file.write("EMERGENCY:DECIDE SETTLEMENT\n")
                    self.stllog_file.write("EMERGENCY:STL FLAG=BUY\n")
                    self.order_flag = False
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
