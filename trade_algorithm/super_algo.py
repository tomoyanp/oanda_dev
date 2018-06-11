# coding: utf-8

####################################################
#
# 雛形のクラス
#
####################################################

from datetime import datetime,timedelta
import numpy as np
from logging import getLogger, FileHandler, DEBUG
import os
from common import instrument_init, account_init, decideMarket, getBollingerDataSet, extraBollingerDataSet, getEWMA, countIndex, getSlope, getOriginalEWMA
from abc import ABCMeta, abstractmethod
from mysql_connector import MysqlConnector


class SuperAlgo(object):

    def __init__(self, instrument, base_path, config_name, base_time):
        self.base_path = base_path
        self.instrument = instrument
        self.config_data = instrument_init(self.instrument, self.base_path, config_name)
        self.ask_price = 0
        self.bid_price = 0
        self.insert_time = ""
        self.order_price = 0
        self.stl_price = 0
        self.stoploss_rate = 0
        self.takeprofit_rate = 0
        self.order_flag = False
        self.trade_id = 0
        self.order_kind = ""
        self.mysql_connector = MysqlConnector()
        self.trail_flag = False
        self.trail_second_flag = False
        self.trail_price = 0
        self.order_history = "pass"
        self.profit_history = "pass"
        self.count_threshold = 1

################################################
# listは、要素数が大きいほうが古い。
# 小さいほうが新しい
###############################################

    def resetFlag(self):
        self.order_flag = False
        self.order_kind = ""
        self.trade_id = 0
        self.trail_flag = False
        self.trail_second_flag = False
        self.trail_price = 0

    def setOrderData(self, trade_flag, order_price, order_flag, trade_id):
        self.order_kind = trade_flag
        self.order_price = order_price
        self.order_flag = order_flag
        self.trade_id = trade_id

    def setPrice(self, base_time):
        sql = "select ask_price, bid_price, insert_time from %s_TABLE where insert_time <= \'%s\' order by insert_time DESC limit 1" % (self.instrument, base_time)
        response = self.mysql_connector.select_sql(sql)
        self.ask_price = response[0][0]
        self.bid_price = response[0][1]
        self.insert_time = response[0][2]

    def getAskPrice(self):
        return self.ask_price

    def getBidPrice(self):
        return self.bid_price

    def setTradeId(self, trade_id):
        self.trade_id = trade_id

    def getTradeId(self):
        return self.trade_id

    def getOrderFlag(self):
        return self.order_flag

    def setOrderFlag(self, flag):
        self.order_flag = flag

    def setOrderKind(self, kind):
        self.order_kind = kind

    def setOrderPrice(self, price):
        self.order_price = price

    def getOrderPrice(self):
        return self.order_price

    def setStlPrice(self, price):
        self.stl_price = price

    def getStlPrice(self):
        return self.stl_price

    def getBidPrice(self):
        return self.bid_price


    def getAskPrice(self):
        return self.ask_price

    def getCurrentPrice(self):
        price = (self.ask_price + self.bid_price) / 2
        return price

    def getCurrentTime(self):
        return self.insert_time

    def getOrderKind(self):
        return self.order_kind

    def decideTradeTime(self, base_time, trade_flag):
        enable_time_mode = self.config_data["enable_time_mode"]
        if enable_time_mode == "on":
            enable_times = self.config_data["enable_time"]
            enable_flag = False
            cmp_time = base_time.strftime("%Y-%m-%d")

            for ent in enable_times:
                ent = "%s %s" % (cmp_time, ent)
                before_time = datetime.strptime(ent, "%Y-%m-%d %H:%M:%S")
                after_time = before_time + timedelta(hours=1)

                if base_time > before_time and base_time < after_time:
                    enable_flag = True
        else:
            enable_flag = True


        if enable_flag:
            pass
        else:
            trade_flag = "pass"


        return trade_flag

    def calcThreshold(self, trade_flag):
        stop_loss = self.config_data["stop_loss"]
        take_profit = self.config_data["take_profit"]
        threshold_list = {}
        if trade_flag == "buy":
            threshold_list["stoploss"] = self.ask_price - stop_loss
            threshold_list["takeprofit"] = self.ask_price + take_profit
        else:
            threshold_list["stoploss"] = self.bid_price + stop_loss
            threshold_list["takeprofit"] = self.bid_price - take_profit

        if take_profit == 0:
            threshold_list["takeprofit"] = 0

        if stop_loss == 0:
            threshold_list["stoploss"] = 0

        self.stoploss_rate = threshold_list["stoploss"]
        self.takeprofit_rate = threshold_list["takeprofit"]

        return threshold_list


    # testmodeでstoploss, takdeprofitに引っかかった場合
    def decideReverceStl(self):
        try:
            self.takeprofit_rate = float(self.takeprofit_rate)
            self.stoploss_rate = float(self.stoploss_rate)
            self.ask_price = float(self.ask_price)
            self.bid_price = float(self.bid_price)

            stl_flag = False
            if self.order_kind == "buy":
                if self.bid_price > self.takeprofit_rate or self.bid_price < self.stoploss_rate:
                    stl_flag = True

            elif self.order_kind == "sell":
                if self.ask_price < self.takeprofit_rate or self.ask_price > self.stoploss_rate:
                    stl_flag = True

            return stl_flag
        except:
            raise


    def calcProfit(self):
        if self.order_kind == "buy":
            stl_price = self.bid_price
            profit = stl_price - self.order_price
        else:
            stl_price = self.ask_price
            profit = self.order_price - stl_price

        if profit >= 0:
            self.profit_history = "v"
            sleep_time = self.config_data["stl_sleep_vtime"]
#            self.count_threshold = 0
            self.count_threshold = 1

        else:
            self.profit_history = "l"
            sleep_time = self.config_data["stl_sleep_ltime"]
#            if self.count_threshold >= 3:
            if self.count_threshold >= 1:
                pass
            else:
                self.count_threshold = self.count_threshold + 1

        self.order_history = self.order_kind
        self.setStlPrice(stl_price)

        return profit, sleep_time


    @abstractmethod
    def setIndicator(self, base_time):
        pass

    @abstractmethod
    def decideTrade(self, base_time):
        pass

    @abstractmethod
    def decideStl(self, base_time):
        pass
