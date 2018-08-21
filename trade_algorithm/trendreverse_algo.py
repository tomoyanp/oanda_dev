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
from get_indicator import getBollingerWrapper, getVolatilityPriceWrapper, getHighlowPriceWrapper, getLastPriceWrapper, getWeekStartPrice, getRsiWrapper
from trade_calculator import decideLowExceedPrice, decideLowSurplusPrice, decideHighExceedPrice, decideHighSurplusPrice, decideVolatility, decideDailyVolatilityPrice
from mysql_connector import MysqlConnector
from datetime import datetime, timedelta
from logging import getLogger, FileHandler, DEBUG

import traceback

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

                if seconds < 10 and minutes % 5 == 0:
                    self.setReverse5mIndicator(base_time)
                if seconds < 10 and minutes == 0:
                    self.setReverse1hIndicator(base_time)
                if seconds < 10 and hour == 7:
                    self.setReverseDailyIndicator(base_time)


                # if weekday == Saturday, we will have no entry.
                if weekday == 5 and hour >= 5:
                    trade_flag = "pass"
                    self.buy_count = 0
                    self.sell_count = 0

                else:
                    # if spread rate is greater than 0.5, we will have no entry
                    if (self.ask_price - self.bid_price) >= 0.05:
                        pass

                    else:
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
                        #stl_flag = self.decideReverseStl(stl_flag, base_time)
                        #stl_flag = self.decideTrailLogic(stl_flag, self.ask_price, self.bid_price, base_time)

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

            if self.algorithm == "perfect_order":
                if self.order_kind == "buy" and current_price > self.upper_sigma_1h1 and self.stl_first_flag == False:
                    self.stl_first_flag = True
                    self.writeDebugStlLog(base_time, stl_flag)
                elif self.order_kind == "sell" and current_price < self.lower_sigma_1h1 and self.stl_first_flag == False:
                    self.stl_first_flag = True
                    self.writeDebugStlLog(base_time, stl_flag)
               
                if self.order_kind == "buy" and self.stl_first_flag and current_price < self.sma1h40:
                    stl_flag = True
                    self.writeDebugStlLog(base_time, stl_flag)
                elif self.order_kind == "sell" and self.stl_first_flag and current_price > self.sma1h40:
                    stl_flag = True
                    self.writeDebugStlLog(base_time, stl_flag)

            elif self.algorithm == "reverse_order":         
                reverse_stoploss_rate = 0.3

                if self.order_kind == "buy" and current_price > self.upper_sigma_1h3:
                    stl_flag = True
                    self.writeDebugStlLog(base_time, stl_flag)
                elif self.order_kind == "sell" and current_price < self.lower_sigma_1h3:
                    stl_flag = True
                    self.writeDebugStlLog(base_time, stl_flag)
               
                if self.order_kind == "buy" and current_price < (self.order_price - reverse_stoploss_rate):
                    stl_flag = True
                    self.writeDebugStlLog(base_time, stl_flag)
                elif self.order_kind == "sell" and current_price > (self.order_price + reverse_stoploss_rate):
                    stl_flag = True
                    self.writeDebugStlLog(base_time, stl_flag)


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


    def decidePerfectOrder(self, span, slope_flag):
        direct = "pass"
        if span == "5m":
            if (self.sma5m20 > self.sma5m40 > self.sma5m80):
                if slope_flag:
                    if (self.sma5m20_slope > 0 and self.sma5m40_slope > 0 and self.sma5m80_slope > 0):
                        direct = "buy"
                else:
                    direct = "buy"
            elif (self.sma5m20 < self.sma5m40 < self.sma5m80):
                if slope_flag:
                    if (self.sma5m20_slope < 0 and self.sma5m40_slope < 0 and self.sma5m80_slope < 0):
                        direct = "sell"
                else:
                    direct = "sell"

        elif span == "1h":
            if (self.sma1h20 > self.sma1h40 > self.sma1h80):
                if slope_flag:
                    if (self.sma1h20_slope > 0 and self.sma1h40_slope > 0 and self.sma1h80_slope > 0):
                        direct = "buy"
                else:
                    direct = "buy"
            elif (self.sma1h20 < self.sma1h40 < self.sma1h80):
                if slope_flag:
                    if (self.sma1h20_slope < 0 and self.sma1h40_slope < 0 and self.sma1h80_slope < 0):
                        direct = "sell"
                else:
                    direct = "sell"

        return direct

    def decideSma(self, sma_value, current_price):
        direct = "pass"
        if current_price > sma_value:
            direct = "buy"

        elif current_price < sma_value:
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
            if ((self.min_price < self.sma1d20 < self.max_price) == True and (self.thisday_min < self.sma1d20 < self.thisday_max) == True) or (40 < self.rsi_value < 70 and (self.upper_sigma_1d3 - self.lower_sigma_1d3) < 10):
