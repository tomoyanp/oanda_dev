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

class MultiEvolvAlgo(SuperAlgo):
    def __init__(self, instrument, base_path, config_name, base_time):
        super(MultiEvolvAlgo, self).__init__(instrument, base_path, config_name, base_time)
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
        self.setReverseIndicator(base_time)
        self.high_price, self.low_price = getHighlowPriceWrapper(instrument=self.instrument, base_time=base_time, span=1, table_type="day", connector=self.mysql_connector)
        self.daily_slope = self.getDailySlope(self.instrument, base_time, span=10, connector=self.mysql_connector)
        self.reverse_sell_flag = False
        self.reverse_buy_flag = False
        self.reverse_sell_count = 0
        self.reverse_buy_count = 0

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
                        trade_flag = self.decideReverseTrade(trade_flag, current_price, base_time)

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
                    self.setDailyIndicator(base_time)
                    current_price = self.getCurrentPrice()
                    weekday = base_time.weekday()
                    hour = base_time.hour

                    # if weekday == Saturday, we will settle one's position.
                    if weekday == 5 and hour >= 5:
                        self.result_logger.info("# weekend stl logic")
                        stl_flag = True

                    else:
                        stl_flag = self.decideCommonStoploss(stl_flag, current_price, base_time)
                        stl_flag = self.decideReverseStoploss(stl_flag, base_time)
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
#            if hour >= 15 or hour < 4:
            if 1 == 1:
                if minutes % 5 == 4 and seconds >= 50:
                    self.setExpantionIndicator(base_time)
                    self.calcBuyExpantion(current_price, base_time)
                    self.calcSellExpantion(current_price, base_time)
                    if self.buy_count > self.count_threshold and trade_flag == "pass":
                        surplus_flag, surplus_mode = decideHighSurplusPrice(current_price=current_price, high_price=self.high_price, threshold=0.5)
                        exceed_flag, exceed_mode = decideHighExceedPrice(current_price=current_price, high_price=self.high_price, threshold=0.2)

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
                        surplus_flag, surplus_mode = decideLowSurplusPrice(current_price=current_price, low_price=self.low_price, threshold=0.5)
                        exceed_flag, exceed_mode = decideLowExceedPrice(current_price=current_price, low_price=self.low_price, threshold=0.2)

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

#            if  (hour >= 15 or hour < 4) and seconds >= 50:
            if 1==1:
                self.setVolatilityIndicator(base_time)
                up_flag, down_flag = decideVolatility(current_price=current_price, volatility_value=0.3, volatility_buy_price=self.volatility_buy_price,         volatility_bid_price=self.volatility_bid_price)

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

                if trade_flag != "pass":
                    self.first_take_profit = 0.5
                    self.second_take_profit = 1.0
                    self.first_trail_threshold = 0.3
                    self.second_trail_threshold = 0.3


        return trade_flag


    def decideReverseTrade(self, trade_flag, current_price, base_time):
        minutes = base_time.minute
        seconds = base_time.second
        if minutes == 59 and seconds >= 50:
            common_stoploss = 0.2
            self.setReverseIndicator(base_time)
            if self.sell_count > self.count_threshold or self.buy_count > self.count_threshold:
                pass
            elif (self.upper_sigma_1h3 - self.lower_sigma_1h3) > 2:
                if self.upper_sigma_1h2 < self.end_price:
                    self.reverse_sell_flag = True
                    self.result_logger.info("# reverse sell flag on at %s " % base_time)
    
                elif self.lower_sigma_1h2 > self.end_price:
                    self.reverse_buy_flag = True
                    self.result_logger.info("# reverse buy flag on at %s " % base_time)
    
                if self.reverse_sell_flag:
                    if self.end_price < self.upper_sigma_1h2:
                        self.reverse_sell_count = self.reverse_sell_count + 1
                        self.result_logger.info("# reverse sell count increment at %s " % base_time)
                    else:
                        self.reverse_sell_count = 0
                if self.reverse_buy_flag:
                    if self.end_price > self.lower_sigma_1h2:
                        self.reverse_buy_count = self.reverse_buy_count + 1
                        self.result_logger.info("# reverse buy count increment at %s " % base_time)
                    else:
                        self.reverse_buy_count = 0
    
                if self.reverse_sell_count == 2:
                    trade_flag = "sell"
                    self.original_stoploss_rate = common_stoploss
                    self.algorithm = "reverse"
                    self.writeResultLog()
                if self.reverse_buy_count == 2:
                    trade_flag = "buy"
                    self.algorithm = "reverse"
                    self.original_stoploss_rate = common_stoploss
                    self.writeResultLog()

                if trade_flag != "pass":
                    self.first_take_profit = 0.3
                    self.second_take_profit = 0.5
                    self.first_trail_threshold = 0.3
                    self.second_trail_threshold = 0.01


        return trade_flag

