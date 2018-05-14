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
        self.original_stoploss_rate = 0
        self.week_start_price = 0
        self.setIndicator(base_time)
        self.high_price, self.low_price = getHighlowPriceWrapper(instrument=self.instrument, base_time=base_time, span=24, slide_span=0, connector=self.mysql_connector)
        self.daily_slope = self.getDailySlope(self.instrument, base_time, span=10, connector=self.mysql_connector)
        self.stoploss_flag = False
        self.algorithm = ""

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

                    self.setOriginalStoploss(trade_flag)

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

                    # if weekday == Saturday, we will settle one's position.
                    if weekday == 5 and hour >= 5:
                        self.result_logger.info("# weekend stl logic")
                        stl_flag = True

                    else:
                        stl_flag = self.decideVolatilityStopLoss(stl_flag, current_price, base_time)
                        stl_flag = self.decideExpantionStopLoss(stl_flag, current_price, base_time)
                        stl_flag = self.decideTrailLogic(stl_flag, self.ask_price, self.bid_price, base_time)
#                        stl_flag = self.decideStopLoss(stl_flag, current_price, base_time)

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
            if current_price > (self.upper_sigma_5m3) > 0 and (self.upper_sigma_1h3 - self.lower_sigma_1h3) < 2 and self.slope > 0:
                self.buy_count = self.buy_count + 1
                self.buy_count_price = current_price
                self.sell_count = 0

        else:
            if current_price > (self.upper_sigma_5m3) and current_price > self.buy_count_price and (self.upper_sigma_1h3 - self.lower_sigma_1h3) < 2 and self.slope > 0:
                self.buy_count = self.buy_count + 1
                self.first_flag_time = base_time
                self.sell_count = 0
                self.buy_count_price = current_price


    def calcSellExpantion(self, current_price, base_time):
        if self.sell_count == 0:
            if current_price < self.lower_sigma_5m3 and (self.upper_sigma_1h3 - self.lower_sigma_1h3) < 2 and self.slope < 0:
                self.sell_count = self.sell_count + 1
                self.sell_count_price = current_price
                self.buy_count = 0

        else:
            if current_price < self.lower_sigma_5m3 and current_price < self.sell_count_price and (self.upper_sigma_1h3 - self.lower_sigma_1h3) < 2 and self.slope < 0:
                self.sell_count = self.sell_count + 1
                self.first_flag_time = base_time
                self.buy_count = 0


    def decideVolatilityTrade(self, trade_flag, current_price, base_time):
        hour = base_time.hour
        seconds = base_time.second

        if  (hour >= 15 or hour < 4) and seconds >= 50:
            self.setVolatilityIndicator(base_time)
            up_flag, down_flag = decideVolatility(current_price=current_price, volatility_value=0.3, volatility_buy_price=self.volatility_buy_price,     volatility_bid_price=self.volatility_bid_price)

            if up_flag:
                trade_flag = "buy"
                self.buy_count = 0
                self.sell_count = 0
                self.algorithm = "volatility"
                self.writeVolatilityLog(current_price, mode="trade")
            elif down_flag:
                trade_flag = "sell"
                self.buy_count = 0
                self.sell_count = 0
                self.algorithm = "volatility"
                self.writeVolatilityLog(current_price, mode="trade")

        return trade_flag

    def decideExpantionTrade(self, trade_flag, current_price, base_time):
        hour = base_time.hour
        minutes = base_time.minute
        seconds = base_time.second
        if hour >= 15 or hour < 4:
            if minutes % 5 == 4 and seconds >= 50:
                self.setExpantionIndicator(base_time)
                mode = "trade"
                # expantion logic
                self.calcBuyExpantion(current_price, base_time)
                self.calcSellExpantion(current_price, base_time)
                if self.buy_count > self.count_threshold and trade_flag == "pass":
                    surplus_flag, surplus_mode = decideHighSurplusPrice(current_price=current_price, high_price=self.high_price, threshold=0.5)
                    exceed_flag, exceed_mode = decideHighExceedPrice(current_price=current_price, high_price=self.high_price, threshold=0.2)

                    if surplus_flag:
                        trade_flag = "buy"
                        self.writeExpantionLog(current_price, mode=mode, highlow_mode="surplus")
                        self.buy_count = 0
                        self.sell_count = 0

                    elif exceed_flag:
                        trade_flag = "buy"
                        self.writeExpantionLog(current_price, mode=mode, highlow_mode="exceed")
                        self.buy_count = 0
                        self.sell_count = 0

                elif self.sell_count > self.count_threshold and trade_flag == "pass":
                    surplus_flag, surplus_mode = decideLowSurplusPrice(current_price=current_price, low_price=self.low_price, threshold=0.5)
                    exceed_flag, exceed_mode = decideLowExceedPrice(current_price=current_price, low_price=self.low_price, threshold=0.2)

                    if surplus_flag:
                        trade_flag = "sell"
                        self.writeExpantionLog(current_price, mode=mode, highlow_mode="surplus")
                        self.buy_count = 0
                        self.sell_count = 0

                    elif exceed_flag:
                        trade_flag = "sell"
                        self.writeExpantionLog(current_price, mode=mode, highlow_mode="exceed")
                        self.buy_count = 0
                        self.sell_count = 0
        else:
            self.buy_count = 0
            self.sell_count = 0

        mode = "trade"
        self.writeDebugLog(base_time, up_flag="null", down_flag="null", mode=mode)

        return trade_flag


    def setOriginalStoploss(self, trade_flag):
        if trade_flag != "pass":
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

    def decideStopLoss(self, stl_flag, current_price, base_time):
        minutes = base_time.minute
        seconds = base_time.second
        if minutes % 5 == 4 and seconds >= 50 and self.algorithm != "volatility":
            stop_loss_threshold_list = [0, 0.1, 0.2]
            self.debug_logger.info("#### decideStoploss Function ####")
            self.debug_logger.info("self.order_kind=%s" % self.order_kind)
            self.debug_logger.info("self.order_price=%s" % self.order_price)
            self.debug_logger.info("self.ask_price=%s" % self.ask_price)
            self.debug_logger.info("self.bid_price=%s" % self.bid_price)

            if self.order_kind == "buy" and self.stoploss_flag == False:
                if float(self.order_price - self.bid_price) > float(stop_loss_threshold_list[1]):
                    self.debug_logger.info("stoploss_flag to be True")
                    self.stoploss_flag = True
            elif self.order_kind == "sell" and self.stoploss_flag == False:
                if float(self.ask_price - self.order_price) > float(stop_loss_threshold_list[1]):
                    self.debug_logger.info("stoploss_flag to be True")
                    self.stoploss_flag = True


            if self.order_kind == "buy" and self.stoploss_flag:
                if float(self.order_price - self.bid_price) < float(stop_loss_threshold_list[0]):
                    self.debug_logger.info("execute help settlement")
                    self.result_logger.info("Execute Help Settlement")
                    stl_flag = True
                elif float(self.order_price - self.bid_price) > float(stop_loss_threshold_list[2]):
                    self.debug_logger.info("execute final settlement")
                    self.result_logger.info("Execute Final Settlement")
                    stl_flag = True
            elif self.order_kind == "sell" and self.stoploss_flag:
                if float(self.ask_price - self.order_price) < float(stop_loss_threshold_list[0]):
                    self.debug_logger.info("execute help settlement")
                    self.result_logger.info("Execute Help Settlement")
                    stl_flag = True
                elif float(self.ask_price - self.order_price) > float(stop_loss_threshold_list[2]):
                    self.debug_logger.info("execute final settlement")
                    self.result_logger.info("Execute Final Settlement")
                    stl_flag = True

        return stl_flag


    def decideVolatilityStopLoss(self, stl_flag, current_price, base_time):
        mode = "stl"
        seconds = base_time.second
        if seconds >= 50:
            self.setVolatilityIndicator(base_time)
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
        minutes = base_time.minute
        seconds = base_time.second

        if minutes % 5 == 4 and seconds >= 50:
            if self.order_kind == "buy":
                if (self.order_price - self.bid_price) > self.original_stoploss_rate:
                    stl_flag = True

            elif self.order_kind == "sell":
                if (self.ask_price - self.order_price) > self.original_stoploss_rate:
                    stl_flag = True

