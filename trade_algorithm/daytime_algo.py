# coding: utf-8
####################################################
# トレード判断
# bollinger 1h3sigmaの幅が1.5以下（expantionの判定）
# bollinger 5m3+0.1の突破
#
# 損切り判断
# １）とりあえず0.3に設定
#
# 利確判断
# １）含み益が最低利益(30pips)を確保しているか確認
# ２）現在価格が移動平均線にタッチしたら決済する
# ３）リミットオーダーは1.0
####################################################

from super_algo import SuperAlgo
from common import instrument_init, account_init, decideMarket, getBollingerDataSet, extraBollingerDataSet, getEWMA, countIndex, getSlope, getOriginalEWMA
from mysql_connector import MysqlConnector
from datetime import datetime, timedelta
from logging import getLogger, FileHandler, DEBUG
import pandas as pd
import decimal


class DaytimeAlgo(SuperAlgo):
    def __init__(self, instrument, base_path, config_name, base_time):
        super(DaytimeAlgo, self).__init__(instrument, base_path, config_name, base_time)
        self.base_price = 0
        self.setPrice(base_time)
        self.debug_logger = getLogger("debug")
        self.result_logger = getLogger("result")
        self.slope = 0
        self.mysql_connector = MysqlConnector()
        self.first_flag = self.config_data["first_trail_mode"]
        self.second_flag = self.config_data["second_trail_mode"]
        self.most_high_price = 0
        self.most_low_price = 0

    def decideTrade(self, base_time):
        trade_flag = "pass"
        try:
            if self.order_flag:
                pass
            else:
                #weekday = base_time.weekday()
                hour = base_time.hour
                minutes = base_time.minute
                seconds = base_time.second
#                if hour == 9 and minutes == 59:
                if hour == 7 and minutes == 59:
                    self.debug_logger.info("%s :DaytimeLogic START" % base_time)
                    start_price, insert_time = self.getStartPrice(base_time)
                    current_price = self.getCurrentPrice()
                    trade_flag = self.decideDaytimeTrade(trade_flag, current_price, start_price)
                    self.result_logger.info("################################")
                    self.result_logger.info("# start_price at %s, values=%s, current_price=%s" % (insert_time, start_price, current_price))
                    self.result_logger.info("# current_price - start_price difference=%s" % (float(current_price) - float(start_price)))

            return trade_flag
        except:
            raise

    # 損切り、利確はオーダー時に出している
    # ここでは、急に逆方向に動いた時に決済出来るようにしている
    def decideStl(self, base_time):
        try:
            stl_flag = False
            if self.order_flag:
                minutes = base_time.minute
                hour = base_time.hour

                if hour == 14 and minutes == 59:
                    self.result_logger.info("# Execute Settlemnt: daytime algorithm timeup")
                    stl_flag = True

            else:
                pass

            return stl_flag
        except:
            raise

    def decideDaytimeStopLoss(self, stl_flag, current_price):


        return stl_flag

    def decideDaytimeTrade(self, trade_flag, current_price, start_price):

        if float(current_price) > float(start_price):
            trade_flag = "buy"
        else:
            trade_flag = "sell"

        return trade_flag

    def getStartPrice(self, base_time):
        start_time = base_time.strftime("%Y-%m-%d 07:00:00")
        width = 24 * 3600
        #start_time = base_time.strftime("%Y-%m-%d 08:00:00")
        sql = "select ask_price, bid_price, insert_time from %s_TABLE where insert_time < \'%s\' order by insert_time desc limit %s" % (self.instrument, start_time, width)
        self.debug_logger.info(base_time)
        self.debug_logger.info(sql)
        response = self.mysql_connector.select_sql(sql)
        ask_price = response[-1][0]
        bid_price = response[-1][1]
        insert_time = response[-1][2]
        self.debug_logger.info(insert_time)

        return ((ask_price + bid_price) / 2), insert_time


