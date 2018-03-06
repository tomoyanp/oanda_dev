#coding: utf-8
#############################################
# Parent Class ===> new price_object
# Parent Class ===> new thread
# Parent Class ===> thread.setBaseTime
# Thread Class ===> compute price and price_object.setPrice
# Parent Class ===> price_object.getPrice
#############################################

from datetime import datetime, timedelta
from indicator_object import IndicatorObject
from mysql_connector import MysqlConnector
from common import instrument_init, decideMarket, getEWMA, getBollingerDataSet, getSlope
import logging, traceback

class ComputeIndicator:
    def __init__(self, instrument, time_width, base_time):
        self.instrument = instrument
        self.time_width = time_width
        self.indicator_object = IndicatorObject()
        self.old_base_time = base_time
        self.base_time = base_time
        self.mysql_connector = MysqlConnector()
        self.setPrice(base_time)

    def getHiLowPrice(self, base_time):
        # 直近2時間前〜1時間前の高値、安値を入れる
        # 一日で取りたい場合はSQLでフォローする
        start_time = base_time - timedelta(hours=2)
        end_time = base_time - timedelta(hours=1)
        sql = "select max(ask_price), max(bid_price) from %s_TABLE where insert_time > \'%s\' and insert_time < \'%s\'" % (self.instrument, start_time, end_time) 
        response = self.mysql_connector.select_sql(sql)
        for res in response:
            ask_price = res[0]
            bid_price = res[1]
        hi_price = (ask_price + bid_price)/2
        sql = "select min(ask_price), min(bid_price) from %s_TABLE where insert_time > \'%s\' and insert_time < \'%s\'" % (self.instrument, start_time, end_time)
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
        end_time = base_time.strftime("%Y-%m-%d %H:%M:%S")
        sql = "select ask_price, bid_price, insert_time from %s_TABLE where insert_time < \'%s\' ORDER BY insert_time DESC limit %s" % (self.instrument, end_time, self.time_width)
        response = self.mysql_connector.select_sql(sql)
        self.indicator_object.setPriceList(response)

    def addPrice(self, base_time):
        start_time = self.old_base_time.strftime("%Y-%m-%d %H:%M:%S")
        end_time = base_time.strftime("%Y-%m-%d %H:%M:%S")
        sql = "select ask_price, bid_price, insert_time from %s_TABLE where insert_time >= \'%s\' and insert_time < \'%s\'" % (self.instrument, start_time, end_time)
        response = self.mysql_connector.select_sql(sql)
        self.indicator_object.addPriceList(response)

    def setPrice(self, base_time):
        if len(self.indicator_object.getAskPriceList()) == 0:
            self.setInitialPrice(base_time)
        else:
            self.addPrice(base_time)

    def calculatePollingTime(self, base_time, response, polling_time):
        flag = False
        if len(response) > 0:
            get_time = response[0][0]
            if base_time >= (get_time + timedelta(seconds=polling_time)):
                flag = True
            else:
                pass
        else:
            flag = True

        return flag

    def set1hIndicator(self, base_time):
        logging.info("set1hIndicator base_time = %s" % base_time)
        ask_price_list = self.indicator_object.getAskPriceList()
        bid_price_list = self.indicator_object.getBidPriceList()

        try: 
            sql = "select insert_time from INDICATOR_TABLE where insert_time <= \'%s\' and type = \'bollinger1h3\' order by insert_time DESC limit 1" % base_time
            response = self.mysql_connector.select_sql(sql)
            polling_time = 3600
            if self.calculatePollingTime(base_time, response, polling_time):
                # 1時間置きに実行
                ind_type = "highlow"
                # 前日高値、安値の計算
                if decideMarket(base_time - timedelta(hours=2)):
                    high_price, low_price = self.getHiLowPrice(base_time)
        
                    # instrument, type, high_price, low_price, insert_time
                    sql = "insert into INDICATOR_TABLE(instrument, type, high_price, low_price, insert_time) values(\'%s\', \'%s\', %s, %s, \'%s\')" % (self.instrument, ind_type, high_price, low_price, base_time)
                    self.mysql_connector.insert_sql(sql)
                    logging.info(sql)
         
        
                ind_type = "ewma1h200"
                wma_length = 200
                candle_width = 3600
                # 移動平均の取得(WMA200 1h)
                ewma200_1h = getEWMA(ask_price_list, bid_price_list, wma_length, candle_width)
                # instrument, type, ewma_value, insert_time
                sql = "insert into INDICATOR_TABLE(instrument, type, ewma_value,  insert_time) values(\'%s\', \'%s\', %s, \'%s\')" % (self.instrument, ind_type, ewma200_1h[-1], base_time)
                self.mysql_connector.insert_sql(sql)
                logging.info(sql)
        
    
                ind_type = "bollinger1h1"
                window_size = 28
                candle_width = 3600
                sigma_valiable = 1
                data_set = getBollingerDataSet(ask_price_list, bid_price_list, window_size, sigma_valiable, candle_width)
                sql = "insert into INDICATOR_TABLE(instrument, type, upper_sigma, lower_sigma, base_line, insert_time) values(\'%s\', \'%s\', %s, %s, %s, \'%s\')" % (self.instrument, ind_type, data_set["upper_sigmas"][-1], data_set["lower_sigmas"][-1], data_set["base_lines"][-1], base_time)
                self.mysql_connector.insert_sql(sql)
                logging.info(sql)
     
                ind_type = "bollinger1h2.5"
                window_size = 28
                candle_width = 3600
                sigma_valiable = 2.5
                data_set = getBollingerDataSet(ask_price_list, bid_price_list, window_size, sigma_valiable, candle_width)
                sql = "insert into INDICATOR_TABLE(instrument, type, upper_sigma, lower_sigma, base_line, insert_time) values(\'%s\', \'%s\', %s, %s, %s, \'%s\')" % (self.instrument, ind_type, data_set["upper_sigmas"][-1], data_set["lower_sigmas"][-1], data_set["base_lines"][-1], base_time)
                self.mysql_connector.insert_sql(sql)
                logging.info(sql)
     
                ind_type = "bollinger1h3"
                window_size = 28
                candle_width = 3600
                sigma_valiable = 3
                data_set = getBollingerDataSet(ask_price_list, bid_price_list, window_size, sigma_valiable, candle_width)
                sql = "insert into INDICATOR_TABLE(instrument, type, upper_sigma, lower_sigma, base_line, insert_time) values(\'%s\', \'%s\', %s, %s, %s, \'%s\')" % (self.instrument, ind_type, data_set["upper_sigmas"][-1], data_set["lower_sigmas"][-1], data_set["base_lines"][-1], base_time)
                self.mysql_connector.insert_sql(sql)
                logging.info(sql)
 
        except Exception as e:
            logging.info(traceback.format_exc())


    def set5mIndicator(self, base_time):
        ask_price_list = self.indicator_object.getAskPriceList()
        bid_price_list = self.indicator_object.getBidPriceList()

        try: 
            logging.info("set5mIndicator base_time = %s" % base_time)
            # 1シグマボリンジャーバンドを取得する
            window_size = 28
            candle_width = 300
            sigma_valiable = 1
            data_set = getBollingerDataSet(ask_price_list, bid_price_list, window_size, sigma_valiable, candle_width)
            # instrument, type, upper_sigma, lower_sigma, base_line, insert_time
            ind_type = "bollinger5m1"
            sql = "insert into INDICATOR_TABLE(instrument, type, upper_sigma, lower_sigma, base_line, insert_time) values(\'%s\', \'%s\', %s, %s, %s, \'%s\')" % (self.instrument, ind_type, data_set["upper_sigmas"][-1], data_set["lower_sigmas"][-1], data_set["base_lines"][-1], base_time)
            self.mysql_connector.insert_sql(sql)
            logging.info(sql)
    
            # 2.5シグマボリンジャーバンドを取得する
            window_size = 28
            candle_width = 300
            sigma_valiable = 2.5
            data_set = getBollingerDataSet(ask_price_list, bid_price_list, window_size, sigma_valiable, candle_width)
            # instrument, type, upper_sigma, lower_sigma, base_line, insert_time
            ind_type = "bollinger5m2.5"
            sql = "insert into INDICATOR_TABLE(instrument, type, upper_sigma, lower_sigma, base_line, insert_time) values(\'%s\', \'%s\', %s, %s, %s, \'%s\')" % (self.instrument, ind_type, data_set["upper_sigmas"][-1], data_set["lower_sigmas"][-1], data_set["base_lines"][-1], base_time)
            self.mysql_connector.insert_sql(sql)
            logging.info(sql)
    
            # 3シグマボリンジャーバンドを取得する
            window_size = 28
            candle_width = 300
            sigma_valiable = 3
            data_set = getBollingerDataSet(ask_price_list, bid_price_list, window_size, sigma_valiable, candle_width)
            # instrument, type, upper_sigma, lower_sigma, base_line, insert_time
            ind_type = "bollinger5m3"
            sql = "insert into INDICATOR_TABLE(instrument, type, upper_sigma, lower_sigma, base_line, insert_time) values(\'%s\', \'%s\', %s, %s, %s, \'%s\')" % (self.instrument, ind_type, data_set["upper_sigmas"][-1], data_set["lower_sigmas"][-1], data_set["base_lines"][-1], base_time)
            self.mysql_connector.insert_sql(sql)
            logging.info(sql)
    
            # 移動平均の取得(WMA50 5m)
            wma_length = 50
            candle_width = 300
            ewma50 = getEWMA(ask_price_list, bid_price_list, wma_length, candle_width)
            # 短期トレンドの取得
            slope_length = (10 * candle_width) * -1
            slope_list = ewma50[slope_length:]
            slope = getSlope(slope_list)
    
            # instrument, type, ewma_value, insert_time
            ind_type = "ewma5m50"
            sql = "insert into INDICATOR_TABLE(instrument, type, ewma_value, slope, insert_time) values(\'%s\', \'%s\', %s, %s, \'%s\')" % (self.instrument, ind_type, ewma50[-1], slope, base_time)
            self.mysql_connector.insert_sql(sql)
            logging.info(sql)
    
            # 移動平均の取得(WMA200 5m)
            wma_length = 200
            candle_width = 300
            ewma200 = getEWMA(ask_price_list, bid_price_list, wma_length, candle_width)
    
            # instrument, type, ewma_value, insert_time
            ind_type = "ewma5m200"
            sql = "insert into INDICATOR_TABLE(instrument, type, ewma_value, insert_time) values(\'%s\', \'%s\', %s,  \'%s\')" % (self.instrument, ind_type, ewma200[-1], base_time)
            self.mysql_connector.insert_sql(sql)
            logging.info(sql)

        except Exception as e:
            logging.info(traceback.format_exc())

    def computeInsertIndicator(self, base_time, span):
        if decideMarket(base_time):
            self.setPrice(base_time)
            try: 
                if span == "1h":
                    self.set1hIndicator(base_time)
                elif span == "5m":
                    self.set5mIndicator(base_time)
                else:
                    pass
            except Exception as e:
                logging.info(traceback.format_exc())

        else:
            pass
