# coding: utf-8
####################################################
# Trade Decision
# trade timing: at 13, 14, 15, 20, 21 o'clock
# if endprice over bollinger band 2sigma 2 times
# if oshime and modori at ema 20, execute entry
# stoploss rate: 20pips
# takeprofit rate: 50pips
####################################################


from super_algo import SuperAlgo
from common import instrument_init, account_init, decideMarket, getSlope, getEWMA
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
        self.log_max_price = 0
        self.log_min_price = 0
        self.first_flag = "pass"
        self.second_flag = "pass"
        self.first_flag_time = None
        self.second_flag_time = None
        self.setExpantionIndicator(base_time)
        #self.setVolatilityIndicator(base_time)
        self.setDailyIndicator(base_time)

    # decide trade entry timing
    def decideTrade(self, base_time):
        trade_flag = "pass"
        try:
            if self.order_flag:
                pass
            else:
#            if 1 == 1:
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
                        if 1==1:
                            trade_flag = self.decideExpantionTrade(trade_flag, current_price, base_time)
    
    
                if trade_flag != "pass" and self.order_flag:
                    if trade_flag == "buy" and self.order_kind == "buy":
                        trade_flag = "pass"
                    elif trade_flag == "sell" and self.order_kind == "sell":
                        trade_flag = "pass"
                    else:
                        self.result_logger.info("# execute all over the world at MultiAlgo")
    
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

                    if hour == 7 and minutes == 0 and seconds < 10:
                        self.setDailyIndicator(base_time)

                    # if weekday == Saturday, we will settle one's position.
                    if weekday == 5 and hour >= 5:
                        self.result_logger.info("# weekend stl logic")
                        stl_flag = True

                    else:
                        stl_flag = self.decideCommonStoploss(stl_flag, current_price, base_time)
                        stl_flag = self.decideExpantionStoploss(stl_flag, current_price, base_time)
                        stl_flag = self.decideTrailLogic(stl_flag, self.ask_price, self.bid_price, base_time)

            else:
                pass

            self.writeDebugLog(base_time, mode="stl")

            return stl_flag
        except:
            raise


    def decideHighLowPrice(self, current_price, exceed_th, surplus_th, high_price, low_price, mode):
        flag = False

        if mode == "buy":
            if current_price  > (high_price + exceed_th):
                flag = True
            elif current_price < (high_price - surplus_th):
                flag = True
        elif mode == "sell":
            if current_price < (low_price - exceed_th):
                flag = True
            elif current_price > (low_price + surplus_th):
                flag = True

        return flag


    # cannot allovertheworld
    def decideExpantionTrade(self, trade_flag, current_price, base_time):
        if trade_flag == "pass":
            hour = base_time.hour
            minutes = base_time.minute
            seconds = base_time.second

            expantion_timelimit = 3    # 3hours
            #if (hour == 8 or hour == 9 or hour == 10 or hour == 12 or hour == 13 or hour == 14 or hour == 15 or hour == 16 or hour == 17 or hour == 19 or hour == 20 or hour == 21) and (minutes == 59) and seconds < 10:
            if (hour == 12 or hour == 13 or hour == 14 or hour == 19) and (minutes == 59) and seconds < 10:
                self.setExpantionIndicator(base_time)
                if self.sma20_1h > self.sma40_1h > self.sma80_1h:
                    trade_flag  = "buy"
                    self.algorithm = "expantion"
                    self.entry_time = base_time

                elif self.sma20_1h < self.sma40_1h < self.sma80_1h:
                    trade_flag = "sell"
                    self.algorithm = "expantion"
                    self.entry_time = base_time

        self.setExpantionStoploss(trade_flag)
        return trade_flag


    def setExpantionStoploss(self, trade_flag):
#        if trade_flag != "pass" and self.algorithm == "expantion":
        if trade_flag != "pass":
            if trade_flag == "buy" and self.daily_slope > 0:
                self.original_stoploss_rate = 0.2
            elif trade_flag == "buy" and self.daily_slope < 0:
                self.original_stoploss_rate = 0.2
            elif trade_flag == "sell" and self.daily_slope < 0:
                self.original_stoploss_rate = 0.2
            elif trade_flag == "sell" and self.daily_slope > 0:
                self.original_stoploss_rate = 0.2

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

    def decideTouchBollinger(self, mode):
        flag = False
        if mode == "upper":
            for i in range(0, len(self.upper_sigma_5m2_list)):
                if self.end_price_5m_list[i] > self.upper_sigma_5m2_list[i]:
                    flag = True

        elif mode == "lower":
            for i in range(0, len(self.lower_sigma_5m2_list)):
                if self.end_price_5m_list[i] < self.lower_sigma_5m2_list[i]:
                    flag = True

        return flag
         

    def decideExpantionStoploss(self, stl_flag, current_price, base_time):
        target_time = self.entry_time + timedelta(minutes=11)
        base_ftime = base_time.strftime("%Y-%m-%d %H:%M:00")
        target_ftime = target_time.strftime("%Y-%m-%d %H:%M:00")

        seconds = base_time.second
 
        if target_ftime == base_ftime and seconds < 10:
            self.debug_logger.info("target_time=%s" % target_time)
            self.debug_logger.info("base_time=%s" % base_time)
            self.setExpantionIndicator(base_time)
            if self.order_kind == "buy" and self.decideTouchBollinger("upper") == False:
                self.result_logger.info("bollinger stoploss")
                stl_flag = True
    
            elif self.order_kind == "sell" and self.decideTouchBollinger("lower") == False:
                self.result_logger.info("bollinger stoploss")
                stl_flag = True

