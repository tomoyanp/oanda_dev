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
        self.buy_count_price = 0
        self.sell_count = 0
        self.sell_count_price = 0
        self.week_start_price = 0
        self.setIndicator(base_time)
        self.high_price, self.low_price = getHighlowPriceWrapper(instrument=self.instrument, base_time=base_time, span=24, slide_span=0, connector=self.mysql_connector)

    def decideTrade(self, base_time):
        trade_flag = "pass"
        try:
            if self.order_flag:
                pass
            else:
                self.setDailyIndicator(base_time)
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
                elif seconds >= 50:
                    self.setCommonlyIndicator(base_time)
                    trade_flag = self.decideVolatilityTrade(trade_flag, current_price, base_time)

                    if minutes % 5 == 4:
                        self.setIndicator(base_time)
                        elif (hour >= 15 or hour < 4):
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


                if ex_stlmode == "on":
                    self.setDailyIndicator(base_time)
                    current_price = self.getCurrentPrice()

                    minutes = base_time.minute
                    seconds = base_time.second
                    weekday = base_time.weekday()
                    hour = base_time.hour

                    # 土曜の5時以降にポジションを持っている場合は決済する
                    if weekday == 5 and hour >= 5:
                        self.result_logger.info("# weekend stl logic")
                        stl_flag = True
                    elif seconds >= 50:
                        self.setCommonlyIndicator(base_time)
                        stl_flag = self.decideVolatilityStopLoss(stl_flag, current_price, base_time)

                        if minutes % 5 == 4:
                            self.setIndicator(base_time)
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

        if self.buy_count == 0:
            if current_price > (self.upper_sigma_5m3):
                self.buy_count = 1
                self.buy_count_price = current_price
                self.sell_count = 0

        elif self.buy_count == 1:
            if current_price > (self.upper_sigma_5m3) and current_price > self.buy_count_price:
                self.buy_count = 2
                self.first_flag_time = base_time
                self.sell_count = 0

        elif self.buy_count == 2:
            pass

    def calcSellExpantion(self, current_price, base_time):
        if self.sell_count == 0:
            if cuurent_price < self.lower_sigma_5m3:
                self.sell_count = 1
                self.sell_count_price = current_price
                self.buy_count = 0

        elif self.sell_count == 1:
            if cuurent_price < self.lower_sigma_5m3 and current_price < self.sell_count_price:
                self.sell_count = 2
                self.first_flag_time = base_time
                self.buy_count = 0

        elif self.sell_count == 2:
            pass

    def decideVolatilityTrade(self, trade_flag, current_price, base_time):
        mode = "trade"
        # volatility price logic
        up_flag, down_flag = decideVolatility(current_price=current_price, volatility_value=0.3, volatility_buy_price=self.volatility_buy_price, volatility_bid_price=self.volatility_bid_price)

        if up_flag:
            trade_flag = "buy"
            self.buy_count = 0
            self.sell_count = 0
            self.writeVolatilityLog(current_price, mode="trade")
        elif down_flag:
            trade_flag = "sell"
            self.buy_count = 0
            self.sell_count = 0
            self.writeVolatilityLog(current_price, mode="trade")

        return trade_flag

    def decideExpantionTrade(self, trade_flag, current_price, base_time):
        mode = "trade"
        # expantion logic
        self.calcBuyExpantion(current_price, base_time)
        self.calcSellExpantion(current_price, base_time)
        if self.buy_count == 2 and trade_flag == "pass":
            surplus_flag, surplus_mode = decideHighSurplusPrice(current_price=current_price, high_price=self.high_price, threshold=0.5)
            exceed_flag, exceed_mode = decideHighExceedPrice(current_price=current_price, high_price=self.high_price, threshold=0.2)

            if surplus_flag:
                trade_flag = "buy"
                self.buy_count = 0
                self.sell_count = 0
                self.writeExpantionLog(current_price, mode=mode, highlow_mode="surplus")

            elif exceed_flag:
                trade_flag = "buy"
                self.buy_count = 0
                self.sell_count = 0
                self.writeExpantionLog(current_price, mode=mode, highlow_mode="exceed")

        elif self.sell_count == 2 and trade_flag == "pass":
            surplus_flag, surplus_mode = decideLowSurplusPrice(current_price=current_price, low_price=self.low_price, threshold=0.5)
            exceed_flag, exceed_mode = decideLowExceedPrice(current_price=current_price, low_price=self.low_price, threshold=0.2)

            if surplus_flag:
                trade_flag = "sell"
                self.buy_count = 0
                self.sell_count = 0
                self.writeExpantionLog(current_price, mode=mode, highlow_mode="surplus")

            elif exceed_flag:
                trade_flag = "sell"
                self.buy_count = 0
                self.sell_count = 0
                self.writeExpantionLog(current_price, mode=mode, highlow_mode="exceed")

        else:
            pass

        if trade_flag != "pass":
            self.mode = "expantion"

