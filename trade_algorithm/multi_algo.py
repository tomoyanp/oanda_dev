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

class MultiAlgo(SuperAlgo):
    def __init__(self, instrument, base_path, config_name, base_time):
        super(MultiAlgo, self).__init__(instrument, base_path, config_name, base_time)
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
        self.week_start_price = 0
        self.count_threshold = 1
        self.stoploss_flag = False
        self.algorithm = ""
        self.setExpantionIndicator(base_time)
        self.setVolatilityIndicator(base_time)
        self.setDailyIndicator(base_time)

    # decide trade entry timing
    def decideTrade(self, base_time):
        trade_flag = "pass"
        try:
            if self.order_flag:
                pass
            else:
                weekday = base_time.weekday()
                hour = base_time.hour
                minutes = base_time.minute
                seconds = base_time.second
                current_price = self.getCurrentPrice()

                if hour == 7 and minutes == 0 and seconds < 10:
                    self.setDailyIndicator(base_time)

                # if weekday == Saturday, we will have no entry.
                if weekday == 5 and hour >= 5:
                    trade_flag = "pass"
                    self.buy_count = 0
                    self.sell_count = 0

                else:
                    # if spread rate is greater than 0.5, we will have no entry
                    if (self.ask_price - self.bid_price) >= 0.5:
                        pass

                    else:
                        trade_flag = self.decideVolatilityTrade(trade_flag, current_price, base_time)
                        trade_flag = self.decideExpantionTrade(trade_flag, current_price, base_time)

            self.writeDebugLog(base_time, mode="trade")

            return trade_flag
        except:
            raise

    # settlement logic
    def decideStl(self, base_time):
        try:
            stl_flag = False
            ex_stlmode = self.config_data["ex_stlmode"]
            if self.order_flag:


                if ex_stlmode == "on":
                    weekday = base_time.weekday()
                    hour = base_time.hour
                    minutes = base_time.minute
                    seconds = base_time.second
                    current_price = self.getCurrentPrice()

                    if hour == 7 and minutes == 0 and seconds < 10:
                        self.setDailyIndicator(base_time)

                    # if weekday == Saturday, we will settle one's position.
                    if weekday == 5 and hour >= 5:
                        self.result_logger.info("# weekend stl logic")
                        stl_flag = True

                    else:
                        stl_flag = self.decideCommonStoploss(stl_flag, current_price, base_time)
                        stl_flag = self.decideTrailLogic(stl_flag, self.ask_price, self.bid_price, base_time)

            else:
                pass

            self.writeDebugLog(base_time, mode="stl")

            return stl_flag
        except:
            raise


    def calcBuyExpantion(self, current_price, base_time):
        # when current_price touch reversed sigma, count = 0
        # when value is bigger than 2 between upper 3sigma and lower 3sigma, bollinger band base line's slope is bigger than 0,
        # count += 1

        if self.buy_count == 0:
            if current_price > (self.upper_sigma_5m3) > 0 and (self.upper_sigma_1h3 - self.lower_sigma_1h3) < 2:
                self.buy_count = self.buy_count + 1
                self.buy_count_price = current_price
                self.sell_count = 0

        else:
            if current_price > (self.upper_sigma_5m3) and current_price > self.buy_count_price and (self.upper_sigma_1h3 - self.lower_sigma_1h3) < 2:
                self.buy_count = self.buy_count + 1
                self.first_flag_time = base_time
                self.sell_count = 0
                self.buy_count_price = current_price


    def calcSellExpantion(self, current_price, base_time):
        if self.sell_count == 0:
            if current_price < self.lower_sigma_5m3 and (self.upper_sigma_1h3 - self.lower_sigma_1h3) < 2:
                self.sell_count = self.sell_count + 1
                self.sell_count_price = current_price
                self.buy_count = 0

        else:
            if current_price < self.lower_sigma_5m3 and current_price < self.sell_count_price and (self.upper_sigma_1h3 - self.lower_sigma_1h3) < 2:
                self.sell_count = self.sell_count + 1
                self.first_flag_time = base_time
                self.buy_count = 0

    def decideExpantionTrade(self, trade_flag, current_price, base_time):
        if trade_flag == "pass":
            hour = base_time.hour
            minutes = base_time.minute
            seconds = base_time.second
            if minutes % 5 == 4 and seconds < 10:
                self.setExpantionIndicator(base_time)
                self.calcBuyExpantion(current_price, base_time)
                self.calcSellExpantion(current_price, base_time)
                if self.buy_count > self.count_threshold and trade_flag == "pass":
                    surplus_flag, surplus_mode = decideHighSurplusPrice(current_price=self.end_price_5m, high_price=self.high_price, threshold=0.5)
                    exceed_flag, exceed_mode = decideHighExceedPrice(current_price=self.end_price_5m, high_price=self.high_price, threshold=0.2)

                    if surplus_flag:
                        trade_flag = "buy"
                        self.algorithm = "expantion"
                        self.writeResultLog()
                        self.buy_count = 0
                        self.sell_count = 0

                    elif exceed_flag:
                        trade_flag = "buy"
                        self.algorithm = "expantion"
                        self.writeResultLog()
                        self.buy_count = 0
                        self.sell_count = 0

                elif self.sell_count > self.count_threshold and trade_flag == "pass":
                    surplus_flag, surplus_mode = decideLowSurplusPrice(current_price=self.end_price_5m, low_price=self.low_price, threshold=0.5)
                    exceed_flag, exceed_mode = decideLowExceedPrice(current_price=self.end_price_5m, low_price=self.low_price, threshold=0.2)

                    if surplus_flag:
                        trade_flag = "sell"
                        self.algorithm = "expantion"
                        self.writeResultLog()
                        self.buy_count = 0
                        self.sell_count = 0

                    elif exceed_flag:
                        trade_flag = "sell"
                        self.algorithm = "expantion"
                        self.writeResultLog()
                        self.buy_count = 0
                        self.sell_count = 0

            else:
                self.buy_count = 0
                self.sell_count = 0

        self.setExpantionStoploss(trade_flag)
        return trade_flag

    def decideVolatilityTrade(self, trade_flag, current_price, base_time):
        if trade_flag == "pass":
            hour = base_time.hour
            seconds = base_time.second
            common_stoploss = 0.2

            if  (hour >= 15 or hour < 4) and seconds < 10:
                self.setVolatilityIndicator(base_time)
                up_flag, down_flag = decideVolatility(volatility_value=0.3, start_price=self.start_price_1m, end_price=self.end_price_1m)

                if up_flag:
                    trade_flag = "buy"
                    self.buy_count = 0
                    self.sell_count = 0
                    self.original_stoploss_rate = common_stoploss
                    self.algorithm = "volatility"
                    self.writeResultLog()
                elif down_flag:
                    trade_flag = "sell"
                    self.buy_count = 0
                    self.sell_count = 0
                    self.original_stoploss_rate = common_stoploss
                    self.algorithm = "volatility"
                    self.writeResultLog()

        return trade_flag

    def setExpantionStoploss(self, trade_flag):
        if trade_flag != "pass" and self.algorithm == "expantion":
            if trade_flag == "buy" and self.daily_slope > 0:
                self.original_stoploss_rate = 1.0 
                self.result_logger.info("# self.original_stoploss_rate=%s" %  self.original_stoploss_rate)
            elif trade_flag == "buy" and self.daily_slope < 0:
                self.original_stoploss_rate = 0.2
                self.result_logger.info("# self.original_stoploss_rate=%s" %  self.original_stoploss_rate)
            elif trade_flag == "sell" and self.daily_slope < 0:
                self.original_stoploss_rate = 1.0
                self.result_logger.info("# self.original_stoploss_rate=%s" %  self.original_stoploss_rate)
            elif trade_flag == "sell" and self.daily_slope > 0:
                self.original_stoploss_rate = 0.2
                self.result_logger.info("# self.original_stoploss_rate=%s" %  self.original_stoploss_rate)


    def decideCommonStoploss(self, stl_flag, current_price, base_time):
        if self.algorithm == "expantion" or self.algorithm == "volatility" or self.algorithm == "reverse":
            minutes = base_time.minute
            seconds = base_time.second

            if minutes % 5 == 0 and seconds < 10:
                if self.order_kind == "buy":
                    if (self.order_price - self.bid_price) > self.original_stoploss_rate:
                        self.result_logger.info("# execute common stoploss")
                        stl_flag = True

                elif self.order_kind == "sell":
                    if (self.ask_price - self.order_price) > self.original_stoploss_rate:
                        self.result_logger.info("# execute common stoploss")
                        stl_flag = True

        return stl_flag