#                if self.order_flag:
                if 1 == 1:
                    pass
                else:
                    if current_price < self.lower_sigma_1h25 and self.first_trade_flag != "buy" and self.order_kind != "buy":
                        self.first_trade_flag = "buy"
                        self.first_trade_time = base_time
                        self.first_trade_price = current_price
                        self.second_trade_flag = False
                        self.third_trade_flag = "pass"
                        self.writeDebugTradeLog(base_time, trade_flag)
                    elif current_price > self.upper_sigma_1h25 and self.first_trade_flag != "sell" and self.order_kind != "sell":
                        self.first_trade_flag = "sell"
                        self.first_trade_time = base_time
                        self.first_trade_price = current_price
                        self.second_trade_flag = False
                        self.third_trade_flag = "pass"
                        self.writeDebugTradeLog(base_time, trade_flag)
    
                    if self.first_trade_flag == "buy" and self.decidePerfectOrder("5m", slope_flag=True) == "buy":
                        trade_flag = "buy"
                        self.algorithm = "reverse_order"
                        self.writeDebugTradeLog(base_time, trade_flag)
    
                        self.first_trade_flag = "pass"
                        self.second_trade_flag = False
                        self.third_trade_flag = "pass"
    
                    elif self.first_trade_flag == "sell" and self.decidePerfectOrder("5m", slope_flag=True) == "sell":
                        trade_flag = "sell"
                        self.algorithm = "reverse_order"
                        self.writeDebugTradeLog(base_time, trade_flag)
    
                        self.first_trade_flag = "pass"
                        self.second_trade_flag = False
                        self.third_trade_flag = "pass"

            else:
                if self.decidePerfectOrder("1h", slope_flag=False) == "buy" and self.first_trade_flag != "buy" and self.order_kind != "buy":
                #if self.decidePerfectOrder("1h", slope_flag=True) == "buy" and self.first_trade_flag != "buy" and self.order_kind != "buy":
                    self.first_trade_flag = "buy"
                    self.perfect_order_buycount = self.perfect_order_buycount + 1
                    self.first_trade_time = base_time
                    self.first_trade_price = current_price
                    self.second_trade_flag = False
                    self.third_trade_flag = "pass"
                    self.writeDebugTradeLog(base_time, trade_flag)

                elif self.decidePerfectOrder("1h", slope_flag=False) == "sell" and self.first_trade_flag != "sell" and self.order_kind != "sell":
                #elif self.decidePerfectOrder("1h", slope_flag=True) == "sell" and self.first_trade_flag != "sell" and self.order_kind != "sell":
                    self.perfect_order_sellcount = self.perfect_order_sellcount + 1
                    self.first_trade_flag = "sell"
                    self.first_trade_time = base_time
                    self.first_trade_price = current_price
                    self.second_trade_flag = False
                    self.third_trade_flag = "pass"
                    self.writeDebugTradeLog(base_time, trade_flag)
               
                if self.first_trade_flag == "buy":
                    if current_price < self.sma1h20 and self.second_trade_flag == False:
                        self.second_trade_time = base_time
                        self.second_trade_flag = True
                        self.second_trade_price = current_price
                        self.writeDebugTradeLog(base_time, trade_flag)

                elif self.first_trade_flag == "sell":
                    if current_price > self.sma1h20 and self.second_trade_flag == False:
                        self.second_trade_time = base_time
                        self.second_trade_flag = True
                        self.second_trade_price = current_price
                        self.writeDebugTradeLog(base_time, trade_flag)


                #if self.first_trade_flag == "buy" and self.second_trade_flag and self.decidePerfectOrder("5m", slope_flag=True) == "buy":
                if self.first_trade_flag == "buy" and self.second_trade_flag and self.decidePerfectOrder("5m", slope_flag=False) == "buy":
                    self.third_trade_flag = "buy"
                    self.third_trade_time = base_time
                    self.third_trade_price = current_price
                    self.writeDebugTradeLog(base_time, trade_flag)

                #elif self.first_trade_flag == "sell" and self.second_trade_flag and self.decidePerfectOrder("5m", slope_flag=True) == "sell":
                elif self.first_trade_flag == "sell" and self.second_trade_flag and self.decidePerfectOrder("5m", slope_flag=False) == "sell":
                    self.third_trade_flag = "sell"
                    self.third_trade_time = base_time
                    self.third_trade_price = current_price
                    self.writeDebugTradeLog(base_time, trade_flag)


                if self.first_trade_flag == "buy" and self.second_trade_flag and self.third_trade_flag == "buy":
                    trade_flag = "buy"
                    self.first_trade_flag = "pass"
                    self.second_trade_flag = False
                    self.third_trade_flag = "pass"
                    self.algorithm = "perfect_order"
                    self.writeDebugTradeLog(base_time, trade_flag)

                elif self.first_trade_flag == "sell" and self.second_trade_flag and self.third_trade_flag == "sell":
                    trade_flag = "sell"
                    self.first_trade_flag = "pass"
                    self.second_trade_flag = False
                    self.third_trade_flag = "pass"
                    self.algorithm = "perfect_order"
                    self.writeDebugTradeLog(base_time, trade_flag)

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
        try:
            ### get 5m dataset
            target_time = base_time - timedelta(minutes=5)
    
            dataset = getBollingerWrapper(target_time, self.instrument, table_type="5m", window_size=21, connector=self.mysql_connector, sigma_valiable=2.5, length=0)
            self.upper_sigma_5m25 = dataset["upper_sigmas"][-1]
            self.lower_sigma_5m25 = dataset["lower_sigmas"][-1]
    
            dataset = getBollingerWrapper(target_time, self.instrument, table_type="5m", window_size=20, connector=self.mysql_connector, sigma_valiable=2, length=5)
            self.sma5m20 = dataset["base_lines"][-1]
            self.sma5m20_before = dataset["base_lines"][-5]
    
            dataset = getBollingerWrapper(target_time, self.instrument, table_type="5m", window_size=40, connector=self.mysql_connector, sigma_valiable=2, length=5)
            self.sma5m40 = dataset["base_lines"][-1]
            self.sma5m40_before = dataset["base_lines"][-5]
    
            dataset = getBollingerWrapper(target_time, self.instrument, table_type="5m", window_size=80, connector=self.mysql_connector, sigma_valiable=2, length=5)
            self.sma5m80 = dataset["base_lines"][-1]
            self.sma5m80_before = dataset["base_lines"][-5]
    
    #        self.sma5m20_slope = getSlope([self.sma5m20_before, self.sma5m20])
    #        self.sma5m40_slope = getSlope([self.sma5m40_before, self.sma5m40])
    #        self.sma5m80_slope = getSlope([self.sma5m80_before, self.sma5m80])
    
        except Exception as e:
            message = traceback.format_exc()
            self.debug_logger.info("# %s" % base_time)
            self.debug_logger.info("# %s" % message)

    def getStartTime(self, base_time):
        hour = base_time.hour
        week = base_time.weekday()

        base_ftime = base_time.strftime("%Y-%m-%d 07:00:00")
        base_time = datetime.strptime(base_ftime, "%Y-%m-%d %H:%M:%S")

        if hour < 9: 
            for i in range(1, 5):
                tmp_time = base_time - timedelta(days=i)
                if decideMarket(tmp_time):
                    break
            base_time = tmp_time

        else:
            pass

        return base_time

    def setReverse1hIndicator(self, base_time):
        try:
            ### get 1h dataset
            target_time = base_time - timedelta(hours=1)
    
            dataset = getBollingerWrapper(target_time, self.instrument, table_type="1h", window_size=21, connector=self.mysql_connector, sigma_valiable=1, length=0)
            self.upper_sigma_1h1 = dataset["upper_sigmas"][-1]
            self.lower_sigma_1h1 = dataset["lower_sigmas"][-1]
    
            dataset = getBollingerWrapper(target_time, self.instrument, table_type="1h", window_size=21, connector=self.mysql_connector, sigma_valiable=2.5, length=0)
            self.upper_sigma_1h25 = dataset["upper_sigmas"][-1]
            self.lower_sigma_1h25 = dataset["lower_sigmas"][-1]
    
            dataset = getBollingerWrapper(target_time, self.instrument, table_type="1h", window_size=21, connector=self.mysql_connector, sigma_valiable=3, length=0)
            self.upper_sigma_1h3 = dataset["upper_sigmas"][-1]
            self.lower_sigma_1h3 = dataset["lower_sigmas"][-1]
    
            dataset = getBollingerWrapper(target_time, self.instrument, table_type="1h", window_size=100, connector=self.mysql_connector, sigma_valiable=2, length=0)
            self.sma1h100 = dataset["base_lines"][-1]
    
            dataset = getBollingerWrapper(target_time, self.instrument, table_type="1h", window_size=20, connector=self.mysql_connector, sigma_valiable=2, length=10)
            self.sma1h20 = dataset["base_lines"][-1]
            self.sma1h20_before = dataset["base_lines"][-10]
            self.sma1h20_slope = getSlope([self.sma1h20_before, self.sma1h20])
    
    
            dataset = getBollingerWrapper(target_time, self.instrument, table_type="1h", window_size=40, connector=self.mysql_connector, sigma_valiable=2, length=10)
            self.sma1h40 = dataset["base_lines"][-1]
            self.sma1h40_before = dataset["base_lines"][-10]
            self.sma1h40_slope = getSlope([self.sma1h40_before, self.sma1h40])
    
    
            dataset = getBollingerWrapper(target_time, self.instrument, table_type="1h", window_size=80, connector=self.mysql_connector, sigma_valiable=2, length=10)
            self.sma1h80 = dataset["base_lines"][-1]
            self.sma1h80_before = dataset["base_lines"][-10]
            self.sma1h80_slope = getSlope([self.sma1h80_before, self.sma1h80])
    
    
            start_time = self.getStartTime(base_time)
            sql = "select max_price, min_price from %s_%s_TABLE where insert_time > \'%s\' and insert_time < \'%s\'" % (self.instrument, "1h", start_time, base_time)
            response = self.mysql_connector.select_sql(sql)
            tmp_max = []
            tmp_min = []
            for res in response:
                tmp_max.append(res[0])
                tmp_min.append(res[1])
            
            self.thisday_max = max(tmp_max)
            self.thisday_min = min(tmp_min)
    
        except Exception as e:
            message = traceback.format_exc()
            self.debug_logger.info("# %s" % base_time)
            self.debug_logger.info("# %s" % message)

    def setReverseDailyIndicator(self, base_time):
        try:
            ### get daily dataset
            target_time = base_time - timedelta(days=1)
            sql = "select max_price, min_price, start_price, end_price from %s_%s_TABLE where insert_time < \'%s\' order by insert_time desc limit 1" % (self.instrument, "day", target_time) 
            response = self.mysql_connector.select_sql(sql)
            self.max_price_1d = response[0][0]
            self.min_price_1d = response[0][1]
            self.start_price_1d = response[0][2]
            self.end_price_1d = response[0][3]
    
            dataset = getBollingerWrapper(target_time, self.instrument, table_type="day", window_size=21, connector=self.mysql_connector, sigma_valiable=3, length=0)
            self.upper_sigma_1d3 = dataset["upper_sigmas"][-1]
            self.lower_sigma_1d3 = dataset["lower_sigmas"][-1]
    
    
            dataset = getBollingerWrapper(target_time, self.instrument, table_type="day", window_size=21, connector=self.mysql_connector, sigma_valiable=1, length=0)
            self.upper_sigma_1d1 = dataset["upper_sigmas"][-1]
            self.lower_sigma_1d1 = dataset["lower_sigmas"][-1]
    
            dataset = getBollingerWrapper(target_time, self.instrument, table_type="day", window_size=20, connector=self.mysql_connector, sigma_valiable=2, length=0)
            self.sma1d20 = dataset["base_lines"][-1]
    
            sql = "select max_price, min_price from %s_%s_TABLE where insert_time < '%s' order by insert_time desc limit 1" % (self.instrument, "day", target_time)
            response = self.mysql_connector.select_sql(sql)
            self.max_price = response[0][0]
            self.min_price = response[0][1]
    
            self.rsi_value = getRsiWrapper(target_time, self.instrument, "day", self.mysql_connector, 14)

        except Exception as e:
            message = traceback.format_exc()
            self.debug_logger.info("# %s" % base_time)
            self.debug_logger.info("# %s" % message)
            

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
             
