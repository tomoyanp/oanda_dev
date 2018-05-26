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
from common import instrument_init, account_init, decideMarket, getSlope,getEWMA
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
            stl_flag = False

            return stl_flag
        except:
            raise


    def decideReverseTrade(self, trade_flag, current_price, base_time):
        hour = base_time.hour
        seconds = base_time.second
        if hour > 4 and hour < 15:
            if (self.ask_price - self.bid_price) < 0.02:
                if seconds >= 50:
                    self.setIndicator(base_time)
    
                    if self.max_price > self.upper_sigma_1m2 and self.start_price > self.end_price and self.end_price < self.upper_sigma_1m2:
                        trade_flag = "sell"
                        self.result_logger.info("###################################")
                        self.result_logger.info("in TradeReverse Algorithm")
                        self.writeResultLog(current_price)
    
                    elif self.min_price < self.lower_sigma_1m2 and self.start_price < self.end_price and self.end_price > self.lower_sigma_1m2:
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
        slope_length = 0
        dataset = getBollingerWrapper(base_time, self.instrument, table_type="1m", window_size=28, connector=self.mysql_connector, sigma_valiable=2, length=slope_length)
        self.upper_sigma_1m2 = dataset["upper_sigmas"][-1]
        self.lower_sigma_1m2 = dataset["lower_sigmas"][-1]
        self.base_line_1m2 = dataset["base_lines"][-1]

        sql = "select start_price, max_price, min_price, end_price from %s_%s_TABLE where insert_time < \'%s\' order by insert_time desc limit 1" % (self.instrument, "1m", base_time)
        response = self.mysql_connector.select_sql(sql)
        self.start_price = response[0][0]
        self.max_price = response[0][1]
        self.min_price = response[0][2]
        self.end_price = response[0][3]

    def writeDebugLog(self, base_time, current_price):
        self.debug_logger.info("# in TrendReverse Algorithm : %s" % base_time)
        self.debug_logger.info("# current_price=%s" % current_price)

    def writeResultLog(self, current_price):
        self.result_logger.info("# current_price=%s" % current_price)
        self.result_logger.info("# self.upper_sigma_1m2=%s" % self.upper_sigma_1m2)
        self.result_logger.info("# self.lower_sigma_1m2=%s" % self.lower_sigma_1m2)
        self.result_logger.info("# self.base_line_1m2=%s" % self.base_line_1m2)
        self.result_logger.info("# self.start_price=%s" % self.start_price)
        self.result_logger.info("# self.end_price=%s" % self.end_price)
        self.result_logger.info("# self.max_price=%s" % self.max_price)
        self.result_logger.info("# self.min_price=%s" % self.min_price)
