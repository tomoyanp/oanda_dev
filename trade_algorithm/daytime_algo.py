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
        self.setIndicator(base_time)
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
                if hour < 4 or hour > 14 or (hour == 14 and minutes > 50):
                    pass
                else:
                    # 1分足の終値付近で計算ロジックに入る
                    if seconds <= 10:
                        self.debug_logger.info("%s :DaytimeLogic START" % base_time)
                        self.setIndicator(base_time)
                        current_price = self.getCurrentPrice()
                        trade_flag = self.decideDaytimeTrade(trade_flag, current_price)

            return trade_flag
        except:
            raise

    # 損切り、利確はオーダー時に出している
    # ここでは、急に逆方向に動いた時に決済出来るようにしている
    def decideStl(self, base_time):
        try:
            stl_flag = False
            ex_stlmode = self.config_data["ex_stlmode"]
            if self.order_flag:
                if ex_stlmode == "on":
                    minutes = base_time.minute
                    seconds = base_time.second
                    weekday = base_time.weekday()
                    hour = base_time.hour
                    current_price = self.getCurrentPrice()
                    if minutes % 5 == 0 and seconds <= 10:
                        self.debug_logger.info("%s :DaytimeStlLogic START" % base_time)
                        self.setIndicator(base_time)
                        stl_flag = self.decideDaytimeStopLoss(stl_flag, current_price)

                if hour == 14 and minutes > 50:
                    self.result_logger.info("# Execute Settlemnt: daytime algorithm timeup")
                    stl_flag = True

            else:
                pass

            return stl_flag
        except:
            raise

    def decideDaytimeStopLoss(self, stl_flag, current_price):


        return stl_flag

    def decideDaytimeTrade(self, trade_flag, current_price):

        if self.upper_sigma_1m3 < current_price:
            self.result_logger("# current_price higher than upper_sigma_1m3")
            trade_flag = "buy"
        elif self.lower_sigma > current_price:
            self.result_logger("# current_price lower than upper_sigma_1m3")
            trade_flag = "sell"

        else:
            pass

        return trade_flag


    def setIndicator(self, base_time):
        self.setBollinger1m3(base_time)