#        self.writeDebugLog(base_time, up_flag, down_flag, mode=mode)

        return trade_flag

    def decideVolatilityStopLoss(self, stl_flag, current_price, base_time):
        mode = "stl"
        up_flag, down_flag = decideVolatility(current_price=current_price, volatility_value=0.3, volatility_buy_price=self.volatility_buy_price, volatility_bid_price=self.volatility_bid_price)

        if up_flag and self.order_kind == "sell":
            stl_flag = True
            self.buy_count = 0
            self.sell_count = 0
            self.writeVolatilityLog(current_price, mode=mode)
        elif down_flag and self.order_kind == "buy":
            stl_flag = True
            self.buy_count = 0
            self.sell_count = 0
            self.writeVolatilityLog(current_price, mode=mode)

        return stl_flag

    def decideExpantionStopLoss(self, stl_flag, current_price, base_time):
        mode = "stl"

        if current_price > self.upper_sigma_5m3 and self.order_kind == "sell":
            stl_flag = True
            self.result_logger.info("# Execute Reverse Settlement")
            self.result_logger.info("# current_price=%s, self.upper_sigma_5m3=%s, self.lower_sigma_5m3=%s, self.order_kind=%s" % (current_price, self.upper_sigma_5m3, self.lower_sigma_5m3, self.order_kind))

        elif current_price < self.lower_sigma_5m3 and self.order_kind == "buy":
            stl_flag = True
            self.result_logger.info("# Execute Reverse Settlement")
            self.result_logger.info("# current_price=%s, self.upper_sigma_5m3=%s, self.lower_sigma_5m3=%s, self.order_kind=%s" % (current_price, self.upper_sigma_5m3, self.lower_sigma_5m3, self.order_kind))

        else:
            pass

#        self.writeDebugLog(base_time, up_flag, down_flag, mode=mode)

        return stl_flag

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


    def setCommonlyIndicator(self, base_time):
        self.volatility_buy_price, self.volatility_bid_price = getVolatilityPriceWrapper(self.instrument, base_time, span=60, connector=self.mysql_connector)


    def setDailyIndicator(self, base_time):
        hour = base_time.hour
        minute = base_time.minute
        second = base_time.second
        if hour == 7 and minute == 0 and second <= 10:
            self.high_price, self.low_price = getHighlowPriceWrapper(instrument=self.instrument, base_time=base_time, span=24, slide_span=0, connector=self.mysql_connector)


    # log writer program
    def writeDebugLog(self, base_time, up_flag, down_flag, mode):
        if mode == "trade":
            self.debug_logger.info("%s :TrendExpantionLogic" % base_time)
        elif mode == "stl":
            self.debug_logger.info("%s :ExpantionStlLogic START" % base_time)

        self.debug_logger.info("base time=%s" % base_time)
        self.debug_logger.info("self.order_kind=%s" % self.order_kind)
        self.debug_logger.info("up_flag=%s" % up_flag)
        self.debug_logger.info("down_flag=%s" % down_flag)
        self.debug_logger.info("self.buy_count=%s" % self.buy_count)
        self.debug_logger.info("self.sell_count=%s" % self.sell_count)
        self.debug_logger.info("self.high_price=%s" % self.high_price)
        self.debug_logger.info("self.low_price=%s" % self.low_price)
        self.debug_logger.info("#############################################")

    def writeVolatilityLog(self, current_price, mode):
        if mode == "trade":
            self.result_logger.info("#######################################################")
            self.result_logger.info("# in volatility_price Algorithm")
        elif mode == "stl":
            self.result_logger.info("# Execute Volatility Settlement")

        self.result_logger.info("# volatility_buy_price=%s, current_price=%s" % (self.volatility_buy_price, current_price))
        self.result_logger.info("# volatility_bid_price=%s, current_price=%s" % (self.volatility_bid_price, current_price))

    def writeExpantionLog(self, current_price, mode, highlow_mode):
        if mode == "trade":
            self.result_logger.info("#######################################################")
            self.result_logger.info("# in Expantion Algorithm")
        elif mode == "stl":
            self.result_logger.info("# Execute Reverse Settlement")

        self.result_logger.info("# first_flag_time=%s" % self.first_flag_time)
        self.result_logger.info("# upper_sigma_1h3=%s , lower_sigma_1h3=%s" % (self.upper_sigma_1h3, self.lower_sigma_1h3))
        self.result_logger.info("# current_price=%s, upper_sigma_5m3=%s" % (current_price, self.upper_sigma_5m3))
        self.result_logger.info("# highlow_mode=%s, self.high_price=%s, self.low_price=%s" % (highlow_mode, self.high_price, self.low_price))
        self.result_logger.info("# slope=%s" % (self.slope))
