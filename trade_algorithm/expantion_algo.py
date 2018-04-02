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

    def decideTrade(self, base_time):
        trade_flag = "pass"
        try:
            if self.order_flag:
                pass
            else:
                minutes = base_time.minute
                seconds = base_time.second
                # 1分足の終値付近で計算ロジックに入る
                if minutes % 5 == 4 and seconds >= 50:
                    self.debug_logger.info("%s :TrendExpantionLogic START" % base_time)
                    # 性能的に5分に一回呼び出しに変更
                    self.setIndicator(base_time)
                    current_price = self.getCurrentPrice()
                    trade_flag = self.decideExpantionTrade(trade_flag, current_price)

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
                    current_price = self.getCurrentPrice()
                    # 5分足の終値付近で計算ロジックに入る
                    if minutes % 5 == 4 and seconds >= 50:
                        self.debug_logger.info("%s :ExpantionStlLogic START" % base_time)
                        self.setIndicator(base_time)
                        stl_flag = self.decideExpantionStopLoss(stl_flag, current_price)
                    # 1時間ごとにやる
                    if minutes == 0 and seconds >= 50:
                        self.debug_logger.info("%s :ExpantionStlLogic START" % base_time)
                        self.setIndicator(base_time)
                        stl_flag = self.decideExpantionTakeProfit(stl_flag, current_price)

                    # trailなので毎回
                    stl_flag = self.decideTrailLogic(stl_flag, self.ask_price, self.bid_price, current_price)
            else:
                pass

            return stl_flag
        except:
            raise

    def decideExpantionTakeProfit(self, stl_flag, current_price):
        # Stop Loss Algorithm
        order_price = self.getOrderPrice()
        min_take_profit = 0.7

        # bollinger 逆側の向きが変わったら
        if self.order_kind == "buy":
            if (self.bid_price - order_price) > min_take_profit and self.bollinger1h3_lower_sigma_slope > 0:
                self.result_logger.info("# EXECUTE STLMENT at Take Profit")
                self.result_logger.info("# current_bid_price=%s, order_price=%s, min_take_profit=%s" % (self.bid_price, order_price, min_take_profit))
                self.result_logger.info("# bollinger1h3_lower_sigma_slope=%s" % (self.bollinger1h3_lower_sigma_slope))
                stl_flag = True
        elif self.order_kind == "sell":
            if (order_price - self.ask_price) > min_take_profit and self.bollinger1h3_upper_sigma_slope < 0:
                self.result_logger.info("# EXECUTE STLMENT at Take Profit")
                self.result_logger.info("# current_ask_price=%s, order_price=%s, min_take_profit=%s" % (self.ask_price, order_price, min_take_profit))
                self.result_logger.info("# bollinger1h3_upper_sigma_slope=%s" % (self.bollinger1h3_upper_sigma_slope))
                stl_flag = True

        return stl_flag

    def decideExpantionStopLoss(self, stl_flag, current_price):
        # 損切り逆方向にタッチしたら
        order_price = self.getOrderPrice()
        if self.order_kind == "buy":
            if current_price < self.lower_sigma_5m3:
                stl_flag = True
                self.result_logger.info("# EXECUTE STLEMENT at Reverse Stl mode")
        elif self.order_kind == "sell":
            if current_price > self.upper_sigma_5m3:
                stl_flag = True
                self.result_logger.info("# EXECUTE STLEMENT at Reverse Stl mode")

        return stl_flag

    def decideExpantionTrade(self, trade_flag, current_price):
        # Buy Logic at Trend Follow Mode

        # slopeは上を向いている場合は買いエントリしない。下を向いている場合は売りエントリしない
#        if (self.upper_sigma_1h3 - self.lower_sigma_1h3) > 1 and (self.upper_sigma_1h3 - self.lower_sigma_1h3) < 2:
        if (self.upper_sigma_1h3 - self.lower_sigma_1h3) < 2:
            if current_price > (self.upper_sigma_5m3) and self.slope > 0.01:
#                if self.order_history != "buy" or self.profit_history != "l":
                 if self.buy_count >= 1:
                    trade_flag = "buy"
                    self.result_logger.info("#######################################################")
                    self.result_logger.info("# decideExpantionTrade: BUY")
                    self.result_logger.info("# upper_sigma_1h3=%s , lower_sigma_1h3=%s" % (self.upper_sigma_1h3, self.lower_sigma_1h3))
                    self.result_logger.info("# current_price=%s, upper_sigma_5m3=%s" % (current_price, self.upper_sigma_5m3))
                    self.result_logger.info("# slope=%s" % (self.slope))
                 else:
                    self.buy_count = self.buy_count + 1
                    self.sell_count = 0
                 
            elif current_price < (self.lower_sigma_5m3) and self.slope < -0.01:
#                if self.order_history != "sell" or self.profit_history != "l":
                if self.sell_count >= 1:
                    trade_flag = "sell"
                    self.result_logger.info("#######################################################")
                    self.result_logger.info("# decideExpantionTrade: SELL")
                    self.result_logger.info("# upper_sigma_1h3=%s , lower_sigma_1h3=%s" % (self.upper_sigma_1h3, self.lower_sigma_1h3))
                    self.result_logger.info("# current_price=%s, lower_sigma_5m3=%s" % (current_price, self.lower_sigma_5m3))
                    self.result_logger.info("# slope=%s" % (self.slope))
                else:
                    self.sell_count = self.sell_count + 1
                    self.buy_count = 0
            else:
                pass
        else:
            pass

        return trade_flag

    def decideTrailLogic(self, stl_flag, current_ask_price, current_bid_price, current_price):
        order_price = self.getOrderPrice()
        first_flag = self.config_data["first_trail_mode"]
        second_flag = self.config_data["second_trail_mode"]
        first_take_profit = 0.3
        second_take_profit = 0.5
        trail_take_profit = 0.1


        if first_flag == "on":
            # 最小利確0.3を超えたら、トレールストップモードをONにする
            if self.order_kind == "buy":
                if (current_bid_price - order_price) > first_take_profit:
                    self.trail_flag = True
            elif self.order_kind == "sell":
                if (order_price - current_ask_price) > first_take_profit:
                    self.trail_flag = True


            # trail_flagがONで、含み益がなくなったら決済する
            if self.trail_flag == True and self.order_kind == "buy":
                if (current_bid_price - order_price) < trail_take_profit:
                    self.result_logger.info("# Execute Trail Stop")
                    self.result_logger.info("# current_bid_price=%s, order_price=%s" % (current_bid_price, order_price))
                    stl_flag = True
            elif self.trail_flag == True and self.order_kind == "sell":
                if (order_price - current_ask_price) < trail_take_profit:
                    self.result_logger.info("# Execute Trail Stop")
                    self.result_logger.info("# current_ask_price=%s, order_price=%s" % (current_ask_price, order_price))
                    stl_flag = True


        if second_flag == "on":
            # 含み益0.5超えたら、トレールストップの二段階目をONにする
            if self.order_kind == "buy":
                if (current_bid_price - order_price) > second_take_profit:
                    self.trail_second_flag = True
            elif self.order_kind == "sell":
                if (order_price - current_ask_price) > second_take_profit:
                    self.trail_second_flag = True


            # second_flagがTrueで且つ、含み益が0.3以下になったら決済する
            if self.trail_second_flag == True and self.order_kind == "buy":
                if (current_bid_price - order_price) < 0.3:
                    stl_flag = True
            elif self.trail_second_flag == True and self.order_kind == "sell":
                if (order_price - current_ask_price) < 0.3:
                    stl_flag = True

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
