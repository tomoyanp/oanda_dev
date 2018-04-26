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

class ExpantionAlgo(SuperAlgo):
    def __init__(self, instrument, base_path, config_name, base_time):
        super(ExpantionAlgo, self).__init__(instrument, base_path, config_name, base_time)
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
        self.mode = ""
        self.buy_count = 0
        self.sell_count = 0
        self.week_start_price = 0
        self.setIndicator(base_time)

    def decideTrade(self, base_time):
        trade_flag = "pass"
        try:
            if self.order_flag:
                pass
            else:
                self.setDailyIndicator(base_time)

                weekday = base_time.weekday()
                hour = base_time.hour
                minutes = base_time.minute
                seconds = base_time.second
                current_price = self.getCurrentPrice()
                if (minutes % 5 == 4 and seconds >= 50):
                    self.setIndicator(base_time)
                    # if weekday == Saturday, will have no entry.
                    if weekday == 5 and hour >= 5:
                        trade_flag = "pass"
                        self.buy_count = 0
                        self.sell_count = 0

                    elif hour >= 15 or hour < 4:
                        self.debug_logger.info("%s :TrendExpantionLogic START" % base_time)
                        trade_flag = self.decideExpantionTrade(trade_flag, current_price, base_time)
                    else:
                        self.buy_count = 0
                        self.sell_count = 0

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

                self.setDailyIndicator(base_time)
                if ex_stlmode == "on":
                    minutes = base_time.minute
                    seconds = base_time.second
                    weekday = base_time.weekday()
                    hour = base_time.hour
                    current_price = self.getCurrentPrice()
                    if minutes % 5 == 4 and seconds >= 50:
                        self.setIndicator(base_time)
                        # 土曜の5時以降にポジションを持っている場合は決済する
                        if weekday == 5 and hour >= 5:
                            self.result_logger.info("# weekend stl logic")
                            stl_flag = True
                        else:
                            self.debug_logger.info("%s :ExpantionStlLogic START" % base_time)
                            stl_flag = self.decideExpantionStopLoss(stl_flag, current_price, base_time)
                            stl_flag = self.decideTrailLogic(stl_flag, self.ask_price, self.bid_price)
            else:
                pass

            return stl_flag
        except:
            raise



    def calcBuyExpantion(self, current_price, base_time):
        # when current_price touch reversed sigma, count = 0
        # when value is bigger than 2 between upper 3sigma and lower 3sigma, bollinger band base line's slope is bigger than 0,
        # count += 1

        if self.buy_count == 2:
            pass
        else:
            if current_price > (self.upper_sigma_5m3):
                if (self.upper_sigma_1h3 - self.lower_sigma_1h3) < 2 and self.slope > 0:
                    self.buy_count = self.buy_count + 1

                self.sell_count = 0

            if self.buy_count == 2:
                self.first_flag_time = base_time


    def calcSellExpantion(self, current_price, base_time):
        if self.sell_count == 2:
            pass
        else:
            if current_price < (self.lower_sigma_5m3):
                if (self.upper_sigma_1h3 - self.lower_sigma_1h3) < 2 and self.slope < 0:
                    self.sell_count = self.sell_count + 1

                self.buy_count = 0

            if self.sell_count == 2:
                self.first_flag_time = base_time

    def decideExpantionStopLoss(self, stl_flag, current_price, base_time):
        up_flag, down_flag = decideVolatility(current_price=current_price, volatility_value=0.3, volatility_buy_price=self.volatility_buy_price, volatility_bid_price=self.volatility_bid_price)
        self.calcBuyExpantion(current_price, base_time)
        self.calcSellExpantion(current_price, base_time)

        if up_flag and self.order_kind == "sell":
            stl_flag = True
            self.result_logger.info("# Execute Volatility Settlement")
            self.result_logger.info("# volatility_buy_price=%s, current_price=%s" % (self.volatility_buy_price, current_price))
            self.buy_count = 0
            self.sell_count = 0
        elif down_flag and self.order_kind == "buy":
            stl_flag = True
            self.result_logger.info("# Execute Volatility Settlement")
            self.result_logger.info("# volatility_bid_price=%s, current_price=%s" % (self.volatility_bid_price, current_price))
            self.buy_count = 0
            self.sell_count = 0

        if self.buy_count == 2 and self.order_kind == "sell":
            if self.ask_price > self.week_start_price:
                stl_flag = True
                self.result_logger.info("# Execute Reverse Settlement")
                self.result_logger.info("# upper_sigma_1h3=%s ,lower_sigma_1h3=%s" % (self.upper_sigma_1h3, self.lower_sigma_1h3))
                self.result_logger.info("# current_price=%s ,upper_sigma_5m3=%s" % (current_price, self.upper_sigma_5m3))
                self.result_logger.info("# slope=%s" % (self.slope))
                self.result_logger.info("# week_start_price=%s" % (self.week_start_price))


        elif self.sell_count == 2 and self.order_kind == "buy":
            if self.bid_price < self.week_start_price:
                stl_flag = True
                self.result_logger.info("# Execute Reverse Settlement")
                self.result_logger.info("# upper_sigma_1h3=%s ,     lower_sigma_1h3=%s" % (self.upper_sigma_1h3, self.lower_sigma_1h3))
                self.result_logger.info("# current_price=%s, lower_sigma_5m3=%s" % (current_price, self.lower_sigma_5m3))
                self.result_logger.info("# slope=%s" % (self.slope))
                self.result_logger.info("# week_start_price=%s" % (self.week_start_price))


        self.debug_logger.info("base time=%s" % base_time)
        self.debug_logger.info("self.order_kind=%s" % self.order_kind)
        self.debug_logger.info("up_flag=%s" % up_flag)
        self.debug_logger.info("down_flag=%s" % down_flag)
        self.debug_logger.info("self.buy_count=%s" % self.buy_count)
        self.debug_logger.info("self.sell_count=%s" % self.sell_count)
        self.debug_logger.info("week_start_price=%s" % (self.week_start_price))
        self.debug_logger.info("#############################################")


        return stl_flag


    def decideExpantionTrade(self, trade_flag, current_price, base_time):
        up_flag, down_flag = decideVolatility(current_price=current_price, volatility_value=0.3, volatility_buy_price=self.volatility_buy_price, volatility_bid_price=self.volatility_bid_price)
        self.calcBuyExpantion(current_price, base_time)
        self.calcSellExpantion(current_price, base_time)

        if up_flag:
            trade_flag = "buy"
            self.result_logger.info("#######################################################")
            self.result_logger.info("# in volatility_price Algorithm")
            self.result_logger.info("# volatility_buy_price=%s, current_price=%s" % (self.volatility_buy_price, current_price))
            self.debug_logger.info("volatility_price + 0.5 = %s, current_price=%s" % (float(self.volatility_buy_price) + float(0.5), current_price))
            self.buy_count = 0
            self.sell_count = 0
        elif down_flag:
            trade_flag = "sell"
            self.result_logger.info("#######################################################")
            self.result_logger.info("# in volatility_price Algorithm")
            self.result_logger.info("# volatility_bid_price=%s, current_price=%s" % (self.volatility_bid_price, current_price))
            self.debug_logger.info("volatility_price - 0.5 = %s, current_price=%s " % (float(self.volatility_buy_price) + float(0.5), current_price))
            self.buy_count = 0
            self.sell_count = 0

        if self.buy_count == 2 and trade_flag == "pass":
            if self.ask_price > self.week_start_price:
                trade_flag = "buy"
                self.result_logger.info("#######################################################")
                self.result_logger.info("# in Expantion Algorithm")
                self.result_logger.info("# first_flag_time=%s" % self.first_flag_time)
                self.result_logger.info("# upper_sigma_1h3=%s , lower_sigma_1h3=%s" % (self.upper_sigma_1h3, self.lower_sigma_1h3))
                self.result_logger.info("# current_price=%s, upper_sigma_5m3=%s" % (current_price, self.upper_sigma_5m3))
                self.result_logger.info("# slope=%s" % (self.slope))
                self.result_logger.info("# week_start_price=%s" % (self.week_start_price))
                self.buy_count = 0
                self.sell_count = 0

        elif self.sell_count == 2 and trade_flag == "pass":
            if self.bid_price < self.week_start_price:
                trade_flag = "sell"
                self.result_logger.info("#######################################################")
                self.result_logger.info("# in Expantion Algorithm")
                self.result_logger.info("# first_flag_time=%s" % self.first_flag_time)
                self.result_logger.info("# upper_sigma_1h3=%s , lower_sigma_1h3=%s" % (self.upper_sigma_1h3, self.lower_sigma_1h3))
                self.result_logger.info("# current_price=%s, lower_sigma_5m3=%s" % (current_price, self.lower_sigma_5m3))
                self.result_logger.info("# slope=%s" % (self.slope))
                self.result_logger.info("# week_start_price=%s" % (self.week_start_price))
                self.buy_count = 0
                self.sell_count = 0

        else:
            pass

        if trade_flag != "pass":
            self.mode = "expantion"

        self.debug_logger.info("base time=%s" % base_time)
        self.debug_logger.info("self.order_kind=%s" % self.order_kind)
        self.debug_logger.info("up_flag=%s" % up_flag)
        self.debug_logger.info("down_flag=%s" % down_flag)
        self.debug_logger.info("self.buy_count=%s" % self.buy_count)
        self.debug_logger.info("self.sell_count=%s" % self.sell_count)
        self.debug_logger.info("week_start_price=%s" % (self.week_start_price))
        self.debug_logger.info("#############################################")

        return trade_flag

    def resetFlag(self):
        if self.order_kind == "buy":
            self.buy_count = 0
        elif self.order_kind == "sell":
            self.sell_count = 0
        self.mode = ""
        self.most_high_price = 0
        self.most_low_price = 0
        super(ExpantionAlgo, self).resetFlag()

    def decideTrailLogic(self, stl_flag, current_ask_price, current_bid_price):
        order_price = self.getOrderPrice()
        first_take_profit = 0.5
        second_take_profit = 1.0

        # update the most high and low price
        if self.most_high_price == 0 and self.most_low_price == 0:
            self.most_high_price = order_price
            self.most_low_price = order_price

        if self.most_high_price < current_bid_price:
            self.most_high_price = current_bid_price
        if self.most_low_price > current_ask_price:
            self.most_low_price = current_ask_price

        # first trailing stop logic
        if self.first_flag == "on":
            if self.order_kind == "buy":
                if (current_bid_price - order_price) > first_take_profit:
                    self.trail_flag = True
            elif self.order_kind == "sell":
                if (order_price - current_ask_price) > first_take_profit:
                    self.trail_flag = True
            if self.trail_flag == True and self.order_kind == "buy":
                if (self.most_high_price - 0.5) > current_bid_price:
                    self.result_logger.info("# Execute FirstTrail Stop")
                    self.result_logger.info("# current_bid_price=%s, order_price=%s" % (current_bid_price, order_price))
                    stl_flag = True
            elif self.trail_flag == True and self.order_kind == "sell":
                if (self.most_low_price + 0.5) < current_ask_price :
                    self.result_logger.info("# Execute FirstTrail Stop")
                    self.result_logger.info("# current_ask_price=%s, order_price=%s" % (current_ask_price, order_price))
                    stl_flag = True

        # second trailing stop logic
        if self.second_flag == "on":
            if self.order_kind == "buy":
                if (current_bid_price - order_price) > second_take_profit:
                    self.trail_second_flag = True
            elif self.order_kind == "sell":
                if (order_price - current_ask_price) > second_take_profit:
                    self.trail_second_flag = True
            if self.trail_second_flag == True and self.order_kind == "buy":
                if (self.most_high_price - 0.3) > current_bid_price:
                    self.result_logger.info("# Execute SecondTrail Stop")
                    self.result_logger.info("# current_bid_price=%s, order_price=%s" % (current_bid_price, order_price))
                    stl_flag = True
            elif self.trail_second_flag == True and self.order_kind == "sell":
                if (self.most_low_price + 0.3) < current_ask_price :
                    self.result_logger.info("# Execute SecondTrail Stop")
                    self.result_logger.info("# current_ask_price=%s, order_price=%s" % (current_ask_price, order_price))
                    stl_flag = True

        return stl_flag

    def setIndicator(self, base_time):
        upper_list, lower_list, base_list = getBollingerWrapper(base_time, self.instrument, ind_type="bollinger5m3", span=1, connector=self.mysql_connector)
        self.upper_sigma_5m3 = upper_list[0]
        self.lower_sigma_5m3 = lower_list[0]
        self.base_line_5m3 = base_list[0]

        upper_list, lower_list, base_list = getBollingerWrapper(base_time, self.instrument, ind_type="bollinger1h3", span=1, connector=self.mysql_connector)
        self.upper_sigma_1h3 = upper_list[0]
        self.lower_sigma_1h3 = lower_list[0]
        self.base_line_1h3 = base_list[0]

        upper_list, lower_list, base_list = getBollingerWrapper(base_time, self.instrument, ind_type="bollinger1h3", span=5, connector=self.mysql_connector)
        self.slope = getSlope(base_list)
        self.volatility_buy_price, self.volatility_bid_price = getVolatilityPriceWrapper(self.instrument, base_time, span=5, connector=self.mysql_connector)

    def setDailyIndicator(self, base_time):
        self.week_start_price = getWeekStartPrice(self.instrument, base_time, self.week_start_price, ((self.ask_price + self.bid_price) / 2))
