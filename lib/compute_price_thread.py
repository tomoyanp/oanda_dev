#coding: utf-8
#############################################
# Parent Class ===> new price_object
# Parent Class ===> new thread
# Parent Class ===> thread.setBaseTime
# Thread Class ===> compute price and price_object.setPrice
# Parent Class ===> price_object.getPrice
#############################################

import threading
from datetime import datetime, timedelta
from indicator_object import IndicatorObject
from mysql_connector import MysqlConnector
from common import instrument_init, decideMarket, getEWMA, getBollingerDataSet, getSlope

class ComputePriceThread(threading.Thread):
    def __init__(self, instrument, base_path, config_name, indicator_object, base_time):
        super(ComputePriceThread, self).__init__()
        self.instrument = instrument
        self.config_data = instrument_init(instrument, base_path, config_name)
        self.indicator_object = indicator_object
        self.old_base_time = base_time
        self.base_time = base_time
        self.mysql_connector = MysqlConnector()
        self.setPrice(base_time)
        self.setIndicator(base_time)


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
        #print sql
        response = self.mysql_connector.select_sql(sql)

        for res in response:
            ask_price = res[0]
            bid_price = res[1]

        hi_price = (ask_price + bid_price)/2

        sql = "select min(ask_price), min(bid_price) from %s_TABLE where insert_time > \'%s\' and insert_time < \'%s\'" % (self.instrument, before_start_time, before_end_time)
        #print sql
        response = self.mysql_connector.select_sql(sql)

        for res in response:
            ask_price = res[0]
            bid_price = res[1]

        min_price = (ask_price + bid_price)/2

        return hi_price, min_price

    def setBaseTime(self, base_time):
        self.base_time = base_time

    def getBaseTime(self):
        return self.base_time

    def setInitialPrice(self, base_time):
        time_width = self.config_data["time_width"]
        end_time = base_time.strftime("%Y-%m-%d %H:%M:%S")
        sql = "select ask_price, bid_price, insert_time from %s_TABLE where insert_time < \'%s\' ORDER BY insert_time DESC limit %s" % (self.instrument, end_time, time_width)
        response = self.mysql_connector.select_sql(sql)
        self.indicator_object.setPriceList(response)

    def addPrice(self, base_time):
        start_time = self.old_base_time.strftime("%Y-%m-%d %H:%M:%S")
        end_time = base_time.strftime("%Y-%m-%d %H:%M:%S")
        sql = "select ask_price, bid_price, insert_time from %s_TABLE where insert_time >= \'%s\' and insert_time < \'%s\' ORDER BY insert_time ASC" % (self.instrument, start_time, end_time)
        response = self.mysql_connector.select_sql(sql)
        self.indicator_object.addPriceList(response)

    def setPrice(self, base_time):
        if len(self.indicator_object.getAskPriceList()) == 0:
            self.setInitialPrice(base_time)
        else:
            self.addPrice(base_time)

    def calculatePollingTime(self, base_time, cmp_object, polling_time):
        flag = False
        if len(cmp_object) > 0:
            get_time = cmp_object["get_time"]
            if base_time > (get_time + timedelta(seconds=polling_time)):
                flag = True
            else:
                pass
        else:
            flag = True

        return flag

    def setIndicator(self, base_time):
        ask_price_list = self.indicator_object.getAskPriceList()
        bid_price_list = self.indicator_object.getBidPriceList()

        # 1時間置きに実行
        polling_time = 3600
        cmp_object = self.indicator_object.getHighLowPriceDataset()
        if self.calculatePollingTime(base_time, cmp_object, polling_time):
            print "NOOOOOOOOOOOOOOOOOOOOOOO"
            # 前日高値、安値の計算
            high_price, low_price = self.getHiLowPriceBeforeDay(base_time)
            self.indicator_object.setHighLowPriceDataset(high_price, low_price, base_time)

            wma_length = 200
            candle_width = 3600
            # 移動平均の取得(WMA200 1h)
            ewma200_1h = getEWMA(ask_price_list, bid_price_list, wma_length, candle_width)
            self.indicator_object.setEwma200_1hDataset(ewma200_1h, base_time)

        # 2.5シグマボリンジャーバンドを取得する
        window_size = 28
        candle_width = 300
        sigma_valiable = 2.5
        data_set = getBollingerDataSet(ask_price_list, bid_price_list, window_size, sigma_valiable, candle_width)
        self.indicator_object.setBollinger2p5sigmaDataset(data_set, base_time)

        # 移動平均の取得(WMA50 5m)
        wma_length = 50
        candle_width = 300
        ewma50 = getEWMA(ask_price_list, bid_price_list, wma_length, candle_width)
        # 短期トレンドの取得
        slope_length = (10 * candle_width) * -1
        slope_list = ewma50[slope_length:]
        slope = getSlope(slope_list)
        self.indicator_object.setEwma50_5mDataset(ewma50, slope, base_time)

        # 移動平均の取得(WMA200 5m)
        wma_length = 200
        candle_width = 300
        ewma200 = getEWMA(ask_price_list, bid_price_list, wma_length, candle_width)
        self.indicator_object.setEwma200_5mDataset(ewma200, base_time)

    def run(self):
        print "thread start"
        for i in range(0, 100):
            #print "thread start"
#        while True:
            base_time = self.getBaseTime()
            #print base_time
            #print "=========================="
            #print "base_time = %s" % base_time
            #print "old_base_time = %s" % self.old_base_time
            if self.old_base_time < base_time:
                print base_time
                if decideMarket(base_time):
                    self.setPrice(base_time)
                    self.setIndicator(base_time)
                self.old_base_time = base_time
            else:
                pass
            #print "thread end"
        print "thread end"
