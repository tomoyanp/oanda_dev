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
        self.setVolatilityIndicator(base_time)

    def decideTrade(self, base_time):
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
                        trade_flag = self.decideVolatilityTrade(trade_flag, current_price, base_time)

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

                    # if weekday == Saturday, we will settle one's position.
                    if weekday == 5 and hour >= 5:
                        self.result_logger.info("# weekend stl logic")
                        stl_flag = True

                    elif hour == 15:
                        self.result_logger.info("# timeup stl logic")
                        stl_flag = True
                    else:
                        stl_flag = self.decideTrailLogic(stl_flag, self.ask_price, self.bid_price, base_time)

            else:
                pass

            self.writeDebugLog(base_time, mode="stl")

            return stl_flag
        except:
            raise




    def decideVolatilityTrade(self, trade_flag, current_price, base_time):
        if trade_flag == "pass":
            hour = base_time.hour
            minutes = base_time.minute
            seconds = base_time.second

#            if  hour == 6 or hour == 7 or hour == 8 or hour == 9 or hour == 10:
            if hour == 7 or hour == 8 or hour == 9 or hour == 10:
                if minutes < 15:
                    if minutes % 5 == 4 and seconds <= 10:
                        self.setVolatilityIndicator(base_time)
                        up_flag, down_flag = decideVolatility(current_price=current_price, volatility_value=0.1, volatility_buy_price=self.volatility_buy_price, volatility_bid_price=self.volatility_bid_price)
        
                        if up_flag:
                            trade_flag = "buy"
                            self.algorithm = "volatility"
                            self.writeResultLog()
                        elif down_flag:
                            trade_flag = "sell"
                            self.algorithm = "volatility"
                            self.writeResultLog()

        return trade_flag



# trail settlement function
    def decideTrailLogic(self, stl_flag, current_ask_price, current_bid_price, base_time):
        minutes = base_time.minute
        seconds = base_time.second

#        if minutes % 5 == 4 and seconds >= 50:
        order_price = self.getOrderPrice()
        first_take_profit = 0.2
 
        # update the most high and low price
        if self.most_high_price == 0 and self.most_low_price == 0:
            self.most_high_price = order_price
            self.most_low_price = order_price
 
        if self.most_high_price < current_bid_price:
            self.most_high_price = current_bid_price
        if self.most_low_price > current_ask_price:
            self.most_low_price = current_ask_price
 
        # first trailing stop logic
        if self.order_kind == "buy":
            if (current_bid_price - order_price) > first_take_profit:
                self.trail_flag = True
        elif self.order_kind == "sell":
            if (order_price - current_ask_price) > first_take_profit:
                self.trail_flag = True
        if self.trail_flag == True and self.order_kind == "buy":
            if (self.most_high_price - 0.2) > current_bid_price:
                self.result_logger.info("# Execute FirstTrail Stop")
                stl_flag = True
        elif self.trail_flag == True and self.order_kind == "sell":
            if (self.most_low_price + 0.2) < current_ask_price :
                self.result_logger.info("# Execute FirstTrail Stop")
                stl_flag = True

        return stl_flag

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
        super(DaytimeAlgo, self).resetFlag()


    def setVolatilityIndicator(self, base_time):
        self.volatility_buy_price, self.volatility_bid_price = getVolatilityPriceWrapper(self.instrument, base_time, span=300, connector=self.mysql_connector)

# write log function

    def writeDebugLog(self, base_time, mode):
        self.debug_logger.info("%s: %s Logic START" % (base_time, mode))

    def writeResultLog(self):
        self.result_logger.info("#######################################################")
        self.result_logger.info("# in %s Algorithm" % self.algorithm)
        self.result_logger.info("# self.ask_price=%s" % self.ask_price)
        self.result_logger.info("# self.bid_price=%s" % self.bid_price)
        self.result_logger.info("# volatility_buy_price=%s" % self.volatility_buy_price)
        self.result_logger.info("# volatility_bid_price=%s" % self.volatility_bid_price)

