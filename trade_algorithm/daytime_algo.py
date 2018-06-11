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
#
# 押し目バージョン(閾値0.1）
####################################################

from super_algo import SuperAlgo
from common import instrument_init, account_init, decideMarket, getSlope
from get_indicator import getBollingerWrapper, getVolatilityPriceWrapper, getHighlowPriceWrapper, getLastPriceWrapper, getWeekStartPrice
from trade_calculator import decideLowExceedPrice, decideLowSurplusPrice, decideHighExceedPrice, decideHighSurplusPrice, decideVolatility, decideDailyVolatilityPrice
from mysql_connector import MysqlConnector
from datetime import datetime, timedelta
from logging import getLogger, FileHandler, DEBUG

class DaytimeAlgo(SuperAlgo):
    def __init__(self, instrument, base_path, config_name, base_time):
        super(DaytimeAlgo, self).__init__(instrument, base_path, config_name, base_time)
        self.base_price = 0
        self.setPrice(base_time)
        self.debug_logger = getLogger("debug")
        self.result_logger = getLogger("result")
        self.mysql_connector = MysqlConnector()
        self.first_flag = self.config_data["first_trail_mode"]
        self.second_flag = self.config_data["second_trail_mode"]
        self.most_high_price = 0
        self.most_low_price = 0
        self.mode = ""
        self.buy_count = 0
        self.buy_count_price = 0
        self.sell_count = 0
        self.sell_count_price = 0
        self.original_stoploss_rate = 0
        self.stoploss_flag = False
        self.algorithm = ""
        self.high_price = 0
        self.low_price = 500
        self.entry_buy_count = 0
        self.entry_sell_count = 0
        self.setDaytimeIndicator(base_time)
        self.update_price_flag = False


    def updatePrice(self, base_time):
        pass
#        if base_time.hour > 4 and base_time.hour < 15:
#            self.update_price_flag = True
#            if self.ask_price > self.high_price:
#                self.high_price = self.ask_price
#                self.high_basetime = base_time
#            if self.bid_price < self.low_price:
#                self.low_price = self.bid_price
#                self.low_basetime = base_time
#
#        if base_time.hour == 15 and self.update_price_flag:
#            self.update_price_flag = False
#            self.result_logger.info("# self.high_price_time=%s, self.high_price=%s" % (self.high_basetime, self.high_price))
#            self.result_logger.info("# self.low_price_time=%s, self.low_price=%s" % (self.low_basetime, self.low_price))
#            self.low_price = 500
#            self.high_price = 0
             


    def decideTrade(self, base_time):
        self.updatePrice(base_time)
        trade_flag = "pass"
        try:
            if self.order_flag:
                pass
            else:
                current_price = self.getCurrentPrice()
                weekday = base_time.weekday()
                hour = base_time.hour

                # if weekday == Saturday, we will have no entry.
                if weekday == 5 and hour >= 5:
                    trade_flag = "pass"

                else:
                    # if spread rate is greater than 0.5, we will have no entry
                    if (self.ask_price - self.bid_price) >= 0.5:
                        pass

                    else:
                        trade_flag = self.decideDaytimeTrade(trade_flag, current_price, base_time)

            self.writeDebugLog(base_time, mode="trade")

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
                    weekday = base_time.weekday()
                    hour = base_time.hour
                    minutes = base_time.minute

                    # if weekday == Saturday, we will settle one's position.
                    if weekday == 5 and hour >= 5:
                        self.result_logger.info("# weekend stl logic")
                        stl_flag = True

                    elif hour == 9 and minutes == 54 and self.order_kind == "buy":
                        self.result_logger.info("# timeup stl logic")
                        stl_flag = True
                    elif hour == 11 and minutes == 59 and self.order_kind == "sell":
                        self.result_logger.info("# timeup stl logic")
                        stl_flag = True
            else:
                pass

            self.writeDebugLog(base_time, mode="stl")

            return stl_flag
        except:
            raise




    def decideDaytimeTrade(self, trade_flag, current_price, base_time):
        if trade_flag == "pass":
            day = base_time.day
            hour = base_time.hour
            minutes = base_time.minute
            seconds = base_time.second

            if day % 5 == 0 and hour == 7:
                self.setDaytimeIndicator(base_time)
                self.algorithm = "anomary follow"
                trade_flag = "buy"
                self.writeResultLog()

            if day % 5 == 0 and hour == 9 and minutes == 55:
                self.setDaytimeIndicator(base_time)
                self.algorithm = "anomary reverse"
                trade_flag = "sell"
                self.writeResultLog()


        return trade_flag



# reset flag and valiables function after settlement
    def resetFlag(self):
        if self.order_kind == "buy":
            self.buy_count = 0
        elif self.order_kind == "sell":
            self.sell_count = 0
        self.mode = ""
        self.most_high_price = 0
        self.most_low_price = 0
        self.stoploss_flag = False
        self.algorithm = ""
        self.entry_buy_count = 0
        self.entry_sell_count = 0
        super(DaytimeAlgo, self).resetFlag()


    def setDaytimeIndicator(self, base_time):
        target_time = base_time - timedelta(days=1)
        sql = "select start_price, end_price, max_price, min_price from %s_%s_TABLE where insert_time < '%s' order by insert_time desc limit 1" % (self.instrument, "day", target_time)
        response = self.mysql_connector.select_sql(sql)
        self.start_price = response[0][0]
        self.end_price = response[0][1]
        self.max_price = response[0][2]
        self.min_price = response[0][3]

# write log function

    def writeDebugLog(self, base_time, mode):
        self.debug_logger.info("%s: %s Logic START" % (base_time, mode))

    def writeResultLog(self):
        self.result_logger.info("#######################################################")
        self.result_logger.info("# in %s Algorithm" % self.algorithm)
        self.result_logger.info("# self.ask_price=%s" % self.ask_price)
        self.result_logger.info("# self.bid_price=%s" % self.bid_price)
        self.result_logger.info("# self.start_price=%s" % self.start_price)
        self.result_logger.info("# self.end_price=%s" % self.end_price)
        self.result_logger.info("# self.max_price=%s" % self.max_price)
        self.result_logger.info("# self.min_price=%s" % self.min_price)

