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
        self.ask_price = 0
        self.bid_price = 0
        self.insert_time = ""
        self.order_price = 0
        self.stl_price = 0
        self.stoploss_rate = 0
        self.takeprofit_rate = 0
        now = datetime.now()
        filename = now.strftime("%Y%m%d%H%M%S")
        self.order_flag = False
        self.trade_id = 0
        self.order_kind = ""
        self.mysql_connector = MysqlConnector()
        self.trail_flag = False
        self.trail_second_flag = False
        self.trail_price = 0
        self.break_wait_flag = "pass"

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
        stl_price = self.getCurrentPrice()
        self.setStlPrice(stl_price)
        if self.order_kind == "buy":
            profit = stl_price - self.order_price
        else:
            profit = self.order_price - stl_price

        if profit >= 0:
            self.profit_history = "v"
            sleep_time = self.config_data["stl_sleep_vtime"]
        else:
            self.profit_history = "l"
            sleep_time = self.config_data["stl_sleep_ltime"]

        self.order_histroy = self.order_kind

        return profit, sleep_time


    def setBollinger1m1(self, base_time):
         # bollinger 1m 1sigma
        ind_type = "bollinger1m1"
        sql = "select upper_sigma, lower_sigma, base_line from INDICATOR_TABLE where instrument = \'%s\' and insert_time <= \'%s\' and type = \'%s\' order by insert_time DESC limit 1" % (self.instrument, base_time, ind_type)
        response = self.mysql_connector.select_sql(sql)
        self.upper_sigma_1m1 = response[0][0]
        self.lower_sigma_1m1 = response[0][1]
        self.base_line_1m1 = response[0][2]

    def setBollinger1m25(self, base_time):
         # bollinger 1m 2.5sigma
        ind_type = "bollinger1m2.5"
        sql = "select upper_sigma, lower_sigma, base_line from INDICATOR_TABLE where instrument = \'%s\' and insert_time <= \'%s\' and type = \'%s\' order by insert_time DESC limit 1" % (self.instrument, base_time, ind_type)
        response = self.mysql_connector.select_sql(sql)
        self.upper_sigma_1m25 = response[0][0]
        self.lower_sigma_1m25 = response[0][1]
        self.base_line_1m25 = response[0][2]

    def setBollinger1m3(self, base_time):
         # bollinger 1m 3sigma
        ind_type = "bollinger1m3"
        sql = "select upper_sigma, lower_sigma, base_line from INDICATOR_TABLE where instrument = \'%s\' and insert_time <= \'%s\' and type = \'%s\' order by insert_time DESC limit 1" % (self.instrument, base_time, ind_type)
        response = self.mysql_connector.select_sql(sql)
        self.upper_sigma_1m3 = response[0][0]
        self.lower_sigma_1m3 = response[0][1]
        self.base_line_1m3 = response[0][2]


    def setBollinger5m25(self, base_time):
        # bollinger 5m 2.5sigma
        ind_type = "bollinger5m2.5"
        sql = "select upper_sigma, lower_sigma, base_line from INDICATOR_TABLE where instrument = \'%s\' and insert_time <= \'%s\' and type = \'%s\' order by insert_time DESC limit 1" % (self.instrument, base_time, ind_type)
        response = self.mysql_connector.select_sql(sql)
        self.upper_sigma_5m25 = response[0][0]
        self.lower_sigma_5m25 = response[0][1]
        self.base_line_5m25 = response[0][2]

    def setBollinger5m3(self, base_time):
        # bollinger 5m 3sigma
        ind_type = "bollinger5m3"
        sql = "select upper_sigma, lower_sigma, base_line from INDICATOR_TABLE where instrument = \'%s\' and insert_time <= \'%s\' and type = \'%s\' order by insert_time DESC limit 1" % (self.instrument, base_time, ind_type)
        response = self.mysql_connector.select_sql(sql)
        self.upper_sigma_5m3 = response[0][0]
        self.lower_sigma_5m3 = response[0][1]
        self.base_line_5m3 = response[0][2]


    def setBollinger1h3(self, base_time):
        # bollinger 1h 3sigma
        ind_type = "bollinger1h3"
        sql = "select upper_sigma, lower_sigma, base_line from INDICATOR_TABLE where instrument = \'%s\' and insert_time <= \'%s\' and type = \'%s\' order by insert_time DESC limit 1" % (self.instrument, base_time, ind_type)
        response = self.mysql_connector.select_sql(sql)
        self.upper_sigma_1h3 = response[0][0]
        self.lower_sigma_1h3 = response[0][1]
        self.base_line_1h3 = response[0][2]

    def setEwma5m50(self, base_time):
        # ewma5m50
        ind_type = "ewma5m50"
        sql = "select ewma_value, slope from INDICATOR_TABLE where instrument = \'%s\' and insert_time <= \'%s\' and type = \'%s\' order by insert_time DESC limit 1" % (self.instrument, base_time, ind_type)
        response = self.mysql_connector.select_sql(sql)
        self.ewma5m50_value = response[0][0]
        self.ewma5m50_slope = response[0][1]

    def setEwma5m200(self, base_time):
        # ewma5m200
        ind_type = "ewma5m200"
        sql = "select ewma_value from INDICATOR_TABLE where instrument = \'%s\' and insert_time <= \'%s\' and type = \'%s\' order by insert_time DESC  limit 1" % (self.instrument, base_time, ind_type)
        response = self.mysql_connector.select_sql(sql)
        self.ewma5m200_value = response[0][0]

    def setSlopeEwma1h50(self, base_time):
        # ewma1h50
        ind_type = "ewma1h50"
        sql = "select ewma_value, slope from INDICATOR_TABLE where instrument = \'%s\' and insert_time <= \'%s\' and type = \'%s\' order by insert_time DESC  limit 5" % (self.instrument, base_time, ind_type)
        response = self.mysql_connector.select_sql(sql)
        tmp = []
        for res in response:
            tmp.append(res[0])
        tmp.reverse()
        self.ewma1h50_slope = tmp[4] - tmp[0]

    def setSlopeBollinger1h3(self, base_time):
        # ewma1h50
        ind_type = "bollinger1h3"
        sql = "select base_line, upper_sigma, lower_sigma from INDICATOR_TABLE where instrument = \'%s\' and insert_time <= \'%s\' and type = \'%s\' order by insert_time DESC  limit 5" % (self.instrument, base_time, ind_type)
        response = self.mysql_connector.select_sql(sql)
        tmp_base_line = []
        tmp_upper_sigma = []
        tmp_lower_sigma = []
        for res in response:
            tmp_base_line.append(res[0])
            tmp_upper_sigma.append(res[1])
            tmp_lower_sigma.append(res[2])

        tmp_base_line.reverse()
        tmp_upper_sigma.reverse()
        tmp_lower_sigma.reverse()
        self.bollinger1h3_slope = tmp_base_line[4] - tmp_base_line[0]
        self.bollinger1h3_upper_sigma_slope = tmp_upper_sigma[4] - tmp_upper_sigma[0]
        self.bollinger1h3_lower_simga_slope = tmp_lower_sigmag[4] - tmp_lower_sigma[0]


    def setEwma1h200(self, base_time):
        # ewma1h200
        ind_type = "ewma1h200"
        sql = "select ewma_value from INDICATOR_TABLE where instrument = \'%s\' and insert_time <= \'%s\' and type = \'%s\' order by insert_time DESC  limit 1" % (self.instrument, base_time, ind_type)
        response = self.mysql_connector.select_sql(sql)
        self.ewma1h200_value = response[0][0]

    def setHighlowPrice(self, base_time, span):
        # high low price
        ind_type = "highlow"
        end_time = base_time - timedelta(hours=1)
        sql = "select high_price, low_price from INDICATOR_TABLE where instrument = \'%s\' and insert_time <= \'%s\' and type = \'%s\' order by insert_time DESC limit %s" % (self.instrument, end_time, ind_type, span)
        response = self.mysql_connector.select_sql(sql)
        high_price_list = []
        low_price_list = []
        for res in response:
            high_price_list.append(res[0])
            low_price_list.append(res[1])

        self.high_price = max(high_price_list)
        self.low_price =  min(low_price_list)

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
