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
from get_indicator import getBollingerWrapper, getVolatilityPriceWrapper, getHighlowPriceWrapper, getLastPriceWrapper, getWeekStartPrice
from trade_calculator import decideLowExceedPrice, decideLowSurplusPrice, decideHighExceedPrice, decideHighSurplusPrice, decideVolatility, decideDailyVolatilityPrice
from mysql_connector import MysqlConnector
from datetime import datetime, timedelta
from logging import getLogger, FileHandler, DEBUG

class TrendReverseAlgo(SuperAlgo):
    def __init__(self, instrument, base_path, config_name, base_time):
        super(TrendReverseAlgo, self).__init__(instrument, base_path, config_name, base_time)
        self.sell_flag = False
        self.buy_flag = False
        self.slope = 0
        self.stop_loss_price = 0
        self.take_profit_price = 0
        self.first_flag = False
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

                # if weekday == Saturday, will have no entry.
                if weekday == 5 and hour >= 5:
                    trade_flag = "pass"
                else:
                    trade_flag = self.decideReverseTrade(trade_flag, current_price, base_time)

                self.writeDebugLog(base_time, current_price)
            return trade_flag
        except:
            raise

    def decideStl(self, base_time):
        try:
            hour = base_time.hour
            weekday = base_time.weekday()
            stl_flag = False

            self.setIndicator(base_time)
            current_price = self.getCurrentPrice()



            if current_price > self.upper_sigma_1m3:
                stl_flag = True
                self.writeResultLog(current_price)
            elif current_price < self.lower_sigma_1m3:
                stl_flag = True
                self.writeResultLog(current_price)

#            if self.first_flag == False:
#                if current_price < self.lower_sigma_1m2:
#                    self.first_flag = True
#                elif current_price > self.upper_sigma_1m2:
#                    self.first_flag = True
#
#            if self.first_flag:
#                if (self.base_line_1m3 - 0.01) <= current_price <= (self.base_line_1m3 + 0.01):
#                    stl_flag = True
#                    self.writeResultLog(current_price)
#                elif (self.base_line_1m3 - 0.01) <= current_price <= (self.base_line_1m3 + 0.01):
#                    stl_flag = True
#                    self.writeResultLog(current_price)

            self.writeDebugLog(base_time, self.getCurrentPrice())
            return stl_flag
        except:
            raise


    def decideReverseTrade(self, trade_flag, current_price, base_time):
        hour = base_time.hour
        if (self.ask_price - self.bid_price) < 0.02:
            self.setIndicator(base_time)
            if self.slope > 0 and (self.base_line_1m3 - 0.01) <= current_price <= (self.base_line_1m3 + 0.01):
#                if self.slope > 0.01:
                if self.slope > 0:
                    trade_flag = "buy"
                    self.result_logger.info("###################################")
                    self.result_logger.info("in TradeFollow Algorithm")
                    self.writeResultLog(current_price)
                else:
                    trade_flag = "sell"
                    self.result_logger.info("###################################")
                    self.result_logger.info("in TradeReverse Algorithm")
                    self.writeResultLog(current_price)
            elif self.slope < 0 and (self.base_line_1m3 - 0.01) <= current_price <= (self.base_line_1m3 + 0.01):
#                if self.slope < -0.01:
                if self.slope < 0:
                    trade_flag = "sell"
                    self.result_logger.info("###################################")
                    self.result_logger.info("in TradeFollow Algorithm")
                    self.writeResultLog(current_price)

                else:
                    trade_flag = "buy"
                    self.result_logger.info("###################################")
                    self.result_logger.info("in TradeReverse Algorithm")
                    self.writeResultLog(current_price)

        self.writeDebugLog(base_time, current_price)

        return trade_flag

    def resetFlag(self):
        self.sell_flag = False
        self.buy_flag = False
        self.most_low_price = 0
        self.most_high_price = 0
        self.take_profit_price = 0
        self.stop_loss_price = 0
        self.first_flag = False
        super(TrendReverseAlgo, self).resetFlag()

    def setIndicator(self, base_time):
        slope_length = 5
        dataset = getBollingerWrapper(base_time, self.instrument, table_type="1m", window_size=28, connector=self.mysql_connector, sigma_valiable=3, length=slope_length)
        self.upper_sigma_1m3 = dataset["upper_sigmas"][-1]
        self.lower_sigma_1m3 = dataset["lower_sigmas"][-1]
        self.base_line_1m3 = dataset["base_lines"][-1]

        base_lines = dataset["base_lines"][(slope_length * -1):]
        self.slope = getSlope(base_lines)

        dataset = getBollingerWrapper(base_time, self.instrument, table_type="1m", window_size=28, connector=self.mysql_connector, sigma_valiable=2, length=0)
        self.upper_sigma_1m2 = dataset["upper_sigmas"][-1]
        self.lower_sigma_1m2 = dataset["lower_sigmas"][-1]
        self.base_line_1m2 = dataset["base_lines"][-1]


    def writeDebugLog(self, base_time, current_price):
        self.debug_logger.info("# in TrendReverse Algorithm : %s" % base_time)
        self.debug_logger.info("# current_price=%s" % current_price)

    def writeResultLog(self, current_price):
        self.result_logger.info("# current_price=%s" % current_price)
        self.result_logger.info("# self.upper_sigma_1m3=%s" % self.upper_sigma_1m3)
        self.result_logger.info("# self.lower_sigma_1m3=%s" % self.lower_sigma_1m3)
        self.result_logger.info("# self.base_line_1m3=%s" % self.base_line_1m3)
        self.result_logger.info("# self.slope=%s" % self.slope)