# stop loss function
    def decideReverseStoploss(self, stl_flag, base_time):
        if self.algorithm == "reverse":
            minutes = base_time.minute
            seconds = base_time.second
            if minutes == 59 and seconds >= 50:
                self.setReverseIndicator(base_time)
                if (self.upper_sigma_1h3 - self.lower_sigma_1h3) < 2:
                    stl_flag = True
                    self.result_logger.info("# band width < 2 settlment execution")
        
        return stl_flag


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

    def decideStoploss(self, stl_flag, base_time):
        minutes = base_time.minute
        seconds = base_time.second
        if minutes % 5 == 4 and seconds >= 50 and self.algorithm != "volatility":
            stop_loss_threshold_list = [0, 0.1, 0.2]

            if self.order_kind == "buy" and self.stoploss_flag == False:
                if float(self.order_price - self.bid_price) > float(stop_loss_threshold_list[1]):
                    self.stoploss_flag = True
            elif self.order_kind == "sell" and self.stoploss_flag == False:
                if float(self.ask_price - self.order_price) > float(stop_loss_threshold_list[1]):
                    self.stoploss_flag = True

            if self.order_kind == "buy" and self.stoploss_flag:
                if float(self.order_price - self.bid_price) < float(stop_loss_threshold_list[0]):
                    self.result_logger.info("Execute Help Settlement")
                    stl_flag = True
                elif float(self.order_price - self.bid_price) > float(stop_loss_threshold_list[2]):
                    self.result_logger.info("Execute Final Settlement")
                    stl_flag = True
            elif self.order_kind == "sell" and self.stoploss_flag:
                if float(self.ask_price - self.order_price) < float(stop_loss_threshold_list[0]):
                    self.result_logger.info("Execute Help Settlement")
                    stl_flag = True
                elif float(self.ask_price - self.order_price) > float(stop_loss_threshold_list[2]):
                    self.result_logger.info("Execute Final Settlement")
                    stl_flag = True

        return stl_flag


    def decideCommonStoploss(self, stl_flag, current_price, base_time):
        if self.algorithm == "expantion" or self.algorithm == "volatility" or self.algorithm == "reverse":
            minutes = base_time.minute
            seconds = base_time.second

            if minutes % 5 == 4 and seconds >= 50:
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

        if minutes % 5 == 4 and seconds >= 50:
            order_price = self.getOrderPrice()


#####            first_take_profit = 0.5
#####            second_take_profit = 1.0
#####            first_trail_threshold = 0.3
#####            second_trail_threshold = 0.3

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
                if (current_bid_price - order_price) > self.first_take_profit:
                    self.trail_flag = True
            elif self.order_kind == "sell":
                if (order_price - current_ask_price) > self.first_take_profit:
                    self.trail_flag = True


            if self.trail_flag == True and self.order_kind == "buy":
                if (self.most_high_price - self.first_trail_threshold) > current_bid_price:
                    self.result_logger.info("# Execute FirstTrail Stop")
                    stl_flag = True
            elif self.trail_flag == True and self.order_kind == "sell":
                if (self.most_low_price + self.first_trail_threshold) < current_ask_price :
                    self.result_logger.info("# Execute FirstTrail Stop")
                    stl_flag = True

            # second trailing stop logic
            if self.order_kind == "buy":
                if (current_bid_price - order_price) > self.second_take_profit:
                    self.trail_second_flag = True
            elif self.order_kind == "sell":
                if (order_price - current_ask_price) > self.second_take_profit:
                    self.trail_second_flag = True
            if self.trail_second_flag == True and self.order_kind == "buy":
                if (self.most_high_price - self.second_trail_threshold) > current_bid_price:
                    self.result_logger.info("# Execute SecondTrail Stop")
                    stl_flag = True
            elif self.trail_second_flag == True and self.order_kind == "sell":
                if (self.most_low_price + self.second_trail_threshold) < current_ask_price :
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
        self.reverse_sell_flag = False
        self.reverse_buy_flag = False
        self.reverse_sell_count = 0
        self.reverse_buy_count = 0
        super(MultiEvolvAlgo, self).resetFlag()