#            self.setExpantionIndicator(base_time)
#            mode = "stl"
#
#            if current_price > self.upper_sigma_5m3 and self.order_kind == "sell":
#                stl_flag = True
#                self.result_logger.info("# Execute Reverse Settlement")
#                self.result_logger.info("# current_price=%s, self.upper_sigma_5m3=%s, self.lower_sigma_5m3=%s, self.order_kind=%s" % (current_price,     #self.upper_sigma_5m3, self.lower_sigma_5m3, self.order_kind))
#
#            elif current_price < self.lower_sigma_5m3 and self.order_kind == "buy":
#                stl_flag = True
#                self.result_logger.info("# Execute Reverse Settlement")
#                self.result_logger.info("# current_price=%s, self.upper_sigma_5m3=%s, self.lower_sigma_5m3=%s, self.order_kind=%s" % (current_price, #self.upper_sigma_5m3, self.lower_sigma_5m3, self.order_kind))

#            self.writeDebugLog(base_time, up_flag="null", down_flag="null", mode=mode)

        return stl_flag

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
        super(ExpantionAlgo, self).resetFlag()

    def decideTrailLogic(self, stl_flag, current_ask_price, current_bid_price, base_time):
        minutes = base_time.minute
        seconds = base_time.second

        if minutes % 5 == 4 and seconds >= 50:
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
                    self.result_logger.info("# current_bid_price=%s, order_price=%s" % (current_bid_price, order_price))
                    stl_flag = True
            elif self.trail_flag == True and self.order_kind == "sell":
                if (self.most_low_price + 0.3) < current_ask_price :
                    self.result_logger.info("# Execute FirstTrail Stop")
                    self.result_logger.info("# current_ask_price=%s, order_price=%s" % (current_ask_price, order_price))
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
                    self.result_logger.info("# current_bid_price=%s, order_price=%s" % (current_bid_price, order_price))
                    stl_flag = True
            elif self.trail_second_flag == True and self.order_kind == "sell":
                if (self.most_low_price + 0.3) < current_ask_price :
                    self.result_logger.info("# Execute SecondTrail Stop")
                    self.result_logger.info("# current_ask_price=%s, order_price=%s" % (current_ask_price, order_price))
                    stl_flag = True

        return stl_flag

    def setExpantionIndicator(self, base_time):
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


    def setVolatilityIndicator(self, base_time):
        self.volatility_buy_price, self.volatility_bid_price = getVolatilityPriceWrapper(self.instrument, base_time, span=60, connector=self.mysql_connector)

    def getDailySlope(self, instrument, base_time, span, connector):
        price_list = []
        target_time = base_time.strftime("%Y-%m-%d 07:00:00")

        sql = "select ask_price, bid_price from %s_TABLE where insert_time < \'%s\' and insert_time like \'%% 06:59:59\' order by insert_time desc limit %s" % (instrument, target_time, span)

        response = connector.select_sql(sql)
        for res in response:
            price = (res[0] + res[1]) / 2
            price_list.append(price)


        price_list.reverse()
        slope = getSlope(price_list)

        return slope


    def setDailyIndicator(self, base_time):
        hour = base_time.hour
        minute = base_time.minute
        second = base_time.second
        if hour == 7 and minute == 0 and second <= 10:
            self.daily_slope = self.getDailySlope(self.instrument, base_time, span=10, connector=self.mysql_connector)
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
            self.result_logger.info("# volatility_buy_price=%s" % self.volatility_buy_price)
            self.result_logger.info("# volatility_bid_price=%s" % self.volatility_bid_price)
            self.result_logger.info("# current_price=%s" % current_price)


    def writeExpantionLog(self, current_price, mode, highlow_mode):
        if mode == "trade":
            self.result_logger.info("#######################################################")
            self.result_logger.info("# in Expantion Algorithm")
            self.result_logger.info("# self.count_threshold=%s" %  self.count_threshold)
            self.result_logger.info("# self.daily_slope=%s" % self.daily_slope)
            self.result_logger.info("# self.buy_count=%s" %  self.buy_count)
            self.result_logger.info("# self.sell_count=%s" %  self.sell_count)

