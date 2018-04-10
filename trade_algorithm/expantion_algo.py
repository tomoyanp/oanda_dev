# coding: utf-8
####################################################
# トレード判断
# bollinger 1h3sigmaの幅が1.5以下（expantionの判定）
# bollinger 5m3+0.1の突破
#
# 損切り判断
# １）とりあえず0.3に設定
#
# 利確判断
# １）含み益が最低利益(30pips)を確保しているか確認
# ２）現在価格が移動平均線にタッチしたら決済する
# ３）リミットオーダーは1.0
####################################################

from super_algo import SuperAlgo
from common import instrument_init, account_init, decideMarket, getBollingerDataSet, extraBollingerDataSet, getEWMA, countIndex, getSlope, getOriginalEWMA
from mysql_connector import MysqlConnector
from datetime import datetime, timedelta
from logging import getLogger, FileHandler, DEBUG
import pandas as pd
import decimal


class ExpantionAlgo(SuperAlgo):
    def __init__(self, instrument, base_path, config_name, base_time):
        super(ExpantionAlgo, self).__init__(instrument, base_path, config_name, base_time)
        self.base_price = 0
        self.setPrice(base_time)
        self.setIndicator(base_time)
        self.debug_logger = getLogger("debug")
        self.result_logger = getLogger("result")
        self.slope = 0
        self.mysql_connector = MysqlConnector()
        self.first_flag = self.config_data["first_trail_mode"]
        self.second_flag = self.config_data["second_trail_mode"]
        self.most_high_price = 0
        self.most_low_price = 0

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
                # 4 ~ 14時は除外
                if hour < 4 or hour > 14:
