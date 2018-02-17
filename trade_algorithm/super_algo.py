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
        self.trade_threshold = self.config_data["trade_threshold"]
        self.optional_threshold = self.config_data["optional_threshold"]
        self.wma_index = self.config_data["candle_width"]
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
        self.trend_index = 0
        self.trend_flag = ""
        self.wma_value = 0
        self.trade_before_flag = ""

        self.profit_history = "i" # initial
        self.order_history  = "i" # initial

        self.start_time = base_time - timedelta(seconds=self.config_data["time_width"])
        self.end_time = base_time
        self.base_time = base_time
        self.trail_flag = False
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

    def setOrderData(self, trade_flag, order_price, order_flag):
        self.order_kind = trade_flag
        self.order_price = order_price
        self.order_flag = order_flag

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

#    def calcThreshold(self, trade_flag, order_price):
#        stop_loss = self.config_data["stop_loss"]
#        take_profit = self.config_data["take_profit"]
#        threshold_list = {}
#        if trade_flag == "buy":
#            threshold_list["stoploss"] = order_price - stop_loss
#            threshold_list["takeprofit"] = order_price + take_profit
#        else:
#            threshold_list["stoploss"] = order_price + stop_loss
#            threshold_list["takeprofit"] = order_price - take_profit
#
#        if take_profit == 0:
#            threshold_list["takeprofit"] = 0
#
#        if stop_loss == 0:
#            threshold_list["stoploss"] = 0
#
#        self.stoploss_rate = threshold_list["stoploss"]
#        self.takeprofit_rate = threshold_list["takeprofit"]
#
#        return threshold_list

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

    def checkTrend(self, target_time, trade_flag):
        trend_mode = self.config_data["trend_follow_mode"]

        if trend_mode == "on":
            trend_time_width = self.config_data["trend_time_width"]
            before_time = target_time - timedelta(hours=trend_time_width)
            start_sql = "select ask_price from %s_TABLE where insert_time > \'%s\' limit 1" % (self.instrument, before_time)
            current_sql = "select ask_price from %s_TABLE where insert_time > \'%s\' limit 1" % (self.instrument, target_time)
            start_result = self.mysqlConnector.select_sql(start_sql)
            current_result = self.mysqlConnector.select_sql(current_sql)

            start_price_list = []
            for result in start_result:
                start_price_list.append(result[0])


            current_price_list = []
            for result in current_result:
                current_price_list.append(result[0])

            start_price = start_price_list[-1]
            current_price = current_price_list[-1]


            trend_threshold = self.config_data["trend_threshold"]
            if (start_price - current_price) > trend_threshold and trade_flag == "sell":
                pass
            elif (current_price - start_price) > trend_threshold and trade_flag == "buy":
                pass
            else:
                trade_flag = "pass"

            return trade_flag

        else:
            return trade_flag


    def tmpCheckTrend(self, target_time):
        trend_time_width = self.config_data["trend_time_width"]
        before_time = target_time - timedelta(hours=trend_time_width)
        start_sql = "select ask_price from %s_TABLE where insert_time > \'%s\' limit 1" % (self.instrument, before_time)
        current_sql = "select ask_price from %s_TABLE where insert_time > \'%s\' limit 1" % (self.instrument, target_time)
        start_result = self.mysqlConnector.select_sql(start_sql)
        current_result = self.mysqlConnector.select_sql(current_sql)

        start_price_list = []
        for result in start_result:
            start_price_list.append(result[0])


        current_price_list = []
        for result in current_result:
            current_price_list.append(result[0])

        start_price = start_price_list[-1]
        current_price = current_price_list[-1]


        slope = current_price - start_price
        return slope


    def newCheckTrend(self, target_time):
       trend_time_width = self.config_data["trend_time_width"]
       trend_time_width = int(trend_time_width)
       before_time = target_time - timedelta(hours=trend_time_width)
       sql = "select ask_price from %s_TABLE where insert_time > \'%s\' and insert_time < \'%s\'" % (self.instrument, before_time, target_time)
       print sql
       response = self.mysqlConnector.select_sql(sql)
       price_list = []
       index_list = []
       index = 1
       for price in response:
           price_list.append(price[0])
           index_list.append(index)
           index = index + 1

       price_list = np.array(price_list)
       index_list = np.array(index_list)
       print price_list
       z = np.polyfit(index_list, price_list, 1)
       slope, intercept = np.poly1d(z)

       return slope


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

    def getHiLowPriceBeforeDay(self, base_time):
        before_day = base_time - timedelta(days=1)

        # 高値安値は直近1時間まで見てみる
        before_end_time = base_time - timedelta(hours=1)
        before_end_time = before_end_time.strftime("%Y-%m-%d %H:%M:%S")

        before_start_time = before_day.strftime("%Y-%m-%d 07:00:00")
        before_start_time = datetime.strptime(before_start_time, "%Y-%m-%d %H:%M:%S")
        if decideMarket(before_start_time):
            before_start_time = before_day.strftime("%Y-%m-%d 07:00:00")
        else:
            before_start_day = base_time - timedelta(days=3)
            before_start_time = before_start_day.strftime("%Y-%m-%d 07:00:00")

        sql = "select max(ask_price), max(bid_price) from %s_TABLE where insert_time > \'%s\' and insert_time < \'%s\'" % (self.instrument, before_start_time, before_end_time)
        print sql
        response = self.mysqlConnector.select_sql(sql)

        for res in response:
            ask_price = res[0]
            bid_price = res[1]

        hi_price = (ask_price + bid_price)/2

        sql = "select min(ask_price), min(bid_price) from %s_TABLE where insert_time > \'%s\' and insert_time < \'%s\'" % (self.instrument, before_start_time, before_end_time)
        print sql
        response = self.mysqlConnector.select_sql(sql)

        for res in response:
            ask_price = res[0]
            bid_price = res[1]

        min_price = (ask_price + bid_price)/2

        return hi_price, min_price

    def getStartEndPrice(self, base_time):
        # 日またぎの場合
        if 0 <= int(base_time.hour) <= 6:
            start_day = base_time - timedelta(days=1)
            start_time = start_day.strftime("%Y-%m-%d 07:00:00")
        else:
            start_time = base_time.strftime("%Y-%m-%d 07:00:00")

        end_time = base_time.strftime("%Y-%m-%d %H:%M:%S")

        sql = "select ask_price, bid_price from %s_TABLE where insert_time = \'%s\'" % (self.instrument, start_time)

        response = self.mysqlConnector.select_sql(sql)
        for res in response:
            ask_price = res[0]
            bid_price = res[1]

        start_price = (ask_price + bid_price)/2

        sql = "select ask_price, bid_price from %s_TABLE where insert_time = \'%s\'" % (self.instrument, end_time)

        response = self.mysqlConnector.select_sql(sql)
        for res in response:
            ask_price = res[0]
            bid_price = res[1]

        end_price = (ask_price + bid_price)/2

        return start_price, end_price

    def getLongEwma(self, base_time):
        # 移動平均の取得(WMA200 * 1h candles)
        wma_length = 200
        candle_width = 3600
        limit_length = wma_length * candle_width
        base_time = base_time.strftime("%Y-%m-%d %H:%M:%S")
        sql = "select ask_price, bid_price, insert_time from %s_TABLE where insert_time < \'%s\' order by insert_time desc limit %s" % (self.instrument, base_time, limit_length)
        print sql

        response = self.mysqlConnector.select_sql(sql)

        ask_price_list = []
        bid_price_list = []
        insert_time_list = []

        for res in response:
            ask_price_list.append(res[0])
            bid_price_list.append(res[1])
            insert_time_list.append(res[2])

        ask_price_list.reverse()
        bid_price_list.reverse()

        ewma200 = getEWMA(ask_price_list, bid_price_list, wma_length, candle_width)

        return ewma200

    def setInitialIndicator(self, base_time):
        # 前日高値、安値の計算
        hi_price, low_price = self.getHiLowPriceBeforeDay(base_time)
        self.hi_low_price_dataset = {"hi_price": hi_price,
                                     "low_price": low_price,
                                     "get_time": base_time}

        # 当日始め値と現在価格の差を取得(現在価格-始値)
        start_price, end_price = self.getStartEndPrice(base_time)
        self.start_end_price_dataset = {"start_price": start_price,
                                        "end_price": end_price,
                                        "get_time": base_time}

        # 1時間足200日移動平均線を取得する
        ewma200_1h = self.getLongEwma(base_time)
        self.ewma200_1h_dataset = {"ewma_value": ewma200_1h[-1],
                               "get_time": base_time}

        # 移動平均じゃなく、トレンド発生＋3シグマ突破でエントリーに変えてみる
        window_size = 28
        candle_width = 300
        sigma_valiable = 2.5
        data_set = getBollingerDataSet(self.ask_price_list, self.bid_price_list, window_size, sigma_valiable, candle_width)
        self.bollinger_2p5sigma_dataset = {"upper_sigma": data_set["upper_sigmas"][-1],
                                           "lower_sigma": data_set["lower_sigmas"][-1],
                                           "base_line": data_set["base_lines"][-1],
                                           "get_time": base_time}

        # 移動平均の取得(WMA50)
        wma_length = 50
        ewma50 = getEWMA(self.ask_price_list, self.bid_price_list, wma_length, candle_width)
        # 短期トレンドの取得
        slope_length = (10 * candle_width) * -1
        slope_list = ewma50[slope_length:]
        slope = getSlope(slope_list)
        self.ewma50_5m_dataset = {"ewma_value": ewma50[-1],
                               "slope": slope,
                               "get_time": base_time}

        # 移動平均の取得(WMA200)
        wma_length = 200
        ewma200 = getEWMA(self.ask_price_list, self.bid_price_list, wma_length, candle_width)
        self.ewma200_5m_dataset = {"ewma_value": ewma200[-1],
                                "get_time": base_time}

        logging.info("######### setInitialIndicator base_time = %s ############" % base_time)
        logging.info("self.hi_low_price_dataset = %s" % self.hi_low_price_dataset)
        logging.info("self.start_end_price_dataset = %s" % self.start_end_price_dataset)
        logging.info("self.bollinger_2p5sigma_dataset = %s" % self.bollinger_2p5sigma_dataset)
        logging.info("self.ewma50_5m_dataset = %s" % self.ewma50_5m_dataset)
        logging.info("self.ewma200_5m_dataset = %s" % self.ewma200_5m_dataset)

    def setIndicator(self, base_time):
        #logging.info("######### setIndicator base_time = %s ############" % base_time)
        polling_time = 1
        cmp_time = self.hi_low_price_dataset["get_time"] + timedelta(hours=polling_time)
        #logging.info("self.hi_low_price_dataset get_time = %s" % self.hi_low_price_dataset["get_time"])
        if cmp_time < base_time and int(base_time.hour) == 7:
            # 前日高値、安値の計算
            hi_price, low_price = self.getHiLowPriceBeforeDay(base_time)
            self.hi_low_price_dataset = {"hi_price": hi_price,
                                         "low_price": low_price,
                                         "get_time": base_time}
        #    logging.info("self.hi_low_price_dataset = %s" % self.hi_low_price_dataset)

        polling_time = 1
        cmp_time = self.start_end_price_dataset["get_time"] + timedelta(hours=polling_time)
        #logging.info("self.start_end_price_dataset get_time = %s" % self.start_end_price_dataset["get_time"])
        if cmp_time < base_time:
            # 当日始め値と現在価格の差を取得(現在価格-始値)
            start_price, end_price = self.getStartEndPrice(base_time)
            self.start_end_price_dataset = {"start_price": start_price,
                                            "end_price": end_price,
                                            "get_time": base_time}
        #    logging.info("self.start_end_price_dataset = %s" % self.start_end_price_dataset)

            # 1時間足200日移動平均線を取得する
            ewma200_1h = self.getLongEwma(base_time)
            self.ewma200_1h_dataset = {"ewma_value": ewma200_1h[-1],
                                       "get_time": base_time}


        polling_time = 60
        cmp_time = self.bollinger_2p5sigma_dataset["get_time"] + timedelta(seconds=polling_time)
        #logging.info("self.bollinger_2p5sigma_dataset get_time = %s" % self.bollinger_2p5sigma_dataset["get_time"])
        if cmp_time < base_time:
            # bollinger_band 2.5sigma
            window_size = 28
            candle_width = 300
            sigma_valiable = 2.5
            data_set = getBollingerDataSet(self.ask_price_list, self.bid_price_list, window_size, sigma_valiable, candle_width)
            self.bollinger_2p5sigma_dataset = {"upper_sigma": data_set["upper_sigmas"][-1],
                                               "lower_sigma": data_set["lower_sigmas"][-1],
                                               "base_line": data_set["base_lines"][-1],
                                               "get_time": base_time}

            # 移動平均の取得(WMA50)
            wma_length = 50
            ewma50 = getEWMA(self.ask_price_list, self.bid_price_list, wma_length, candle_width)
            # 短期トレンドの取得
            slope_length = (10 * candle_width) * -1
            slope_list = ewma50[slope_length:]
            slope = getSlope(slope_list)
            self.ewma50_5m_dataset = {"ewma_value": ewma50[-1],
                                   "slope": slope,
                                   "get_time": base_time}

            # 移動平均の取得(WMA200)
            wma_length = 200
            ewma200 = getEWMA(self.ask_price_list, self.bid_price_list, wma_length, candle_width)
            self.ewma200_5m_dataset = {"ewma_value": ewma200[-1],
                                    "get_time": base_time}
        #    logging.info("self.bollinger_2p5sigma_dataset = %s" % self.bollinger_2p5sigma_dataset)
        #    logging.info("self.ewma50_5m_dataset = %s" % self.ewma50_5m_dataset)
        #    logging.info("self.ewma200_5m_dataset = %s" % self.ewma200_5m_dataset)

    @abstractmethod
    def decideTrade(self):
        pass

    # takeprofit, stoplossではなく、明示的な決済
    @abstractmethod
    def decideStl(self):
        pass