# set Indicator dataset function
    def getDailySlope(self, instrument, base_time, span, connector):
        target_time = base_time.strftime("%Y-%m-%d 07:00:00")
        table_type = "day"

        sql = "select end_price from %s_%s_TABLE where insert_time < \'%s\' order by insert_time desc limit %s" % (instrument, table_type, target_time, span)

        response = connector.select_sql(sql)

        price_list = []
        for res in response:
            price_list.append(res[0])


        price_list.reverse()
        slope = getSlope(price_list)

        return slope

    def setReverseIndicator(self, base_time):
        dataset = getBollingerWrapper(base_time, self.instrument, table_type="1h", window_size=28, connector=self.mysql_connector, sigma_valiable=3, length=0)
        self.upper_sigma_1h3 = dataset["upper_sigmas"][-1]
        self.lower_sigma_1h3 = dataset["lower_sigmas"][-1]
        self.base_line_1h3 = dataset["base_lines"][-1]

        dataset = getBollingerWrapper(base_time, self.instrument, table_type="1h", window_size=28, connector=self.mysql_connector, sigma_valiable=2, length=0)
        self.upper_sigma_1h2 = dataset["upper_sigmas"][-1]
        self.lower_sigma_1h2 = dataset["lower_sigmas"][-1]
        self.base_line_1h2 = dataset["base_lines"][-1]

        sql = "select end_price from %s_%s_TABLE where insert_time < '%s' order by insert_time desc limit 1" % (self.instrument, "1h", base_time)
        response = self.mysql_connector.select_sql(sql)
        self.end_price = response[0][0]


    def setExpantionIndicator(self, base_time):
        dataset = getBollingerWrapper(base_time, self.instrument, table_type="5m", window_size=28, connector=self.mysql_connector, sigma_valiable=3, length=0)
        self.upper_sigma_5m3 = dataset["upper_sigmas"][-1]
        self.lower_sigma_5m3 = dataset["lower_sigmas"][-1]
        self.base_line_5m3 = dataset["base_lines"][-1]

        dataset = getBollingerWrapper(base_time, self.instrument, table_type="1h", window_size=28, connector=self.mysql_connector, sigma_valiable=3, length=0)
        self.upper_sigma_1h3 = dataset["upper_sigmas"][-1]
        self.lower_sigma_1h3 = dataset["lower_sigmas"][-1]
        self.base_line_1h3 = dataset["base_lines"][-1]

    def setVolatilityIndicator(self, base_time):
        self.volatility_buy_price, self.volatility_bid_price = getVolatilityPriceWrapper(self.instrument, base_time, span=60, connector=self.mysql_connector)

    def setDailyIndicator(self, base_time):
        hour = base_time.hour
        minute = base_time.minute
        second = base_time.second
        if hour == 7 and minute == 0 and second <= 10:
            self.daily_slope = self.getDailySlope(self.instrument, base_time, span=10, connector=self.mysql_connector)
            base_ftime = base_time.strftime("%Y-%m-%d 07:00:00")
            self.high_price, self.low_price = getHighlowPriceWrapper(instrument=self.instrument, base_time=base_ftime, span=1, table_type="day", connector=self.mysql_connector)
            dataset = getBollingerWrapper(base_time, self.instrument, table_type="day", window_size=28, connector=self.mysql_connector, sigma_valiable=2, length=0)
            self.upper_sigma_1d2 = dataset["upper_sigmas"][-1]
            self.lower_sigma_1d2 = dataset["lower_sigmas"][-1]
            self.base_line_1d2 = dataset["base_lines"][-1]



# write log function

    def writeDebugLog(self, base_time, mode):
        self.debug_logger.info("%s: %s Logic START" % (base_time, mode))
        self.debug_logger.info("self.buy_count=%s" % self.buy_count)
        self.debug_logger.info("self.sell_count=%s" % self.sell_count)
        self.debug_logger.info("self.high_price=%s" % self.high_price)
        self.debug_logger.info("self.low_price=%s" % self.low_price)
        self.debug_logger.info("self.daily_slope=%s" % self.daily_slope)
        self.debug_logger.info("self.upper_sigma_1h3=%s" % self.upper_sigma_1h3)
        self.debug_logger.info("self.lower_sigma_1h3=%s" % self.lower_sigma_1h3)
        self.debug_logger.info("self.upper_sigma_1h2=%s" % self.upper_sigma_1h2)
        self.debug_logger.info("self.lower_sigma_1h2=%s" % self.lower_sigma_1h2)
        self.debug_logger.info("#############################################")

    def writeResultLog(self):
        self.result_logger.info("#######################################################")
        self.result_logger.info("# in %s Algorithm" % self.algorithm)
        self.result_logger.info("# self.count_threshold=%s" %  self.count_threshold)
        self.result_logger.info("# self.buy_count=%s" %  self.buy_count)
        self.result_logger.info("# self.sell_count=%s" %  self.sell_count)
        self.result_logger.info("# self.daily_slope=%s" % self.daily_slope)
        self.result_logger.info("# volatility_buy_price=%s" % self.volatility_buy_price)
        self.result_logger.info("# volatility_bid_price=%s" % self.volatility_bid_price)
        self.result_logger.info("# self.upper_sigma_5m3=%s" % self.upper_sigma_5m3)
        self.result_logger.info("# self.lower_sigma_5m3=%s" % self.lower_sigma_5m3)
        self.result_logger.info("# self.base_line_5m3=%s" % self.base_line_5m3)
        self.result_logger.info("# self.upper_sigma_1h3=%s" % self.upper_sigma_1h3)
        self.result_logger.info("# self.lower_sigma_1h3=%s" % self.lower_sigma_1h3)
        self.result_logger.info("# self.original_stoploss_rate=%s" % self.original_stoploss_rate)