# trail settlement function
    def decideTrailLogic(self, stl_flag, current_ask_price, current_bid_price, base_time):
        minutes = base_time.minute
        seconds = base_time.second

        if minutes % 5 == 0 and seconds < 10:
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
            if self.order_kind == "buy":
                if (current_bid_price - order_price) > first_take_profit:
                    self.trail_flag = True
            elif self.order_kind == "sell":
                if (order_price - current_ask_price) > first_take_profit:
                    self.trail_flag = True
            if self.trail_flag == True and self.order_kind == "buy":
                if (self.most_high_price - 0.3) > current_bid_price:
                    self.result_logger.info("# Execute FirstTrail Stop")
                    stl_flag = True
            elif self.trail_flag == True and self.order_kind == "sell":
                if (self.most_low_price + 0.3) < current_ask_price :
                    self.result_logger.info("# Execute FirstTrail Stop")
                    stl_flag = True

            # second trailing stop logic
            if self.order_kind == "buy":
                if (current_bid_price - order_price) > second_take_profit:
                    self.trail_second_flag = True
            elif self.order_kind == "sell":
                if (order_price - current_ask_price) > second_take_profit:
                    self.trail_second_flag = True
            if self.trail_second_flag == True and self.order_kind == "buy":
                if (self.most_high_price - 0.3) > current_bid_price:
                    self.result_logger.info("# Execute SecondTrail Stop")
                    stl_flag = True
            elif self.trail_second_flag == True and self.order_kind == "sell":
                if (self.most_low_price + 0.3) < current_ask_price :
                    self.result_logger.info("# Execute SecondTrail Stop")
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
        super(MultiAlgo, self).resetFlag()


