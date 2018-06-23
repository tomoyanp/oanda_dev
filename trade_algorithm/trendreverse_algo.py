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
        self.trade_first_flag = "pass"
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
                        self.result_logger.info("# execute all over the world at TrendReverseAlgo")

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
                if self.order_kind == "buy" and self.max_price_1m > self.upper_sigma_1m2:
                    self.stl_first_flag = True
    
                elif self.order_kind == "sell" and self.min_price_1m < self.lower_sigma_1m2:
                    self.stl_first_flag = True

                if self.order_kind == "buy" and self.stl_first_flag:
                    #if self.end_price_1m < self.upper_sigma_1m2:
                    if self.end_price_1m < self.upper_sigma_1m15:
                        stl_flag = True
                elif self.order_kind == "sell" and self.stl_first_flag:
                    #if self.end_price_1m > self.lower_sigma_1m2:
                    if self.end_price_1m > self.lower_sigma_1m15:
                        stl_flag = True

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
        if trade_flag == "pass" and self.order_flag != True:
#        if trade_flag == "pass":
            hour = base_time.hour
            minutes = base_time.minute
            seconds = base_time.second
            if seconds < 10 and hour != 6:
                self.setReverseIndicator(base_time)

                if (self.upper_sigma_1m2 - self.lower_sigma_1m2) < 0.05:
                    pass
                else:
                    if self.buy_flag == False and self.sell_flag == False:
                        if self.end_price_1m < self.ewma20_1mvalue and self.start_price_1m > self.end_price_1m and self.min_price_1m <= self.ewma20_1mvalue <= self.max_price_1m and self.slope_1m > 0 and self.decideBollingerCrossOver("upper") == False:
                            self.buy_flag = True
                            self.set_time = base_time
        
                        if self.end_price_1m > self.ewma20_1mvalue and self.start_price_1m < self.end_price_1m and self.min_price_1m <= self.ewma20_1mvalue <= self.max_price_1m and self.slope_1m < 0 and self.decideBollingerCrossOver("lower") == False:
                            self.sell_flag = True
                            self.set_time = base_time
    
                    if self.buy_flag:
                        if self.end_price_1m > self.ewma20_1mvalue and self.start_price_1m < self.end_price_1m and self.slope_1m > 0 and self.decideBollingerCrossOver("upper") == False:
                            trade_flag = "buy"
                            self.algorithm = "cross_over_base_line"
    
                    elif self.sell_flag:
                        if self.end_price_1m < self.ewma20_1mvalue and self.start_price_1m > self.end_price_1m and self.slope_1m < 0 and self.decideBollingerCrossOver("lower") == False:
                            trade_flag = "sell"
                            self.algorithm = "cross_over_base_line"

                if self.buy_flag or self.sell_flag:
                    if self.set_time + timedelta(minutes=3) < base_time:
                        self.buy_flag = False
                        self.sell_flag = False

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
        self.trade_first_flag = "pass"
        self.stl_first_flag = False
        self.buy_flag = False
        self.sell_flag = False
        super(TrendReverseAlgo, self).resetFlag()


    def setReverseIndicator(self, base_time):
        target_time = base_time

        ### get 1m dataset
        dataset = getBollingerWrapper(target_time, self.instrument, table_type="1m", window_size=28, connector=self.mysql_connector, sigma_valiable=1.5, length=0)
        self.upper_sigma_1m15 = dataset["upper_sigmas"][-1]
        self.lower_sigma_1m15 = dataset["lower_sigmas"][-1]
        self.base_line_1m15 = dataset["base_lines"][-1]


        dataset = getBollingerWrapper(target_time, self.instrument, table_type="1m", window_size=28, connector=self.mysql_connector, sigma_valiable=2, length=0)
        self.upper_sigma_1m2 = dataset["upper_sigmas"][-1]
        self.lower_sigma_1m2 = dataset["lower_sigmas"][-1]
        self.base_line_1m2 = dataset["base_lines"][-1]


        sql = "select start_price, end_price, max_price, min_price from %s_%s_TABLE where insert_time < \'%s\' order by insert_time desc limit 1" % (self.instrument, "1m", target_time)
        response = self.mysql_connector.select_sql(sql)
        self.start_price_1m = response[0][0]
        self.end_price_1m = response[0][1]
        self.max_price_1m = response[0][2]
        self.min_price_1m = response[0][3]