#            # second trailing stop logic
#            if self.order_kind == "buy":
#                if (current_bid_price - order_price) > second_take_profit:
#                    self.trail_second_flag = True
#            elif self.order_kind == "sell":
#                if (order_price - current_ask_price) > second_take_profit:
#                    self.trail_second_flag = True
#
#            if self.trail_second_flag == True and self.order_kind == "buy":
#                if (self.order_price + 0.5) > current_bid_price:
#                    self.result_logger.info("# Execute SecondTrail Stop")
#                    stl_flag = True
#            elif self.trail_second_flag == True and self.order_kind == "sell":
#                if (self.order_price - 0.5) < current_ask_price :
#                    self.result_logger.info("# Execute SecondTrail Stop")
#                    stl_flag = True
#
#            # third trailing stop logic
#            if self.order_kind == "buy":
#                if (current_bid_price - order_price) > third_take_profit:
#                    self.trail_third_flag = True
#            elif self.order_kind == "sell":
#                if (order_price - current_ask_price) > third_take_profit:
#                    self.trail_third_flag = True
#
#            if self.trail_third_flag == True and self.order_kind == "buy":
#                if (self.order_price + 1.0) > current_bid_price:
#                    self.result_logger.info("# Execute SecondTrail Stop")
#                    stl_flag = True
#            elif self.trail_third_flag == True and self.order_kind == "sell":
#                if (self.order_price - 1.0) < current_ask_price :
#                    self.result_logger.info("# Execute SecondTrail Stop")
#                    stl_flag = True

        return stl_flag