#                if 0==0:
                    # 1分足の終値付近で計算ロジックに入る
                    if minutes % 5 == 0 and seconds <= 10:
                        self.debug_logger.info("%s :TrendExpantionLogic START" % base_time)
                        # 性能的に5分に一回呼び出しに変更
                        self.setIndicator(base_time)
                        current_price = self.getCurrentPrice()
                        trade_flag = self.decideExpantionTrade(trade_flag, current_price)

                    # 土曜の5時以降はエントリーしない
                    if weekday == 5 and hour >= 5:
                        trade_flag = "pass"
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
                    minutes = base_time.minute
                    seconds = base_time.second
                    weekday = base_time.weekday()
                    hour = base_time.hour
                    current_price = self.getCurrentPrice()
                    # 5分足の終値付近で計算ロジックに入る
                    if minutes % 5 == 0 and seconds <= 10:
                        self.debug_logger.info("%s :ExpantionStlLogic START" % base_time)
                        self.setIndicator(base_time)
                        stl_flag = self.decideExpantionStopLoss(stl_flag, current_price)
                        stl_flag = self.decideTrailLogic(stl_flag, self.ask_price, self.bid_price, current_price)
                    # 1時間ごとにやる
                    if minutes == 0 and seconds >= 50:
                        self.debug_logger.info("%s :ExpantionStlLogic START" % base_time)
                        #self.setIndicator(base_time)
                        stl_flag = self.decideExpantionTakeProfit(stl_flag, current_price)

                    # 土曜の5時以降にポジションを持っている場合は決済する
                    if weekday == 5 and hour >= 5:
                        self.result_logger.info("weekend stl logic")
                        stl_flag = True
            else:
                pass

            return stl_flag
        except:
            raise

    def decideExpantionTakeProfit(self, stl_flag, current_price):

        return stl_flag

    def decideExpantionStopLoss(self, stl_flag, current_price):
        order_price = self.getOrderPrice()

        if (self.upper_sigma_1h3 - self.lower_sigma_1h3) < 2:
            if current_price > (self.upper_sigma_5m3) and self.slope > 0.01:
                self.buy_count = self.buy_count + 1
                self.sell_count = 0

            elif current_price < (self.lower_sigma_5m3) and self.slope < -0.01:
                self.sell_count = self.sell_count + 1
                self.buy_count = 0
            else:
                pass

        if float(self.volatility_buy_price) + float(0.5) < current_price and self.order_kind == "sell":
            stl_flag = True
            self.result_logger.info("# Execute Volatility Settlement")
            self.result_logger.info("# volatility_buy_price=%s, current_price=%s" % (self.volatility_buy_price, current_price))
            self.buy_count = 0
            self.sell_count = 0
        elif float(self.volatility_bid_price) - float(0.5) > current_price and self.order_kind == "buy":
            stl_flag = True
            self.result_logger.info("# Execute Volatility Settlement")
            self.result_logger.info("# volatility_bid_price=%s, current_price=%s" % (self.volatility_bid_price, current_price))
            self.buy_count = 0
            self.sell_count = 0

        if self.buy_count >= 2 and self.order_kind == "sell":
            if current_price < (float(self.high_price) - float(0.5)) or (float(self.high_price) + float(0.5)) < current_price:
                stl_flag = True
                self.result_logger.info("# Execute Reverse Settlement")
                self.result_logger.info("# upper_sigma_1h3=%s , lower_sigma_1h3=%s" % (self.upper_sigma_1h3, self.lower_sigma_1h3))
                self.result_logger.info("# current_price=%s, upper_sigma_5m3=%s" % (current_price, self.upper_sigma_5m3))
                self.result_logger.info("# slope=%s" % (self.slope))
            else:
                self.buy_count = 0
                self.sell_count = 0

        elif self.sell_count >= 2 and self.order_kind == "buy":
            if (float(self.low_price) + float(0.5)) < current_price or current_price < (float(self.low_price) - float(0.5)):
                stl_flag = True
                self.result_logger.info("# Execute Reverse Settlement")
                self.result_logger.info("# upper_sigma_1h3=%s , lower_sigma_1h3=%s" % (self.upper_sigma_1h3, self.lower_sigma_1h3))
                self.result_logger.info("# current_price=%s, lower_sigma_5m3=%s" % (current_price, self.lower_sigma_5m3))
                self.result_logger.info("# slope=%s" % (self.slope))
            else:
                self.buy_count = 0
                self.sell_count = 0

        self.debug_logger.info("order_kind = %s" % self.order_kind)
        self.debug_logger.info("buy_count = %s" % self.buy_count)
        self.debug_logger.info("sell_count = %s" % self.sell_count)

        return stl_flag

    def decideExpantionTrade(self, trade_flag, current_price):
        # Buy Logic at Trend Follow Mode
        # slopeは上を向いている場合は買いエントリしない。下を向いている場合は売りエントリしない
        if (self.upper_sigma_1h3 - self.lower_sigma_1h3) < 2:
            if current_price > (self.upper_sigma_5m3) and self.slope > 0.01:
                self.buy_count = self.buy_count + 1
                self.sell_count = 0

            elif current_price < (self.lower_sigma_5m3) and self.slope < -0.01:
                self.sell_count = self.sell_count + 1
                self.buy_count = 0
            else:
                pass

        if float(self.volatility_buy_price) + float(0.5) < current_price:
            trade_flag = "buy"
            self.result_logger.info("#######################################################")
            self.result_logger.info("# decideExpantionTrade: BUY at volatility_price")
            self.result_logger.info("# volatility_buy_price=%s, current_price=%s" % (self.volatility_buy_price, current_price))
            self.debug_logger.info("volatility_price + 0.5 = %s, current_price=%s" % (float(self.volatility_buy_price) + float(0.5), current_price))
            self.buy_count = 0
            self.sell_count = 0
        elif float(self.volatility_bid_price) - float(0.5) > current_price:
            trade_flag = "sell"
            self.result_logger.info("#######################################################")
            self.result_logger.info("# decideExpantionTrade: SELL at volatility_price")
            self.result_logger.info("# volatility_bid_price=%s, current_price=%s" % (self.volatility_bid_price, current_price))
            self.debug_logger.info("volatility_price - 0.5 = %s, current_price=%s " % (float(self.volatility_buy_price) + float(0.5), current_price))
            self.buy_count = 0
            self.sell_count = 0

        if self.buy_count >= 2:
            if current_price < (float(self.high_price) - float(0.5)) or (float(self.high_price) + float(0.5)) < current_price:
                trade_flag = "buy"
                self.result_logger.info("#######################################################")
                self.result_logger.info("# decideExpantionTrade: BUY")
                self.result_logger.info("# upper_sigma_1h3=%s , lower_sigma_1h3=%s" % (self.upper_sigma_1h3, self.lower_sigma_1h3))
                self.result_logger.info("# current_price=%s, upper_sigma_5m3=%s" % (current_price, self.upper_sigma_5m3))
                self.result_logger.info("# slope=%s" % (self.slope))
                self.buy_count = 0
                self.sell_count = 0

        elif self.sell_count >= 2:
            if current_price < (float(self.low_price) - float(0.5)) or (float(self.low_price) + float(0.5)) < current_price:
                trade_flag = "sell"
                self.result_logger.info("#######################################################")
                self.result_logger.info("# decideExpantionTrade: SELL")
                self.result_logger.info("# upper_sigma_1h3=%s , lower_sigma_1h3=%s" % (self.upper_sigma_1h3, self.lower_sigma_1h3))
                self.result_logger.info("# current_price=%s, lower_sigma_5m3=%s" % (current_price, self.lower_sigma_5m3))
                self.result_logger.info("# slope=%s" % (self.slope))
                self.buy_count = 0
                self.sell_count = 0

        else:
            pass

        return trade_flag