#        target_time = self.entry_time + timedelta(hours=3)
#
#        if base_time > target_time:
#            if self.order_kind == "buy" and self.sma20_1h > current_price:
#                self.result_logger.info("sma20 stoploss")
#                stl_flag = True
#            elif self.order_kind == "sell" and self.sma20_1h < current_price:
#                self.result_logger.info("sma20 stoploss")
#                stl_flag = True

        return stl_flag

    def updatePrice(self, current_price):
        if self.log_max_price == 0:
            self.log_max_price = current_price
        elif self.log_max_price < current_price:
            self.log_max_price = current_price
        if self.log_min_price == 0:
            self.log_min_price = current_price
        elif self.log_min_price > current_price:
            self.log_min_price = current_price


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
        self.most_high_price = 0
        self.most_low_price = 0
        self.stoploss_flag = False
        self.algorithm = ""
        self.log_max_price = 0
        self.log_min_price = 0
        self.first_flag = "pass"
        self.second_flag = "pass"
        self.first_flag_time = None
        self.second_flag_time = None
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

        # set 5m 2sigma bollinger band
        dataset = getBollingerWrapper(target_time, self.instrument, table_type="5m", window_size=28, connector=self.mysql_connector, sigma_valiable=2, length=1)
        self.upper_sigma_5m2_list = dataset["upper_sigmas"][-2:]
        self.lower_sigma_5m2_list = dataset["lower_sigmas"][-2:]
        self.base_line_5m2_list = dataset["base_lines"][-2:]

        # set 5m 3sigma bollinger band
        dataset = getBollingerWrapper(target_time, self.instrument, table_type="5m", window_size=28, connector=self.mysql_connector, sigma_valiable=3, length=1)
        self.upper_sigma_5m3_list = dataset["upper_sigmas"][-2:]
        self.lower_sigma_5m3_list = dataset["lower_sigmas"][-2:]
        self.base_line_5m3_list = dataset["base_lines"][-2:]

        # set 5m end price list
        sql = "select end_price from %s_%s_TABLE where insert_time < \'%s\' order by insert_time desc limit 2" % (self.instrument, "5m", target_time)
        response = self.mysql_connector.select_sql(sql)
        tmp = []
        for res in response:
            tmp.append(res[0])

        tmp.reverse()
        self.end_price_5m_list = tmp

        # set dataset 1hour
        target_time = base_time - timedelta(hours=1)

        # set 1h end price list
        sql = "select end_price from %s_%s_TABLE where insert_time < \'%s\' order by insert_time desc limit 80" % (self.instrument, "1h", target_time)
        response = self.mysql_connector.select_sql(sql)
        tmp = []
        for res in response:
            tmp.append(res[0])

        tmp.reverse()
        self.end_price_1h_list = tmp

        self.sma20_1h = sum(self.end_price_1h_list[-20:])/len(self.end_price_1h_list[-20:])
        self.sma40_1h = sum(self.end_price_1h_list[-40:])/len(self.end_price_1h_list[-40:])
        self.sma80_1h = sum(self.end_price_1h_list[-80:])/len(self.end_price_1h_list[-80:])


    def setVolatilityIndicator(self, base_time):
        target_time = base_time - timedelta(minutes=5)
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
        pass
#        self.debug_logger.info("%s: %s Logic START" % (base_time, mode))
#        self.debug_logger.info("# self.buy_count=%s" % self.buy_count)
#        self.debug_logger.info("# self.sell_count=%s" % self.sell_count)
#        self.debug_logger.info("# self.daily_slope=%s" % self.daily_slope)
#        self.debug_logger.info("# self.upper_sigma_1h3=%s" % self.upper_sigma_1h3)
#        self.debug_logger.info("# self.lower_sigma_1h3=%s" % self.lower_sigma_1h3)
#        self.debug_logger.info("# self.upper_sigma_5m3=%s" % self.upper_sigma_5m3)
#        self.debug_logger.info("# self.lower_sigma_5m3=%s" % self.lower_sigma_5m3)
#        self.debug_logger.info("# self.start_price_5m=%s" % self.start_price_5m)
#        self.debug_logger.info("# self.end_price_5m=%s" % self.end_price_5m)
#        self.debug_logger.info("# self.start_price_1m=%s" % self.start_price_1m)
#        self.debug_logger.info("# self.end_price_1m=%s" % self.end_price_1m)
#        self.debug_logger.info("#############################################")

    def entryLogWrite(self, base_time):
        self.result_logger.info("#######################################################")
        self.result_logger.info("# in %s Algorithm" % self.algorithm)
        self.result_logger.info("# EXECUTE ORDER at %s" % base_time)
        self.result_logger.info("# ORDER_PRICE=%s, TRADE_FLAG=%s" % (self.order_price, self.order_kind))
        self.result_logger.info("# self.daily_slope=%s" % self.daily_slope)
        self.result_logger.info("# self.upper_sigma_5m2=%s" % self.upper_sigma_5m2_list[-1])
        self.result_logger.info("# self.lower_sigma_5m2=%s" % self.lower_sigma_5m2_list[-1])
        self.result_logger.info("# self.sma20_1h=%s" % self.sma20_1h)
        self.result_logger.info("# self.sma40_1h=%s" % self.sma40_1h)
        self.result_logger.info("# self.sma80_1h=%s" % self.sma80_1h)

    def settlementLogWrite(self, profit, base_time, stl_price, stl_method):
        self.result_logger.info("# self.log_max_price=%s" % self.log_max_price)
        self.result_logger.info("# self.log_min_price=%s" % self.log_min_price)
        self.result_logger.info("# EXECUTE SETTLEMENT at %s" % base_time)
        self.result_logger.info("# STL_PRICE=%s" % stl_price)
        self.result_logger.info("# PROFIT=%s" % profit)
