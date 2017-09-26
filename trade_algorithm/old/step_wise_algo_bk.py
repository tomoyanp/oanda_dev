# coding: utf-8

####################################################
#
# 陽線 or 陰線が連続して発生しているかを検知するよう作成
# 価格の配列を、何分割かにして、陽線引け、陰線引けの判定をする
#
####################################################

from datetime import datetime
import logging
import os
from common import instrument_init, account_init


current_path = os.path.abspath(os.path.dirname(__file__))

class StepWiseAlgo:
    def __init__(self, trade_threshold, optional_threshold, instrument, base_path):
        self.ask_price_list = []
        self.bid_price_list = []
        self.insert_time_list = []
        self.trade_threshold = trade_threshold
        self.optional_threshold = optional_threshold
        self.order_price = 0
        self.stl_price = 0
        self.stoploss = 0
        self.takeprofit = 0
        now = datetime.now()
        filename = now.strftime("%Y%m%d%H%M%S")
#        self.tradelog_file = open("%s/trade_%s.log" %(current_path, filename), "w")
#        self.stllog_file = open("%s/settlement_%s.log" %(current_path, filename), "w")
        self.order_flag = False
        self.trade_id = 0
        self.order_kind = ""
#        self.price_list_size = price_list_size
        self.start_follow_time = 000000
        self.end_follow_time = 235959
        # 前日が陽線引けかどうかのフラグ
#        self.before_flag = before_flag
        self.base_path = base_path
        self.instrument = instrument
        config_data = instrument_init(self.instrument, self.base_path)
        self.step_wise_unit = config_data["step_wise_unit"]
        self.step_wise_coefficient_threshold = config_data["step_wise_coefficient_threshold"]

