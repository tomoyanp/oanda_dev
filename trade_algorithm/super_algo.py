# coding: utf-8

####################################################
#
# 雛形のクラス
#
####################################################

from datetime import datetime,timedelta
import logging
import os
from common import instrument_init, account_init
from abc import ABCMeta, abstractmethod
from mysql_connector import MysqlConnector

#class SuperAlgo(metaclass=ABCMeta):
class SuperAlgo(object):

    def __init__(self, instrument, base_path):
        self.base_path = base_path
        self.instrument = instrument
        self.config_data = instrument_init(self.instrument, self.base_path)
        self.trade_threshold = self.config_data["trade_threshold"]
        self.optional_threshold = self.config_data["optional_threshold"]

        self.ask_price_list = []
        self.bid_price_list = []
        self.insert_time_list = []
        self.order_price = 0
        self.stl_price = 0
        self.stoploss_rate_rate = 0
        self.takeprofit_rate_rate = 0
        now = datetime.now()
        filename = now.strftime("%Y%m%d%H%M%S")
        self.order_flag = False
        self.trade_id = 0
        self.order_kind = ""
#        self.start_follow_time = 000000
#        self.end_follow_time = 235959
        # 前日が陽線引けかどうかのフラグ
#        self.before_flag = before_flag

        self.mysqlConnector = MysqlConnector()
        self.trend_index = 0
        self.trend_flag = ""

################################################
# listは、要素数が大きいほうが古い。
# 小さいほうが新しい
###############################################

    def resetFlag(self):
        self.order_flag = False
        self.order_kind = ""
        self.trade_id = 0

    def getInitialSql(self, base_time):
        time_width = self.config_data["time_width"]
        start_time = base_time - timedelta(seconds=time_width)
        start_time = start_time.strftime("%Y-%m-%d %H:%M:%S")
        end_time = base_time.strftime("%Y-%m-%d %H:%M:%S")
        sql = "select ask_price, bid_price, insert_time from %s_TABLE where insert_time > \'%s\' and insert_time < \'%s\' order by insert_time" % (self.instrument, start_time, end_time)
        print sql
        return sql

    def getAddSql(self, base_time):
        base_time = base_time.strftime("%Y-%m-%d %H:%M:%S")
        sql = "select ask_price, bid_price, insert_time from %s_TABLE where insert_time = \'%s\' limit 1" % (self.instrument, base_time)
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

    def addResponse(self, response):
        if len(response) < 1:
            pass
        else:
            self.ask_price_list.pop(0)
            self.bid_price_list.pop(0)
            self.insert_time_list.pop(0)

        for line in response:
            self.ask_price_list.append(line[0])
            self.bid_price_list.append(line[1])
            self.insert_time_list.append(line[2])

    def setPriceTable(self, base_time):

        if len(self.ask_price_list) < 1:
            sql = self.getInitialSql(base_time)
            print sql
            response = self.mysqlConnector.select_sql(sql)
            self.setResponse(response)
        else:
            cmp_time = self.insert_time_list[len(self.insert_time_list)-1]
            print cmp_time
            print type(cmp_time)
            #cmp_time = datetime.strptime(cmp_time, "%Y-%m-%d %H:%M:%S")
            cmp_time = cmp_time + timedelta(seconds=300)
            if cmp_time < base_time:
                sql = self.getInitialSql(base_time)
                print sql
                response = self.mysqlConnector.select_sql(sql)
                self.setResponse(response)
            else:
                sql = self.getAddSql(base_time)
                print sql
                response = self.mysqlConnector.select_sql(sql)
                self.addResponse(response)

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

            stl_flag = False
            if self.order_kind == "buy":
                if bid_price > self.takeprofit_rate or bid_price < self.stoploss_rate:
                    self.order_flag = False
                    stl_flag = True

            elif self.order_kind == "sell":
                if ask_price < self.takeprofit_rate or ask_price > self.stoploss_rate:
                    self.order_flag = False
                    stl_flag = True

            return stl_flag
        except:
            raise

    def checkTrend(self, target_time):
        print self.trend_flag
        cmp_time = target_time.strftime("%M%S")
        if self.trend_index == 0 or cmp_time == "0000":
            config_data = instrument_init(self.instrument, self.base_path)
            trend_time_width = config_data["trend_time_width"]
            target_time = target_time - timedelta(hours=trend_time_width)
            target_time = target_time.strftime("%Y-%m-%d %H:%M:%S")
            sql = "select ask_price from %s_TABLE where insert_time > \'%s\'" % (self.instrument, target_time)
            print sql
            result_set = self.mysqlConnector.select_sql(sql)

            price_list = []
            for result in result_set:
                price_list.append(result[0])

            if price_list[0] > price_list[len(price_list)-1]:
                self.trend_flag = "sell"

            else:
                self.trend_flag = "buy"

            self.trend_index = self.trend_index + 1

        return self.trend_flag


    @abstractmethod
    def decideTrade(self):
        pass

    # takeprofit, stoplossではなく、明示的な決済
    @abstractmethod
    def decideStl(self):
        pass