# write log function
    def writeDebugTradeLog(self, base_time, trade_flag):
        self.debug_logger.info("# %s "% base_time)
        self.debug_logger.info("# self.first_trade_flag= %s" % self.first_trade_flag)
        self.debug_logger.info("# self.second_trade_flag=%s" % self.second_trade_flag)
        self.debug_logger.info("# self.third_trade_flag= %s" % self.third_trade_flag)
        self.debug_logger.info("# trade_flag=            %s" % trade_flag)
        self.debug_logger.info("#############################################")

    def writeDebugStlLog(self, base_time, stl_flag):
        self.debug_logger.info("# %s "% base_time)
        self.debug_logger.info("# self.stl_first_flag=%s" % self.stl_first_flag)
        self.debug_logger.info("# stl_flag=           %s" % stl_flag)
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
#        self.result_logger.info("# self.sma5m20_slope=%s" % self.sma5m20_slope)
#        self.result_logger.info("# self.sma5m40_slope=%s" % self.sma5m40_slope)
#        self.result_logger.info("# self.sma5m80_slope=%s" % self.sma5m80_slope)
        self.result_logger.info("# self.sma1h100=%s" % self.sma1h100)
        self.result_logger.info("# self.sma1h20=%s" % self.sma1h20)
        self.result_logger.info("# self.sma1h40=%s" % self.sma1h40)
        self.result_logger.info("# self.sma1h80=%s" % self.sma1h80)
        self.result_logger.info("# self.sma1h20_slope=%s" % self.sma1h20_slope)
        self.result_logger.info("# self.sma1h40_slope=%s" % self.sma1h40_slope)
        self.result_logger.info("# self.sma1h80_slope=%s" % self.sma1h80_slope)
        self.result_logger.info("# self.before_max=%s" % self.max_price)
        self.result_logger.info("# self.before_min=%s" % self.min_price)
        self.result_logger.info("# self.thisday_max=%s" % self.thisday_max)
        self.result_logger.info("# self.thisday_min=%s" % self.thisday_min)
        self.result_logger.info("# self.sma1d20=%s" % self.sma1d20)
        self.result_logger.info("# self.upper_sigma_1d3=%s" % self.upper_sigma_1d3)
        self.result_logger.info("# self.lower_sigma_1d3=%s" % self.lower_sigma_1d3)
        self.result_logger.info("# self.upper_sigma_1d1=%s" % self.upper_sigma_1d1)
        self.result_logger.info("# self.lower_sigma_1d1=%s" % self.lower_sigma_1d1)
        self.result_logger.info("# self.rsi_value=%s" % self.rsi_value)

        if ((self.min_price < self.sma1d20 < self.max_price) == True and (self.thisday_min < self.sma1d20 < self.thisday_max) == True):
            self.result_logger.info("self.sma1d20_logic=TRUE")
        else:
            self.result_logger.info("self.sma1d20_logic=FALSE")

        if (40 < self.rsi_value < 70 and (self.upper_sigma_1d3 - self.lower_sigma_1d3) < 10):
            self.result_logger.info("self.rsi_bollinger_logic=TRUE")
        else:
            self.result_logger.info("self.rsi_bollinger_logic=FALSE")

    def settlementLogWrite(self, profit, base_time, stl_price, stl_method):
        self.result_logger.info("# %s at %s" % (stl_method, base_time))
        self.result_logger.info("# self.ask_price=%s" % self.ask_price)
        self.result_logger.info("# self.bid_price=%s" % self.bid_price)
        self.result_logger.info("# self.log_max_price=%s" % self.log_max_price)
        self.result_logger.info("# self.log_min_price=%s" % self.log_min_price)
        self.result_logger.info("# self.stl_logic=%s" % self.stl_logic)
        self.result_logger.info("# STL_PRICE=%s" % stl_price)
        self.result_logger.info("# PROFIT=%s" % profit)