################################################
# listは、要素数が大きいほうが古い。
# 小さいほうが新しい
###############################################

    def resetFlag(self):
        self.order_flag = False
        self.order_kind = ""
        self.trade_id = 0

    def setResponse(self, response):
        if len(response) < 1:
            pass
        else:
            self.ask_price_list = []
            self.bid_price_list = []
            self.insert_time_list = []
            for line in response:
                self.ask_price_list.append(line[0])
                self.bid_price_list.append(line[1])
                self.insert_time_list.append(line[2])

    def setTradeId(self, response):
        print response
        self.trade_id = response["tradeOpened"]["id"]
        print self.trade_id

    def getTradeId(self):
        return self.trade_id

    def getOrderFlag(self):
        return self.order_flag

    def setOrderFlag(self, flag):
        self.order_flag = flag

    def setOrderPrice(self, price):
        self.order_price = price


    def getOrderPrice(self):
        return self.order_price

    def setStlPrice(self, price):
        self.stl_price = price

    def getAskingPriceList(self):
        return self.ask_price_list

    def getCurrentPrice(self):
        return self.ask_price_list[len(self.ask_price_list)-1]

    def getCurrentTime(self):
        return self.insert_time_list[len(self.insert_time_list)-1]

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

        if take_profit == 0:
            threshold_list["takeprofit"] = 0

        if stop_loss == 0:
            threshold_list["stoploss"] = 0

        self.stoploss = threshold_list["stoploss"]
        self.takeprofit = threshold_list["takeprofit"]

        return threshold_list

    def decideTrade(self):
        try:
            # trade_flag is pass or ask or bid
            now = datetime.now()
            now = now.strftime("%H%M%S")
            now = int(now)
            list_size = len(self.ask_price_list)-1
            # ローソクを何本判断に使うか => step_wise_unit
            # 180秒を1分足3本にバラす場合、 step_wise_index = 180/3 == 60
            step_wise_index = list_size / self.step_wise_unit
            step_wise_threshold = self.trade_threshold / self.step_wise_unit

            # buy_indexが2/3で以上の場合にトレードするよう計算するとする
            # buy_index / step_wise_unit == 0.66666以上になればOKという理解
            # step_wise_coefficient_threshold
            # buyindexの割合と、比較する閾値
            buy_index = 0
            sell_index = 0
            for i in range(0, self.step_wise_unit):
                # 0, 60, 120になるはず
                ask_start = self.ask_price_list[step_wise_index*i]
                # 60, 120, 180になるはず
                ask_end   = self.ask_price_list[step_wise_index*(i+1)]

                if ask_end - ask_start > step_wise_threshold:
                    buy_index = buy_index + 1

                elif ask_start - ask_end > step_wise_threshold:
                    sell_index = sell_index + 1

            total_ask_start = self.ask_price_list[0]
            total_ask_end = self.ask_price_list[len(self.ask_price_list)-1]

            total_ask_difference = total_ask_end - total_ask_start
            total_bid_diffrence = total_ask_start - total_ask_end
            buy_index_ratio = buy_index / self.step_wise_unit
            sell_index_ratio = sell_index / self.step_wise_unit

            trade_flag = "pass"
            self.order_flag = False

            if total_ask_difference > self.trade_threshold:
                if buy_index_ratio > step_wise_coefficient_threshold:
                    trade_flag = "buy"
                    self.order_kind = trade_flag
                    self.order_flag = True
            elif total_bid_diffrence > self.trade_threshold:
                if sell_index / self.step_wise_unit > step_wise_coefficient_threshold:
                    trade_flag = "sell"
                    self.order_kind = trade_flag
                    self.order_flag = True

            return trade_flag

        except:
            raise


    # 高値と安値でトレードする
    def decideHiLowTrade(self):
        try:
            # trade_flag is pass or ask or bid
            now = datetime.now()
            now = now.strftime("%H%M%S")
            now = int(now)
            ask_mx = max(self.ask_price_list)
            ask_min = min(self.ask_price_list)
            ask_mx_index = self.ask_price_list.index(ask_mx)
            ask_min_index = self.ask_price_list.index(ask_min)

            bid_mx = max(self.bid_price_list)
            bid_min = min(self.bid_price_list)
            bid_mx_index = self.bid_price_list.index(bid_mx)
            bid_min_index = self.bid_price_list.index(bid_min)

            self.order_flag = False

            if (ask_mx - ask_min) > self.trade_threshold and ask_mx_index > ask_min_index:
                trade_flag = "buy"
                self.order_kind = trade_flag
                self.order_flag = True

            elif (bid_mx - bid_min) > self.trade_threshold and bid_mx_index < bid_min_index:
                trade_flag = "sell"
                self.order_kind = trade_flag
                self.order_flag = True
            else:
                trade_flag = "pass"
                self.order_flag = False

            return trade_flag

        except:
            raise

    # 損切り、利確はオーダー時に出している
    # ここでは、急に逆方向に動いた時に決済出来るようにしている
    def decideStl(self):
        print "********** Decide Stl **********"
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
            #self.stllog_file.write("====================================================================\n")
            #self.stllog_file.write("INFO:%s\n" % now)
            #self.stllog_file.write("INFO:DECIDE SETTLEMENT\n")
            #self.stllog_file.write("INFO:ask_max=%s, index=%s, insert_time=%s\n" %(ask_mx, ask_mx_index, self.insert_time_list[ask_mx_index]))
            #self.stllog_file.write("INFO:ask_min=%s, index=%s, insert_time=%s\n" %(ask_min, ask_min_index, self.insert_time_list[ask_min_index]))

            stl_flag = False
            if self.order_kind == "buy":
                #if bid_diff > self.trade_threshold:
                if (bid_mx - bid_min) > self.optional_threshold and bid_mx_index < bid_min_index:
                    #self.stllog_file.write("====================================================================\n")
                    #self.stllog_file.write("EMERGENCY:DECIDE SETTLEMENT\n")
                    #self.stllog_file.write("EMERGENCY:STL FLAG=BID\n")
                    self.order_flag = False
                    stl_flag = True

            elif self.order_kind == "sell":
                #if ask_diff > self.optional_threshold:
                if (ask_mx - ask_min) > self.optional_threshold and ask_mx_index > ask_min_index:
                    #self.stllog_file.write("====================================================================\n")
                    #self.stllog_file.write("EMERGENCY:DECIDE SETTLEMENT\n")
                    #self.stllog_file.write("EMERGENCY:STL FLAG=BUY\n")
                    self.order_flag = False
                    stl_flag = True

            return stl_flag
        except:
            raise


    def decideReverceStl(self):
        print "********** Decide Stl **********"
        try:
            ask_price = self.ask_price_list[len(self.ask_price_list)-1]
            bid_price = self.bid_price_list[len(self.bid_price_list)-1]

            stl_flag = False
            if self.order_kind == "buy":
                if bid_price > self.takeprofit or bid_price < self.stoploss:
                    self.order_flag = False
                    stl_flag = True

            elif self.order_kind == "sell":
                if ask_price < self.takeprofit or ask_price > self.stoploss:
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