#    def resetFlag(self):
#        super(ExpantionAlgo, self)
#        self.most_high_price = 0
#        self.most_low_price = 0

    def decideTrailLogic(self, stl_flag, current_ask_price, current_bid_price, current_price):
        order_price = self.getOrderPrice()
        first_take_profit = 0.5
        second_take_profit = 1.0
        trail_take_profit = 0

        if self.most_high_price == 0 and self.most_low_price == 0:
            self.most_high_price = order_price
            self.most_low_price = order_price

        if self.most_high_price < current_bid_price:
            self.most_high_price = current_bid_price
        if self.most_low_price > current_ask_price:
            self.most_low_price = current_ask_price


        if self.first_flag == "on":
            # 最小利確0.5を超えたら、トレールストップモードをONにする
            if self.order_kind == "buy":
                if (current_bid_price - order_price) > first_take_profit:
                    self.trail_flag = True
            elif self.order_kind == "sell":
                if (order_price - current_ask_price) > first_take_profit:
                    self.trail_flag = True

            # trail_flagがONで、含み益がなくなったら決済する
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


        if self.second_flag == "on":
            # 含み益0.5超えたら、トレールストップの二段階目をONにする
            if self.order_kind == "buy":
                if (current_bid_price - order_price) > second_take_profit:
                    self.trail_second_flag = True
            elif self.order_kind == "sell":
                if (order_price - current_ask_price) > second_take_profit:
                    self.trail_second_flag = True

            # trail_flagがONで、含み益がなくなったら決済する
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

#        if first_flag == "on":
#            # 最小利確0.3を超えたら、トレールストップモードをONにする
#            if self.order_kind == "buy":
#                if (current_bid_price - order_price) > first_take_profit:
#                    self.trail_flag = True
#            elif self.order_kind == "sell":
#                if (order_price - current_ask_price) > first_take_profit:
#                    self.trail_flag = True
#
#
#            # trail_flagがONで、含み益がなくなったら決済する
#            if self.trail_flag == True and self.order_kind == "buy":
#                if (current_bid_price - order_price) < trail_take_profit:
#                    self.result_logger.info("# Execute Trail Stop")
#                    self.result_logger.info("# current_bid_price=%s, order_price=%s" % (current_bid_price, order_price))
#                    stl_flag = True
#            elif self.trail_flag == True and self.order_kind == "sell":
#                if (order_price - current_ask_price) < trail_take_profit:
#                    self.result_logger.info("# Execute Trail Stop")
#                    self.result_logger.info("# current_ask_price=%s, order_price=%s" % (current_ask_price, order_price))
#                    stl_flag = True
#
#
#        if second_flag == "on":
#            # 含み益0.5超えたら、トレールストップの二段階目をONにする
#            if self.order_kind == "buy":
#                if (current_bid_price - order_price) > second_take_profit:
#                    self.trail_second_flag = True
#            elif self.order_kind == "sell":
#                if (order_price - current_ask_price) > second_take_profit:
#                    self.trail_second_flag = True
#
#
#            # second_flagがTrueで且つ、含み益が0.3以下になったら決済する
#            if self.trail_second_flag == True and self.order_kind == "buy":
#                if (current_bid_price - order_price) < 0.3:
#                    stl_flag = True
#            elif self.trail_second_flag == True and self.order_kind == "sell":
#                if (order_price - current_ask_price) < 0.3:
#                    stl_flag = True

        return stl_flag

    def setSlope(self, base_time):
        sql = "select base_line from INDICATOR_TABLE where instrument = \'%s\' and type = \'bollinger1h3\' and insert_time <= \'%s\' order by insert_time desc limit 5" % (self.instrument, base_time)
        response = self.mysql_connector.select_sql(sql)
        base_line_list = []
        for res in response:
            print res
            base_line_list.append(res[0])

        base_line_list.reverse()
        self.slope = getSlope(base_line_list)

    def setIndicator(self, base_time):
        self.setBollinger5m3(base_time)
        self.setBollinger1h3(base_time)
        self.setSlopeBollinger1h3(base_time)
        self.setSlope(base_time)
        self.setVolatilityPrice(base_time)
        self.setHighlowPrice(base_time, 24)
