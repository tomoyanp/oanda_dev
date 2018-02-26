# coding: utf-8

####################################################
#
# 雛形のクラス
#
####################################################

from datetime import datetime,timedelta
import numpy as np
import logging
import os
from common import instrument_init, account_init, decideMarket, getBollingerDataSet, extraBollingerDataSet, getEWMA, countIndex, getSlope, getOriginalEWMA
from abc import ABCMeta, abstractmethod
from mysql_connector import MysqlConnector

class SuperAlgo(object):

    def __init__(self, instrument, base_path, config_name, base_time):
        self.base_path = base_path
        self.instrument = instrument
        self.config_data = instrument_init(self.instrument, self.base_path, config_name)
        self.ask_price_list = []
        self.bid_price_list = []
        self.insert_time_list = []
        self.order_price = 0
        self.stl_price = 0
        self.stoploss_rate = 0
        self.takeprofit_rate = 0
        now = datetime.now()
        filename = now.strftime("%Y%m%d%H%M%S")
        self.order_flag = False
        self.trade_id = 0
        self.order_kind = ""

        self.mysqlConnector = MysqlConnector()

        self.profit_history = "i" # initial
        self.order_history  = "i" # initial

        self.start_time = base_time - timedelta(seconds=self.config_data["time_width"])
        self.end_time = base_time
        self.base_time = base_time

        self.trail_flag = False
        self.trail_second_flag = False
        self.break_wait_flag = "pass"
        self.setInitialPrice(self.base_time)
        self.setInitialIndicator(self.base_time)

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
        self.break_wait_flag = "pass"

    def setInitialPrice(self, base_time):
        sql = self.getInitialSql(base_time)
        response = self.mysqlConnector.select_sql(sql)
        self.setResponse(response)

    def addPrice(self, base_time):
        cmp_end_time = self.end_time.strftime("%Y-%m-%d %H:%M:%S")
        cmp_base_time = base_time.strftime("%Y-%m-%d %H:%M:%S")
        if cmp_end_time == cmp_base_time:
            pass
        else:
            self.start_time = self.end_time
            self.end_time = base_time
            sql = self.getAddSql()
            print(sql)
            response = self.mysqlConnector.select_sql(sql)
            self.addResponse(response)

    def getAddSql(self):
        start_time = self.start_time.strftime("%Y-%m-%d %H:%M:%S")
        end_time = self.end_time.strftime("%Y-%m-%d %H:%M:%S")
        sql = "select ask_price, bid_price, insert_time from %s_TABLE where insert_time >= \'%s\' and insert_time < \'%s\' ORDER BY insert_time ASC" % (self.instrument, start_time, end_time)

        return sql


    def getInitialSql(self, base_time):
        time_width = self.config_data["time_width"]

        end_time = base_time.strftime("%Y-%m-%d %H:%M:%S")

        sql = "select ask_price, bid_price, insert_time from %s_TABLE where insert_time < \'%s\' ORDER BY insert_time DESC limit %s" % (self.instrument, end_time, time_width)
        logging.info("sql=%s" % sql)
        return sql

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

            self.ask_price_list.reverse()
            self.bid_price_list.reverse()
            self.insert_time_list.reverse()

            logging.info("start_insert_time = %s, ask_price = %s, bid_price = %s" % (self.insert_time_list[0], self.ask_price_list[0], self.bid_price_list[0]))
            logging.info("end_insert_time = %s, ask_price = %s, bid_price = %s" % (self.insert_time_list[-1], self.ask_price_list[-1], self.bid_price_list[-1]))

    def addResponse(self, response):
        response_length = len(response)
        if response_length < 0:
            pass
        else:
            for i in range(0, response_length):
                self.ask_price_list.pop(0)
                self.bid_price_list.pop(0)
                self.insert_time_list.pop(0)

            for res in response:
                self.ask_price_list.append(res[0])
                self.bid_price_list.append(res[1])
                self.insert_time_list.append(res[2])

    def setOrderData(self, trade_flag, order_price, order_flag, trade_id):
        self.order_kind = trade_flag
        self.order_price = order_price
        self.order_flag = order_flag
        self.trade_id = trade_id

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

    def getCurrentPrice(self):
        price = (self.ask_price_list[-1] + self.bid_price_list[-1]) / 2
        return price

    def getCurrentTime(self):
        return self.insert_time_list[len(self.insert_time_list)-1]

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

        self.stoploss_rate = threshold_list["stoploss"]
        self.takeprofit_rate = threshold_list["takeprofit"]

        return threshold_list


    # testmodeでstoploss, takdeprofitに引っかかった場合
    def decideReverceStl(self):
        try:
            ask_price = self.ask_price_list[len(self.ask_price_list)-1]
            bid_price = self.bid_price_list[len(self.bid_price_list)-1]
            self.takeprofit_rate = float(self.takeprofit_rate)
            self.stoploss_rate = float(self.stoploss_rate)
            ask_price = float(ask_price)
            bid_price = float(bid_price)

            stl_flag = False
            if self.order_kind == "buy":
                if bid_price > self.takeprofit_rate or bid_price < self.stoploss_rate:
                    stl_flag = True

            elif self.order_kind == "sell":
                if ask_price < self.takeprofit_rate or ask_price > self.stoploss_rate:

                    stl_flag = True

            return stl_flag
        except:
            raise


    def calcProfit(self):
        stl_price = self.getCurrentPrice()
        self.setStlPrice(stl_price)
        if self.order_kind == "buy":
            profit = stl_price - self.order_price
        else:
            profit = self.order_price - stl_price

        if profit > 0:
            self.profit_history = "v"
            sleep_time = self.config_data["stl_sleep_vtime"]
        else:
            self.profit_history = "l"
            sleep_time = self.config_data["stl_sleep_ltime"]

        self.order_histroy = self.order_kind

        return profit, sleep_time

    def setDataSet(self, ask_price_list, bid_price_list, insert_time_list):
        self.ask_price_list = ask_price_list
        self.bid_price_list = bid_price_list
        self.insert_time_list = insert_time_list


    @abstractmethod
    def setInitialIndicator(self, base_time):
        pass

    @abstractmethod
    def setIndicator(self, base_time):
        pass

    @abstractmethod
    def decideTrade(self):
        pass

    # takeprofit, stoplossではなく、明示的な決済
    @abstractmethod
    def decideStl(self):
        pass