#        sql = "select end_price from %s_%s_TABLE where insert_time < \'%s\' order by insert_time desc limit 200" % (self.instrument, "1m", target_time)

        width = 60*200
        sql = "select ask_price, bid_price from %s_TABLE where insert_time < \'%s\' order by insert_time desc limit %s" % (self.instrument, target_time, width)
        response = self.mysql_connector.select_sql(sql)
        tmp = []
        for res in response:
            tmp.append((res[0]+res[1])/2)
        tmp.reverse()

        ewma20_rawdata = tmp[-1*60*20:]
        ewma100_rawdata = tmp[-1*60*100:]
        ewma200_rawdata = tmp[-1*60*200:]
        self.ewma20_1mvalue = getEWMA(ewma20_rawdata, len(ewma20_rawdata))[-1]
        self.ewma100_1mvalue = getEWMA(ewma100_rawdata, len(ewma100_rawdata))[-1]
        self.ewma200_1mvalue = getEWMA(ewma200_rawdata, len(ewma200_rawdata))[-1]

        
        # get ewma20 slope
        sql = "select end_price from %s_%s_TABLE where insert_time < \'%s\' order by insert_time desc limit 30" % (self.instrument, "1m", target_time)
        response = self.mysql_connector.select_sql(sql)
        tmp = []
        for res in response:
            tmp.append(res[0])
        tmp.reverse()
        ewma20_1mvalue_list = getEWMA(tmp[-30:], 20)[-10:]
        self.slope_1m = getSlope(ewma20_1mvalue_list)


        ### get 5m dataset
        sql = "select start_price, end_price, max_price, min_price from %s_%s_TABLE where insert_time < \'%s\' order by insert_time desc limit 200" % (self.instrument, "5m", target_time)
        response = self.mysql_connector.select_sql(sql)
        self.start_price_5m = response[0][0]
        self.end_price_5m = response[0][1]
        self.max_price_5m = response[0][2]
        self.min_price_5m = response[0][3]


        dataset = getBollingerWrapper(target_time, self.instrument, table_type="5m", window_size=28, connector=self.mysql_connector, sigma_valiable=2, length=5)
        self.upper_sigma_5m2_list = dataset["upper_sigmas"][-6:]
        self.lower_sigma_5m2_list = dataset["lower_sigmas"][-6:]
        sql = "select max_price, min_price from %s_%s_TABLE where insert_time < \'%s\' order by insert_time desc limit 6" % (self.instrument, "5m", target_time)
        response = self.mysql_connector.select_sql(sql)
        self.max_price_5m_list = []
        self.min_price_5m_list = []

        for res in response:
            self.max_price_5m_list.append(res[0])
            self.min_price_5m_list.append(res[1])

        self.max_price_5m_list.reverse()
        self.min_price_5m_list.reverse()



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
        self.result_logger.info("# EXECUTE ORDER at %s" % base_time)
        self.result_logger.info("# ORDER_PRICE=%s, TRADE_FLAG=%s" % (self.order_price, self.order_kind))
        self.result_logger.info("# self.slope_1m=%s" % self.slope_1m)
        self.result_logger.info("# self.upper_sigma_1m2=%s" % self.upper_sigma_1m2)
        self.result_logger.info("# self.lower_sigma_1m2=%s" % self.lower_sigma_1m2)
        self.result_logger.info("# self.start_price_1m=%s" % self.start_price_1m)
        self.result_logger.info("# self.end_price_1m=%s" % self.end_price_1m)
        self.result_logger.info("# self.max_price_1m=%s" % self.max_price_1m)
        self.result_logger.info("# self.min_price_1m=%s" % self.min_price_1m)
        self.result_logger.info("# self.ewma20_1mvalue=%s" % self.ewma20_1mvalue)
        self.result_logger.info("# self.ewma100_1mvalue=%s" % self.ewma100_1mvalue)
        self.result_logger.info("# self.ewma200_1mvalue=%s" % self.ewma200_1mvalue)

    def settlementLogWrite(self, profit, base_time, stl_price, stl_method):
        self.result_logger.info("# %s at %s" % (stl_method, base_time))
        self.result_logger.info("# self.ask_price=%s" % self.ask_price)
        self.result_logger.info("# self.bid_price=%s" % self.bid_price)
        self.result_logger.info("# self.log_max_price=%s" % self.log_max_price)
        self.result_logger.info("# self.log_min_price=%s" % self.log_min_price)
        self.result_logger.info("# STL_PRICE=%s" % stl_price)
        self.result_logger.info("# PROFIT=%s" % profit)