# set Indicator dataset function
    def getDailySlope(self, instrument, target_time, span, connector):
        table_type = "day"
        sql = "select end_price from %s_%s_TABLE where insert_time < \'%s\' order by insert_time desc limit %s" % (instrument, table_type, target_time, span)
        response = connector.select_sql(sql)

        price_list = []
        for res in response:
            price_list.append(res[0])


        price_list.reverse()
        slope = getSlope(price_list)

        return slope

    def setExpantionIndicator(self, base_time):
        # set dataset 5minutes
        target_time = base_time - timedelta(minutes=5)
        dataset = getBollingerWrapper(target_time, self.instrument, table_type="5m", window_size=28, connector=self.mysql_connector, sigma_valiable=3, length=0)
        self.upper_sigma_5m3 = dataset["upper_sigmas"][-1]
        self.lower_sigma_5m3 = dataset["lower_sigmas"][-1]
        self.base_line_5m3 = dataset["base_lines"][-1]

        sql = "select start_price, end_price from %s_%s_TABLE where insert_time < \'%s\' order by insert_time desc limit 1" % (self.instrument, "5m", target_time)
        response = self.mysql_connector.select_sql(sql)
        self.start_price_5m = response[0][0]
        self.end_price_5m = response[0][1]


        # set dataset 1hour
        target_time = base_time - timedelta(hours=1)
        dataset = getBollingerWrapper(target_time, self.instrument, table_type="1h", window_size=28, connector=self.mysql_connector, sigma_valiable=3, length=0)
        self.upper_sigma_1h3 = dataset["upper_sigmas"][-1]
        self.lower_sigma_1h3 = dataset["lower_sigmas"][-1]
        self.base_line_1h3 = dataset["base_lines"][-1]

    def setVolatilityIndicator(self, base_time):
        target_time = base_time - timedelta(minutes=1)
        sql = "select start_price, end_price from %s_%s_TABLE where insert_time < \'%s\' order by insert_time desc limit 1" % (self.instrument, "5m", target_time)
        response = self.mysql_connector.select_sql(sql)
        self.start_price_1m = response[0][0]
        self.end_price_1m = response[0][1]

    def setDailyIndicator(self, base_time):
        target_time = base_time - timedelta(days=1)
        self.daily_slope = self.getDailySlope(self.instrument, target_time, span=10, connector=self.mysql_connector)

        sql = "select max_price, min_price from %s_%s_TABLE where insert_time < \'%s\' order by insert_time desc limit 1" % (self.instrument, "day", target_time)
        response = self.mysql_connector.select_sql(sql)
        self.high_price = response[0][0]
        self.low_price = response[0][1]


# write log function

    def writeDebugLog(self, base_time, mode):
        self.debug_logger.info("%s: %s Logic START" % (base_time, mode))
        self.debug_logger.info("self.buy_count=%s" % self.buy_count)
        self.debug_logger.info("self.sell_count=%s" % self.sell_count)
        self.debug_logger.info("self.high_price=%s" % self.high_price)
        self.debug_logger.info("self.low_price=%s" % self.low_price)
        self.debug_logger.info("self.daily_slope=%s" % self.daily_slope)
        self.debug_logger.info("#############################################")

    def writeResultLog(self):
        self.result_logger.info("#######################################################")
        self.result_logger.info("# in %s Algorithm" % self.algorithm)
        self.result_logger.info("# self.daily_slope=%s" % self.daily_slope)
        self.result_logger.info("# self.upper_sigma_1h3=%s" % self.upper_sigma_1h3)
        self.result_logger.info("# self.lower_sigma_1h3=%s" % self.lower_sigma_1h3)
        self.result_logger.info("# self.upper_sigma_5m3=%s" % self.upper_sigma_5m3)
        self.result_logger.info("# self.lower_sigma_5m3=%s" % self.lower_sigma_5m3)
        self.result_logger.info("# self.start_price_5m=%s" % self.start_price_5m)
        self.result_logger.info("# self.end_price_5m=%s" % self.end_price_5m)
        self.result_logger.info("# self.start_price_1m=%s" % self.start_price_1m)
        self.result_logger.info("# self.end_price_1m=%s" % self.end_price_1m)
