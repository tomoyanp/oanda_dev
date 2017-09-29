# coding: utf-8

####################################################
#
# 雛形のクラス
#
####################################################

from datetime import datetime
import logging
import os
from common import instrument_init, account_init
from abc import ABCMeta, abstractmethod

#class SuperAlgo(metaclass=ABCMeta):
class SuperAlgo(object):

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
        self.order_flag = False
        self.trade_id = 0
        self.order_kind = ""
#        self.start_follow_time = 000000
#        self.end_follow_time = 235959
        # 前日が陽線引けかどうかのフラグ
#        self.before_flag = before_flag

        self.base_path = base_path
        self.instrument = instrument

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

    def getStlPrice(self):
        return self.stl_price

    def getCurrentPrice(self):
        return self.ask_price_list[len(self.ask_price_list)-1]

    def getCurrentTime(self):
        return self.insert_time_list[len(self.insert_time_list)-1]

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

    # testmodeでstoploss, takdeprofitに引っかかった場合
    def decideReverceStl(self):
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

    @abstractmethod
    def decideTrade(self):
        pass

    # takeprofit, stoplossではなく、明示的な決済
    @abstractmethod
    def decideStl(self):
        pass
