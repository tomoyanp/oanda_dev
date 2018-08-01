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
# 1. decide perfect order and current_price <-> 5m_sma40
# 2. touch bolligner 2sigma 5m
# 3. break ewma20 1m value

from super_algo import SuperAlgo
from common import instrument_init, account_init, decideMarket, getSlope, getEWMA
from get_indicator import getBollingerWrapper, getVolatilityPriceWrapper, getHighlowPriceWrapper, getLastPriceWrapper, getWeekStartPrice
from trade_calculator import decideLowExceedPrice, decideLowSurplusPrice, decideHighExceedPrice, decideHighSurplusPrice, decideVolatility, decideDailyVolatilityPrice
from mysql_connector import MysqlConnector
from datetime import datetime, timedelta
from logging import getLogger, FileHandler, DEBUG

class TrendReverseAlgo(SuperAlgo):
    def __init__(self, instrument, base_path, config_name, base_time):
        super(TrendReverseAlgo, self).__init__(instrument, base_path, config_name, base_time)
        self.base_price = 0
        self.setPrice(base_time)
        self.debug_logger = getLogger("debug")
        self.result_logger = getLogger("result")
        self.mysql_connector = MysqlConnector()
        self.first_flag = self.config_data["first_trail_mode"]
        self.second_flag = self.config_data["second_trail_mode"]
        self.trail_third_flag = False
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
        self.log_max_price = 0
        self.log_min_price = 0
        self.first_trade_flag = "pass"
        self.second_trade_flag = False
        self.first_trade_time = base_time
        self.second_trade_time = base_time
        self.third_trade_flag = "pass"
        self.third_trade_time = base_time
        self.stl_first_flag = False
        self.buy_flag = False
        self.sell_flag = False
        self.stl_logic = "none"
        self.perfect_order_buycount = 0
        self.perfect_order_sellcount = 0
        self.setReverse5mIndicator(base_time)
        self.setReverse1hIndicator(base_time)
        self.setReverseDailyIndicator(base_time)

    # decide trade entry timing
    def decideTrade(self, base_time):
        self.debug_logger.info("decide Trade Logic Start at %s" % base_time.strftime("%Y-%m-%d %H:%M:%S"))
        trade_flag = "pass"
        try:
#            if self.order_flag:
#                pass
#            else:
            if 1==1:
                weekday = base_time.weekday()
                hour = base_time.hour
                minutes = base_time.minute
                seconds = base_time.second
                current_price = self.getCurrentPrice()

                # if weekday == Saturday, we will have no entry.
                if weekday == 5 and hour >= 5:
                    trade_flag = "pass"
                    self.buy_count = 0
                    self.sell_count = 0

                else:
                    # if spread rate is greater than 0.5, we will have no entry
                    if (self.ask_price - self.bid_price) >= 0.05:
                        self.debug_logger.info("spread logic: NG, ask=%s, bid=%s" % (self.ask_price, self.bid_price))

                    else:
                        self.debug_logger.info("spread logic: OK, ask=%s, bid=%s" % (self.ask_price, self.bid_price))
                        trade_flag = self.decideReverseTrade(trade_flag, current_price, base_time)

                if trade_flag != "pass" and self.order_flag:
                    if trade_flag == "buy" and self.order_kind == "buy":
                        trade_flag = "pass"
                    elif trade_flag == "sell" and self.order_kind == "sell":
                        trade_flag = "pass"
                    else:
                        self.stl_logic = "allovertheworld settlement"
                        self.algorithm = self.algorithm + " by allovertheworld"


            return trade_flag
        except:
            raise

    # settlement logic
    def decideStl(self, base_time):
        self.debug_logger.info("decide Settle Logic Start at %s" % base_time.strftime("%Y-%m-%d %H:%M:%S"))
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

                    self.updatePrice(current_price)

                    # if weekday == Saturday, we will settle one's position.
                    if weekday == 5 and hour >= 5:
                        self.result_logger.info("# weekend stl logic")
                        stl_flag = True

                    else:
                        pass
#                        stl_flag = self.decideReverseStl(stl_flag, base_time)
                        stl_flag = self.decideTrailLogic(stl_flag, self.ask_price, self.bid_price, base_time)

            else:
                pass

#            self.writeDebugLog(base_time, mode="stl")

            return stl_flag
        except:
            raise

    def decideReverseStl(self, stl_flag, base_time):
        if self.order_flag:
            hour = base_time.hour
            minutes = base_time.minute
            seconds = base_time.second
            current_price = (self.ask_price + self.bid_price) / 2

            if seconds < 10 and minutes == 0:
#                self.setReverseIndicator(base_time)
                if self.order_kind == "buy" and self.sma1h20 < self.sma1h100:
                    stl_flag = True
                elif self.order_kind == "sell" and self.sma1h20 > self.sma1h100:
                    stl_flag = True

            current_price = (self.ask_price + self.bid_price) / 2

            if self.order_kind == "buy" and current_price > self.upper_sigma_1h3:
                stl_flag = True
            elif self.order_kind == "sell" and current_price < self.lower_sigma_1h3:
                stl_flag = True

#            if seconds < 10:
#                original_stoploss = 0.5
#                #original_stoploss = 0.1
#                if self.order_kind == "buy":
#                    if (self.order_price - self.end_price_1m) > original_stoploss:
#                        stl_flag = True
#                elif self.order_kind == "sell":
#                    if (self.end_price_1m - self.order_price) > original_stoploss:
#                        stl_flag = True
#
#            if self.order_kind == "buy" and self.decidePerfectOrder() == "sell":
#                stl_flag = True
#                self.stl_logic = "reverse_perfect_order"
#            elif self.order_kind == "sell" and self.decidePerfectOrder() == "buy":
#                stl_flag = True
#                self.stl_logic = "reverse_perfect_order"
#
        #    if self.order_kind == "buy" and current_price > self.upper_sigma_1m25:
        #        stl_flag = True
  
        #    elif self.order_kind == "sell" and current_price < self.lower_sigma_1m25:
        #        stl_flag = True

        return stl_flag


    def decideBollingerCrossOver(self, flag):
        state = False
        if flag == "upper":
            for i in range(0, len(self.upper_sigma_5m2_list)):
                if self.max_price_5m_list[i] > self.upper_sigma_5m2_list[i]:
                    state = True

        elif flag == "lower":
            for i in range(0, len(self.lower_sigma_5m2_list)):
                if self.min_price_5m_list[i] < self.lower_sigma_5m2_list[i]:
                    state = True

        else:
            raise

        return state


    def decidePerfectOrder(self, span):
        direct = "pass"
        if span == "5m":
            if (self.sma5m20 > self.sma5m40 > self.sma5m80) and self.sma5m20_slope > 0 and self.sma5m40_slope > 0 and self.sma5m80_slope > 0:
                direct = "buy"
            elif (self.sma5m20 < self.sma5m40 < self.sma5m80) and self.sma5m20_slope < 0 and self.sma5m40_slope < 0 and self.sma5m80_slope < 0:
                direct = "sell"

        elif span == "1h":
            if (self.sma1h20 > self.sma1h40 > self.sma1h80) and self.sma1h20_slope > 0 and self.sma1h40_slope > 0 and self.sma1h80_slope > 0:
                direct = "buy"
            elif (self.sma1h20 < self.sma1h40 < self.sma1h80) and self.sma1h20_slope < 0 and self.sma1h40_slope < 0 and self.sma1h80_slope < 0:
                self.debug_logger.info("1h sell perfect_order")
                direct = "sell"

        return direct

    def decideSma(self, sma_value, current_price):
        direct = "pass"
        if current_price > sma_value:
            self.debug_logger.info("sma logic: buy")
            direct = "buy"

        elif current_price < sma_value:
            self.debug_logger.info("sma logic: sell")
            direct = "sell"

        return direct


    def decideEwma(self):
        flag = True
        if self.start_price_1d < self.end_price_1d:
            if self.start_price_1d < self.sma20_1d < self.end_price_1d:
                flag = False
        else:
            if self.end_price_1d < self.sma20_1d < self.start_price_1d:
                flag = False

        return flag 

    def decideReverseTrade(self, trade_flag, current_price, base_time):
        if trade_flag == "pass":
            hour = base_time.hour
            minutes = base_time.minute
            seconds = base_time.second
            if seconds < 10 and minutes % 5 == 0:
                self.setReverse5mIndicator(base_time)
            if seconds < 10 and minutes == 0:
                self.setReverse1hIndicator(base_time)
            if seconds < 10 and hour == 7:
                self.setReverseDailyIndicator(base_time)

            if 1 == 1:
                if 1 == 1:
                    if 1 == 1:
                        if self.sma1h100 < self.sma1h20 and self.decidePerfectOrder("1h") == "buy" and self.first_trade_flag != "buy" and self.order_kind != "buy":
                            self.debug_logger.info("first trade flag: buy at %s" % base_time)
                            self.first_trade_flag = "buy"
                            self.perfect_order_buycount = self.perfect_order_buycount + 1
                            self.first_trade_time = base_time
                            self.first_trade_price = current_price

                            self.second_trade_flag = False
                            self.third_trade_flag = "pass"
    
                        elif self.sma1h100 > self.sma1h20 and self.decidePerfectOrder("1h") == "sell" and self.first_trade_flag != "sell" and self.order_kind != "sell":
                            self.debug_logger.info("first trade flag: sell at %s" % base_time)
                            self.perfect_order_sellcount = self.perfect_order_sellcount + 1
                            self.first_trade_flag = "sell"
                            self.first_trade_time = base_time
                            self.first_trade_price = current_price

                            self.second_trade_flag = False
                            self.third_trade_flag = "pass"
                   
                    if 1 == 1:
                        if self.first_trade_flag == "buy":
                            if self.decidePerfectOrder("5m") != "buy" and self.second_trade_flag == False:
                                self.debug_logger.info("second trade flag: True at %s" % base_time)
                                self.second_trade_time = base_time
                                self.second_trade_flag = True
                                self.second_trade_price = current_price

                        elif self.first_trade_flag == "sell":
                            if self.decidePerfectOrder("5m") != "sell" and self.second_trade_flag == False:
                                self.debug_logger.info("second trade flag: True at %s" % base_time)
                                self.second_trade_time = base_time
                                self.second_trade_flag = True
                                self.second_trade_price = current_price

                    if self.first_trade_flag == "buy" and self.second_trade_flag and self.decidePerfectOrder("5m") == "buy":
                        self.third_trade_flag = "buy"
                        self.third_trade_time = base_time
                        self.third_trade_price = current_price

                    elif self.first_trade_flag == "sell" and self.second_trade_flag and self.decidePerfectOrder("5m") == "sell":
                        self.third_trade_flag = "sell"
                        self.third_trade_time = base_time
                        self.third_trade_price = current_price

                    #if self.first_trade_flag == "buy" and self.second_trade_flag and self.third_trade_flag == "buy" and current_price < self.lower_sigma_5m25:
                    if self.first_trade_flag == "buy" and self.second_trade_flag and self.third_trade_flag == "buy":
                        self.first_trade_flag = "pass"
                        self.second_trade_flag = False
                        self.third_trade_flag = "pass"
                        trade_flag = "buy"

                    #elif self.first_trade_flag == "sell" and self.second_trade_flag and self.third_trade_flag == "sell" and current_price > self.upper_sigma_5m25:
                    elif self.first_trade_flag == "sell" and self.second_trade_flag and self.third_trade_flag == "sell":
                        self.first_trade_flag = "pass"
                        self.second_trade_flag = False
                        self.third_trade_flag = "pass"
                        trade_flag = "sell"

        return trade_flag

    def updatePrice(self, current_price):
        if self.log_max_price == 0:
            self.log_max_price = current_price
        elif self.log_max_price < current_price:
            self.log_max_price = current_price
        if self.log_min_price == 0:
            self.log_min_price = current_price
        elif self.log_min_price > current_price:
            self.log_min_price = current_price

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
        #self.algorithm = ""
        self.log_max_price = 0
        self.log_min_price = 0
        #self.first_trade_flag = "pass"
        #self.second_trade_flag = False
        self.stl_first_flag = False
        self.buy_flag = False
        self.sell_flag = False
        self.perfect_order_buycount = 0
        self.perfect_order_sellcount = 0
        self.trail_third_flag = False
        self.stl_logic = "none"
        super(TrendReverseAlgo, self).resetFlag()


    def setReverse5mIndicator(self, base_time):
        ### get 5m dataset
        target_time = base_time - timedelta(minutes=5)

        dataset = getBollingerWrapper(target_time, self.instrument, table_type="5m", window_size=28, connector=self.mysql_connector, sigma_valiable=2.5, length=0)
        self.upper_sigma_5m25 = dataset["upper_sigmas"][-1]
        self.lower_sigma_5m25 = dataset["lower_sigmas"][-1]

        dataset = getBollingerWrapper(target_time, self.instrument, table_type="5m", window_size=20, connector=self.mysql_connector, sigma_valiable=2, length=5)
        self.sma5m20 = dataset["base_lines"][-1]
        self.sma5m20_before = dataset["base_lines"][-2]

        dataset = getBollingerWrapper(target_time, self.instrument, table_type="5m", window_size=40, connector=self.mysql_connector, sigma_valiable=2, length=5)
        self.sma5m40 = dataset["base_lines"][-1]
        self.sma5m40_before = dataset["base_lines"][-2]

        dataset = getBollingerWrapper(target_time, self.instrument, table_type="5m", window_size=80, connector=self.mysql_connector, sigma_valiable=2, length=5)
        self.sma5m80 = dataset["base_lines"][-1]
        self.sma5m80_before = dataset["base_lines"][-2]

        self.sma5m20_slope = getSlope([self.sma5m20_before, self.sma5m20])
        self.sma5m40_slope = getSlope([self.sma5m40_before, self.sma5m40])
        self.sma5m80_slope = getSlope([self.sma5m80_before, self.sma5m80])

    def setReverse1hIndicator(self, base_time):
        ### get 1h dataset
        target_time = base_time - timedelta(hours=1)
        dataset = getBollingerWrapper(target_time, self.instrument, table_type="1h", window_size=28, connector=self.mysql_connector, sigma_valiable=3, length=0)
        self.upper_sigma_1h3 = dataset["upper_sigmas"][-1]
        self.lower_sigma_1h3 = dataset["lower_sigmas"][-1]

        dataset = getBollingerWrapper(target_time, self.instrument, table_type="1h", window_size=100, connector=self.mysql_connector, sigma_valiable=2, length=0)
        self.sma1h100 = dataset["base_lines"][-1]

        dataset = getBollingerWrapper(target_time, self.instrument, table_type="1h", window_size=20, connector=self.mysql_connector, sigma_valiable=2, length=1)
        self.sma1h20 = dataset["base_lines"][-1]
        self.sma1h20_before = dataset["base_lines"][-2]
        self.sma1h20_slope = getSlope([self.sma1h20_before, self.sma1h20])


        dataset = getBollingerWrapper(target_time, self.instrument, table_type="1h", window_size=40, connector=self.mysql_connector, sigma_valiable=2, length=1)
        self.sma1h40 = dataset["base_lines"][-1]
        self.sma1h40_before = dataset["base_lines"][-2]
        self.sma1h40_slope = getSlope([self.sma1h40_before, self.sma1h40])


        dataset = getBollingerWrapper(target_time, self.instrument, table_type="1h", window_size=80, connector=self.mysql_connector, sigma_valiable=2, length=1)
        self.sma1h80 = dataset["base_lines"][-1]
        self.sma1h80_before = dataset["base_lines"][-2]
        self.sma1h80_slope = getSlope([self.sma1h80_before, self.sma1h80])

    def setReverseDailyIndicator(self, base_time):
        ### get daily dataset
        target_time = base_time - timedelta(days=1)
        sql = "select max_price, min_price, start_price, end_price from %s_%s_TABLE where insert_time < \'%s\' order by insert_time desc limit 1" % (self.instrument, "day", target_time) 
        response = self.mysql_connector.select_sql(sql)
        self.max_price_1d = response[0][0]
        self.min_price_1d = response[0][1]
        self.start_price_1d = response[0][2]
        self.end_price_1d = response[0][3]

        dataset = getBollingerWrapper(target_time, self.instrument, table_type="day", window_size=28, connector=self.mysql_connector, sigma_valiable=2, length=0)
        self.upper_sigma_1d2 = dataset["upper_sigmas"][-1]
        self.lower_sigma_1d2 = dataset["lower_sigmas"][-1]

        dataset = getBollingerWrapper(target_time, self.instrument, table_type="day", window_size=20, connector=self.mysql_connector, sigma_valiable=2, length=0)

        self.sma20_1d = dataset["base_lines"][-1]


    def decideTrailLogic(self, stl_flag, current_ask_price, current_bid_price, base_time):
        minutes = base_time.minute
        seconds = base_time.second

        if minutes % 5 == 0 and seconds < 10:
            order_price = self.getOrderPrice()
            first_take_profit = 0.5
            second_take_profit = 1.0
            third_take_profit = 2.0

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
                if self.order_price > current_bid_price:
                    self.result_logger.info("# Execute FirstTrail Stop")
                    stl_flag = True
            elif self.trail_flag == True and self.order_kind == "sell":
                if self.order_price < current_ask_price :
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
                if (self.order_price + 0.5) > current_bid_price:
                    self.result_logger.info("# Execute SecondTrail Stop")
                    stl_flag = True
            elif self.trail_second_flag == True and self.order_kind == "sell":
                if (self.order_price - 0.5) < current_ask_price :
                    self.result_logger.info("# Execute SecondTrail Stop")
                    stl_flag = True

            # third trailing stop logic
            if self.order_kind == "buy":
                if (current_bid_price - order_price) > third_take_profit:
                    self.trail_third_flag = True
            elif self.order_kind == "sell":
                if (order_price - current_ask_price) > third_take_profit:
                    self.trail_third_flag = True

            if self.trail_third_flag == True and self.order_kind == "buy":
                if (self.order_price + 1.0) > current_bid_price:
                    self.result_logger.info("# Execute SecondTrail Stop")
                    stl_flag = True
            elif self.trail_third_flag == True and self.order_kind == "sell":
                if (self.order_price - 1.0) < current_ask_price :
                    self.result_logger.info("# Execute SecondTrail Stop")
                    stl_flag = True

        return stl_flag


