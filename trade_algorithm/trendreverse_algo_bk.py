# coding: utf-8
####################################################
# Trade Decision
# if trade timing is between 14:00 - 04:00
# if upper and lower sigma value difference is smaller than 2 yen
# if current price is higher or lower than bollinger band 5m 3sigma
# if current_price is higher or lower than max(min) price last day
#
# Stop Loss Decision
# Same Method Above
#
# Take Profit Decision
# Special Trail mode
# if current profit is higher than 50Pips, 50Pips trail mode
# if current profit is higher than 100Pips, 30Pips trail mode
####################################################

from super_algo import SuperAlgo
from common import instrument_init, account_init, decideMarket, getSlope
from get_indicator import getBollingerWrapper, getVolatilityPriceWrapper, getHighlowPriceWrapper, getLastPriceDifferenceWrapper, getWeekStartPrice
from trade_calculator import decideLowExceedPrice, decideLowSurplusPrice, decideHighExceedPrice, decideHighSurplusPrice, decideVolatility, decideDailyVolatilityPrice
from mysql_connector import MysqlConnector
from datetime import datetime, timedelta
from logging import getLogger, FileHandler, DEBUG

class TrendReverseAlgo(SuperAlgo):
    def __init__(self, instrument, base_path, config_name, base_time):
        super(TrendReverseAlgo, self).__init__(instrument, base_path, config_name, base_time)
        self.setPrice(base_time)
        self.debug_logger = getLogger("debug")
        self.result_logger = getLogger("result")
        self.mysql_connector = MysqlConnector()
        self.setIndicator(base_time)

    def decideTrade(self, base_time):
        trade_flag = "pass"
        try:
            if self.order_flag:
                pass
            else:
                current_price = self.getCurrentPrice()
                weekday = base_time.weekday()
                hour = base_time.hour
                minutes = base_time.minute
                seconds = base_time.second

                # if weekday == Saturday, will have no entry.
                if weekday == 5 and hour >= 5:
                    trade_flag = "pass"
                    self.buy_count = 0
                    self.sell_count = 0
                elif (hour < 15 and hour > 4):
                        self.setIndicator(base_time)
                        trade_flag = self.decideReverseTrade(trade_flag, current_price, base_time)

            self.debug_logger.info("Trade Logic at %s" % base_time)
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
                    current_price = self.getCurrentPrice()
                    minutes = base_time.minute
                    seconds = base_time.second
                    weekday = base_time.weekday()
                    hour = base_time.hour

                    # 土曜の5時以降にポジションを持っている場合は決済する
                    if weekday == 5 and hour >= 5:
                        self.result_logger.info("# weekend stl logic")
                        stl_flag = True
                    elif hour == 15:
                        self.result_logger.info("# reverse time up stl logic")
                        stl_flag = True
            else:
                pass

            self.debug_logger.info("Settlement Logic at %s" % base_time)
            return stl_flag
        except:
            raise



    def decideReverseTrade(self, trade_flag, current_price, base_time):
        mode = "trade"
        if current_price > self.upper_sigma_5m25:
            self.writeExpantionLog(current_price, mode, highlow_mode="dummy")
            trade_flag = "sell"

        elif current_price < self.lower_sigma_5m25:
            self.writeExpantionLog(current_price, mode, highlow_mode="dummy")
            trade_flag = "buy"

        self.writeDebugLog(base_time, up_flag="null", down_flag="null", mode=mode)

        return trade_flag



    def resetFlag(self):
        super(TrendReverseAlgo, self).resetFlag()


    def setIndicator(self, base_time):
        upper_list, lower_list, base_list = getBollingerWrapper(base_time, self.instrument, ind_type="bollinger5m2.5", span=1, connector=self.mysql_connector)
        self.upper_sigma_5m25 = upper_list[0]
        self.lower_sigma_5m25 = lower_list[0]
        self.base_line_5m25 = base_list[0]


    # log writer program
    def writeDebugLog(self, base_time, up_flag, down_flag, mode):
        if mode == "trade":
            self.debug_logger.info("%s :TrendExpantionLogic" % base_time)
        elif mode == "stl":
            self.debug_logger.info("%s :ExpantionStlLogic START" % base_time)

        self.debug_logger.info("base time=%s" % base_time)
        self.debug_logger.info("self.order_kind=%s" % self.order_kind)
        self.debug_logger.info("self.upper_sigma_5m25=%s" % self.upper_sigma_5m25)
        self.debug_logger.info("self.lower_sigma_5m25=%s" % self.lower_sigma_5m25)
        self.debug_logger.info("#############################################")


    def writeExpantionLog(self, current_price, mode, highlow_mode):
        if mode == "trade":
            self.result_logger.info("#######################################################")
            self.result_logger.info("# in Expantion Algorithm")
            self.result_logger.info("# upper_sigma_5m25=%s" % self.upper_sigma_5m25)
            self.result_logger.info("# lower_sigma_5m25=%s" % self.lower_sigma_5m25)
            self.result_logger.info("# base_line_5m25=%s" % self.base_line_5m25)
            self.result_logger.info("# current_price=%s" % current_price)

