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
        self.first_trade_time = base_time
        self.stl_first_flag = False
        self.buy_flag = False
        self.sell_flag = False
        self.setReverseIndicator(base_time)

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
                        self.debug_logger.info("# self.order_flag=%s" % self.order_flag)
                        self.debug_logger.info("# trade_flag=%s" % trade_flag)

                if trade_flag != "pass" and self.order_flag:
                    self.debug_logger.info("# allovertheworld logic")
                    self.debug_logger.info("# trade_flag=%s" % trade_flag)
                    self.debug_logger.info("# self.order_flag=%s" % self.order_flag)
                    if trade_flag == "buy" and self.order_kind == "buy":
                        trade_flag = "pass"
                    elif trade_flag == "sell" and self.order_kind == "sell":
                        trade_flag = "pass"
                    else:
                        self.algorithm = self.algorithm + " by allovertheworld"
                        #self.result_logger.info("# execute all over the world at TrendReverseAlgo")

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

                    self.updatePrice(current_price)

                    # if weekday == Saturday, we will settle one's position.
                    if weekday == 5 and hour >= 5:
                        self.result_logger.info("# weekend stl logic")
                        stl_flag = True

                    else:
                        stl_flag = self.decideReverseStl(stl_flag, base_time)
                        #stl_flag = self.decideTrailLogic(stl_flag, self.ask_price, self.bid_price, base_time)

            else:
                pass

            self.writeDebugLog(base_time, mode="stl")

            return stl_flag
        except:
            raise

    def decideReverseStl(self, stl_flag, base_time):
        if self.order_flag:
            hour = base_time.hour
            minutes = base_time.minute
            seconds = base_time.second
            current_price = (self.ask_price + self.bid_price) / 2

            self.setReverseIndicator(base_time)
            if seconds < 10:
                original_stoploss = 0.5
                #original_stoploss = 0.1
                if self.order_kind == "buy":
                    if (self.order_price - self.end_price_1m) > original_stoploss:
                        stl_flag = True
                elif self.order_kind == "sell":
                    if (self.end_price_1m - self.order_price) > original_stoploss:
                        stl_flag = True

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
            

    def decideReverseTrade(self, trade_flag, current_price, base_time):
#        if trade_flag == "pass" and self.order_flag != True:
        if trade_flag == "pass" and self.order_flag == False:
            hour = base_time.hour
            minutes = base_time.minute
            seconds = base_time.second
            if seconds < 10 and hour != 6:
                self.setReverseIndicator(base_time)
            if 1 == 1:
                if 1 == 1:
                    #if self.first_trade_flag == "pass":
                    if 1 == 1:
                        if (self.sma5m20 > self.sma5m40 > self.sma5m80)  and (self.ask_price - self.bid_price) < 0.1 and current_price > self.sma5m40:
                            self.first_trade_flag = "buy"
                            self.first_trade_time = base_time
    
                        elif (self.sma5m20 < self.sma5m40 < self.sma5m80) and (self.ask_price - self.bid_price) < 0.1 and current_price < self.sma5m40:
                            self.first_trade_flag = "sell"
                            self.first_trade_time = base_time
                        else:
                            self.first_trade_flag = "pass"
                            self.sell_flag = False
                            self.buy_flag = False
                   
                    #if seconds < 10:
                    if 1 == 1:
                        #if self.first_trade_flag == "buy" and self.first_trade_time + timedelta(minutes=1) < base_time:
                        if self.first_trade_flag == "buy" and self.buy_flag == False and self.sell_flag == False:
                            if current_price < self.lower_sigma_1m25:
                                self.buy_flag = True

#                                trade_flag = "buy"
#                                self.algorithm = "cross over base_line"
                        #elif self.first_trade_flag == "sell" and self.first_trade_time + timedelta(minutes=1) < base_time:
                        elif self.first_trade_flag == "sell" and self.buy_flag == False and self.sell_flag == False:
                            if current_price > self.upper_sigma_1m25:
                                self.sell_flag = True