# write log function
    def writeDebugLog(self, base_time, mode):
        self.debug_logger.info("%s: %s Logic START" % (base_time, mode))
        self.debug_logger.info("# self.start_price_1m=%s" % self.start_price_1m)
        self.debug_logger.info("# self.end_price_1m=%s" % self.end_price_1m)
        self.debug_logger.info("# self.slope_1m=%s" % self.slope_1m)
        self.debug_logger.info("#############################################")

    def entryLogWrite(self, base_time):
        self.result_logger.info("#######################################################")
        self.result_logger.info("# in %s Algorithm" % self.algorithm)
        self.result_logger.info("# first_trade_time=%s" % self.first_trade_time)
        self.result_logger.info("# second_trade_time= %s" % self.second_trade_time)
        self.result_logger.info("# third_trade_time= %s" % self.third_trade_time)
        self.result_logger.info("# EXECUTE ORDER at %s" % base_time)
        self.result_logger.info("# first_trade_price=%s" % self.first_trade_price)
        self.result_logger.info("# second_trade_price= %s" % self.second_trade_price)
        self.result_logger.info("# third_trade_price= %s" % self.third_trade_price)
        self.result_logger.info("# ORDER_PRICE=%s, TRADE_FLAG=%s" % (self.order_price, self.order_kind))
        self.result_logger.info("# self.upper_sigma_5m25=%s" % self.upper_sigma_5m25)
        self.result_logger.info("# self.lower_sigma_5m25=%s" % self.lower_sigma_5m25)
        self.result_logger.info("# self.upper_sigma_1h3=%s" % self.upper_sigma_1h3)
        self.result_logger.info("# self.lower_sigma_1h3=%s" % self.lower_sigma_1h3)
        self.result_logger.info("# self.sma5m20=%s" % self.sma5m20)
        self.result_logger.info("# self.sma5m40=%s" % self.sma5m40)
        self.result_logger.info("# self.sma5m80=%s" % self.sma5m80)
        self.result_logger.info("# self.sma5m20_slope=%s" % self.sma5m20_slope)
        self.result_logger.info("# self.sma5m40_slope=%s" % self.sma5m40_slope)
        self.result_logger.info("# self.sma5m80_slope=%s" % self.sma5m80_slope)
        self.result_logger.info("# self.sma1h100=%s" % self.sma1h100)
        self.result_logger.info("# self.sma1h20=%s" % self.sma1h20)
        self.result_logger.info("# self.sma1h40=%s" % self.sma1h40)
        self.result_logger.info("# self.sma1h80=%s" % self.sma1h80)
        self.result_logger.info("# self.sma1h20_slope=%s" % self.sma1h20_slope)
        self.result_logger.info("# self.sma1h40_slope=%s" % self.sma1h40_slope)
        self.result_logger.info("# self.sma1h80_slope=%s" % self.sma1h80_slope)

    def settlementLogWrite(self, profit, base_time, stl_price, stl_method):
        self.result_logger.info("# %s at %s" % (stl_method, base_time))
        self.result_logger.info("# self.ask_price=%s" % self.ask_price)
        self.result_logger.info("# self.bid_price=%s" % self.bid_price)
        self.result_logger.info("# self.log_max_price=%s" % self.log_max_price)
        self.result_logger.info("# self.log_min_price=%s" % self.log_min_price)
        self.result_logger.info("# self.stl_logic=%s" % self.stl_logic)
        self.result_logger.info("# STL_PRICE=%s" % stl_price)
        self.result_logger.info("# PROFIT=%s" % profit)