#                                trade_flag = "sell"
#                                self.algorithm = "cross over base_line"

                    if self.buy_flag and current_price > self.ewma20_1mvalue:
                        trade_flag = "buy"
                    elif self.sell_flag and current_price < self.ewma20_1mvalue:
                        trade_flag = "sell"
#                if self.first_trade_time + timedelta(minutes=10) < base_time and self.first_trade_flag != "pass":
#                    self.debug_logger.info("reset first trade time: %s" % self.first_trade_time)
#                    self.debug_logger.info("reset first trade flag: %s" % self.first_trade_flag)
#                    self.debug_logger.info("reset first trade: %s" % base_time)
#                    self.resetFlag()

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
        self.first_trade_flag = "pass"
        self.stl_first_flag = False
        self.buy_flag = False
        self.sell_flag = False
        super(TrendReverseAlgo, self).resetFlag()


    def setReverseIndicator(self, base_time):
        target_time = base_time - timedelta(minutes=1)

        ### get 1m dataset
        dataset = getBollingerWrapper(target_time, self.instrument, table_type="1m", window_size=28, connector=self.mysql_connector, sigma_valiable=2, length=0)
        self.upper_sigma_1m2 = dataset["upper_sigmas"][-1]
        self.lower_sigma_1m2 = dataset["lower_sigmas"][-1]
        self.base_line_1m2 = dataset["base_lines"][-1]

        dataset = getBollingerWrapper(target_time, self.instrument, table_type="1m", window_size=28, connector=self.mysql_connector, sigma_valiable=2.5, length=0)
        self.upper_sigma_1m25 = dataset["upper_sigmas"][-1]
        self.lower_sigma_1m25 = dataset["lower_sigmas"][-1]
        self.base_line_1m25 = dataset["base_lines"][-1]

        sql = "select start_price, end_price, max_price, min_price from %s_%s_TABLE where insert_time < \'%s\' order by insert_time desc limit 1" % (self.instrument, "1m", target_time)
        response = self.mysql_connector.select_sql(sql)
        self.start_price_1m = response[0][0]
        self.end_price_1m = response[0][1]
        self.max_price_1m = response[0][2]
        self.min_price_1m = response[0][3]


        dataset = getBollingerWrapper(target_time, self.instrument, table_type="1m", window_size=28, connector=self.mysql_connector, sigma_valiable=2, length=9)
        base_line_1m2_list = dataset["base_lines"][-10:]
        self.slope_1m = getSlope(base_line_1m2_list)

        target_time = base_time

#        width = 60*20
#        sql = "select ask_price, bid_price from %s_TABLE where insert_time < \'%s\' order by insert_time desc limit %s" % (self.instrument, target_time, width)
#        response = self.mysql_connector.select_sql(sql)
#        tmp = []
#        for res in response:
#            tmp.append((res[0]+res[1])/2)
#        tmp.reverse()
#
#        ewma20_rawdata = tmp[-1*60*20:]
#        self.ewma20_1mvalue = getEWMA(ewma20_rawdata, len(ewma20_rawdata))[-1]

        width = 60*40
        sql = "select ask_price, bid_price from %s_TABLE where insert_time < \'%s\' order by insert_time desc limit %s" % (self.instrument, target_time, width)
        response = self.mysql_connector.select_sql(sql)
        tmp = []
        for res in response:
            tmp.append((res[0]+res[1])/2)
        tmp.reverse()

        ewma20_rawdata = tmp[-1*60*40:]
        self.ewma20_1mvalue = getEWMA(ewma20_rawdata, len(ewma20_rawdata))[-1]



        ### get 5m dataset
        target_time = base_time - timedelta(minutes=5)

        width = 20
        sql = "select end_price from %s_%s_TABLE where insert_time < \'%s\' order by insert_time desc limit %s" % (self.instrument, "5m", target_time, width)
        response = self.mysql_connector.select_sql(sql)
        tmp = []
        for res in response:
            tmp.append(res[0])
        tmp.reverse()
        self.ewma20_5mvalue = getEWMA(tmp, len(tmp))[-1]

        dataset = getBollingerWrapper(target_time, self.instrument, table_type="5m", window_size=28, connector=self.mysql_connector, sigma_valiable=2, length=0)
        self.base_line_5m2 = dataset["base_lines"][-1]
        self.upper_sigma_5m2 = dataset["upper_sigmas"][-1]
        self.lower_sigma_5m2 = dataset["lower_sigmas"][-1]

        dataset = getBollingerWrapper(target_time, self.instrument, table_type="5m", window_size=20, connector=self.mysql_connector, sigma_valiable=2, length=0)
        self.sma5m20 = dataset["base_lines"][-1]

        dataset = getBollingerWrapper(target_time, self.instrument, table_type="5m", window_size=40, connector=self.mysql_connector, sigma_valiable=2, length=0)
        self.sma5m40 = dataset["base_lines"][-1]

        dataset = getBollingerWrapper(target_time, self.instrument, table_type="5m", window_size=80, connector=self.mysql_connector, sigma_valiable=2, length=0)
        self.sma5m80 = dataset["base_lines"][-1]

    def decideTrailLogic(self, stl_flag, current_ask_price, current_bid_price, base_time):
        minutes = base_time.minute
        seconds = base_time.second

        if minutes % 5 == 0 and seconds < 10:
            order_price = self.getOrderPrice()
            first_take_profit = 0.05
            second_take_profit = 0.05

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
                if (self.most_high_price - 0.02) > current_bid_price:
                    self.result_logger.info("# Execute FirstTrail Stop")
                    stl_flag = True
            elif self.trail_flag == True and self.order_kind == "sell":
                if (self.most_low_price + 0.02) < current_ask_price :
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
                if (self.most_high_price - 0.02) > current_bid_price:
                    self.result_logger.info("# Execute SecondTrail Stop")
                    stl_flag = True
            elif self.trail_second_flag == True and self.order_kind == "sell":
                if (self.most_low_price + 0.02) < current_ask_price :
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
        self.result_logger.info("# First trade time at %s" % self.first_trade_time)
        self.result_logger.info("# EXECUTE ORDER at %s" % base_time)
        self.result_logger.info("# ORDER_PRICE=%s, TRADE_FLAG=%s" % (self.order_price, self.order_kind))
        self.result_logger.info("# self.slope_1m=%s" % self.slope_1m)
        self.result_logger.info("# self.upper_sigma_1m2=%s" % self.upper_sigma_1m2)
        self.result_logger.info("# self.lower_sigma_1m2=%s" % self.lower_sigma_1m2)
        self.result_logger.info("# self.upper_sigma_5m2=%s" % self.upper_sigma_1m2)
        self.result_logger.info("# self.lower_sigma_5m2=%s" % self.lower_sigma_1m2)
        self.result_logger.info("# self.start_price_1m=%s" % self.start_price_1m)
        self.result_logger.info("# self.end_price_1m=%s" % self.end_price_1m)
        self.result_logger.info("# self.max_price_1m=%s" % self.max_price_1m)
        self.result_logger.info("# self.min_price_1m=%s" % self.min_price_1m)
        self.result_logger.info("# self.sma5m20=%s" % self.sma5m20)
        self.result_logger.info("# self.sma5m40=%s" % self.sma5m40)
        self.result_logger.info("# self.sma5m80=%s" % self.sma5m80)

    def settlementLogWrite(self, profit, base_time, stl_price, stl_method):
        self.result_logger.info("# %s at %s" % (stl_method, base_time))
        self.result_logger.info("# self.ask_price=%s" % self.ask_price)
        self.result_logger.info("# self.bid_price=%s" % self.bid_price)
        self.result_logger.info("# self.log_max_price=%s" % self.log_max_price)
        self.result_logger.info("# self.log_min_price=%s" % self.log_min_price)
        self.result_logger.info("# STL_PRICE=%s" % stl_price)
        self.result_logger.info("# PROFIT=%s" % profit)
