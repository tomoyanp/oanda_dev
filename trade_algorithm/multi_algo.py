# coding: utf-8
####################################################
# トレード判断
#　5分足 × 50移動平均のslopeが閾値(0.3)以上の時（トレンド発生と判断）
#　現在価格と5分足 200日移動平均線の比較（上にいれば買い、下にいれば売り）
#  現在価格の5分足終わり値が、ボリンジャーバンド2.5シグマにタッチすること
#
# 損切り判断
# １）反対側へのトレード判断がTrueの場合決済
#
# 利確判断
# １）含み益が最低利益(30pips)を確保しているか確認
# ２）現在価格が移動平均線にタッチしたら決済する
# ３）リミットオーダーは1.0
####################################################

from super_algo import SuperAlgo
from common import instrument_init, account_init, decideMarket, getBollingerDataSet, extraBollingerDataSet, getEWMA, countIndex, getSlope, getOriginalEWMA
from datetime import datetime, timedelta
import logging
import pandas as pd
import decimal


class TrendFollowAlgo(SuperAlgo):
    def __init__(self, instrument, base_path, config_name, base_time):
        super(TrendFollowAlgo, self).__init__(instrument, base_path, config_name, base_time)
        self.base_price = 0
        self.setPrice(base_time)
        self.setIndicator(base_time)

    def decideTrade(self, base_time):
        trade_flag = "pass"
        trade_mode = "null"
        try:
            if self.order_flag:
                pass
            else:
                minutes = base_time.minute
                seconds = base_time.second
                # 5分足の終値付近で計算ロジックに入る
                if (minutes % 5 == 4) and seconds > 50:
                    # 性能的に5分に一回呼び出しに変更
                    self.setIndicator(base_time)
                    current_price = self.getCurrentPrice()
                    trade_flag, trade_mode = self.decideTrendFollowMode(trade_flag, trade_mode, current_price)


                # 1分足の終値付近で計算ロジックに入る
                elif seconds > 50 and trade_flag == "pass":
                    self.setIndicator(base_time)
                    trade_flag, trade_mode = self.reverseTradeMode(trade_flag, trade_mode, current_price)

            return trade_flag, trade_mode

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
                    if (minutes % 5 == 4) and seconds > 50 and self.trade_mode == "follow":
                        self.setIndicator(base_time)
                        stl_flag = self.decideTrendFollowStl(stl_flag, current_price)

                    elif seconds > 50 and self.trade_mode == "reverse":
                        self.setIndicator(base_time, stl_flag)
                        stl_flag = self.decideTrendFollowStl(stl_flag, current_price)
            else:
                pass

            return stl_flag
        except:
            raise

    def decideTrendReverseStl(self, stl_flag, current_price):
        # Stop Loss Algorithm
        if self.order_kind == "buy":
            if current_price < self.lower_sigma_1m3:
                stl_flag = True
            elif current_price > self.upper_sigma_1m25:
                stl_flag = True

        elif self.order_kind == "sell":
            if current_price > self.upper_sigma_1m3:
                stl_flag = True
            elif current_price < self.lower_sigma_1m25:
                stl_flag = True

        logging.info("######### decideStl Logic base_time = %s ##########" % base_time)
        logging.info("upper_sigma1m25 = %s, current_price = %s, lower_sigma1m25 = %s" %(self.upper_sigma_1m25, current_price, self.lower_sigma_1m25))
        logging.info("upper_sigma1m3 = %s,lower_sigma1m3 = %s" %(self.upper_sigma_1m3, self.lower_sigma_1m3))

        return stl_flag

    def decideTrendFollowStl(self, stl_flag, current_price):
        # Stop Loss Algorithm
        order_price = self.getOrderPrice()

        # 最小利確0.3以上、移動平均にぶつかったら
        min_take_profit = 0.3
        if self.order_kind == "buy":
            if (self.bid_price - order_price) > min_take_profit:
                if -0.02 < (current_price - self.base_line_5m25) < 0.02:
                    logging.info("EXECUTE STL")
                    stl_flag = True
        elif self.order_kind == "sell":
            if (order_price - self.ask_price) > min_take_profit:
                if -0.02 < (current_price - self.base_line_5m25) < 0.02:
                    logging.info("EXECUTE STL")
                    stl_flag = True

        stl_flag = self.decideTrailLogic(stl_flag, self.ask_price, self.bid_price, current_price, order_price)
        logging.info("######### decideStl Logic base_time = %s ##########" % base_time)
        logging.info("upper_sigma = %s, current_price = %s, lower_sigma = %s, base_line = %s" %(self.upper_sigma_5m25, current_price, self.lower_sigma_5m25, self.base_line_5m25))
        logging.info("order_price = %s, slope = %s" %(order_price, self.ewma5m50_slope))

        return stl_flag

    def decideTrendFollowMode(self, trade_flag, trade_mode, current_price):
        hilow_price_threshold = 0.5
        low_slope_threshold  = -0.3
        high_slope_threshold = 0.3

        # slopeが上向き、現在価格が移動平均(EWMA200(5分), EWMA200(1時間))より上、現在価格がbollinger3_sigmaより上にいる
        if ((self.ewma5m50_slope - high_slope_threshold) > 0) and (self.ewma5m200_value < current_price) and (current_price > self.upper_sigma_5m25) and (current_price - self.ewma1h200_value) > 0.1 and (self.upper_sigma_1h3 - self.lower_sigma_1h3) > 2:
            # 現在価格が前日高値に対し0.5以内にいる or 当日の値動きが1.0以上ある場合、トレードしない
            if float(self.high_price - hilow_price_threshold) < float(current_price) < (float(self.high_price) + 0.1):
                self.break_wait_flag = "buy"
                logging.info("MOVING RANGE BREAK MODE = buy")
            else:
                trade_flag = "buy"
                trade_mode = "follow"
        # slopeが下向き、現在価格が移動平均(EWMA200(5分), EWMA200(1時間)より下、現在価格がbollinger3_sigmaより下にいる
        elif (self.ewma5m50_slope - low_slope_threshold) < 0 and self.ewma5m200_value > current_price and current_price < self.lower_sigma_5m25 and (self.ewma1h200_value - current_price) > 0.1 and (self.upper_sigma_1h3 - self.lower_sigma_1h3) > 2:
            # 現在価格が前日安値に対し0.5以内にいる or 当日の値動きが1.0以上ある場合、トレードしない
            if float(self.low_price + hilow_price_threshold) > float(current_price) > (float(self.low_price) - 0.1):
                self.break_wait_flag = "sell"
                logging.info("MOVING RANGE BREAK MODE = sell")
            else:
                trade_flag = "sell"
                trade_mode = "follow"

        else:
            trade_flag = "pass"

        logging.info("####### decideTrade Logic base_time = %s #######" % base_time)
        logging.info("break_wait_flag = %s" % (self.break_wait_flag))
        logging.info("hi_price = %s, low_price = %s" % (self.high_price, self.low_price))
        logging.info("5m 50ewma slope = %s, 5m 200ewma = %s, 1h 200ewma = %s, current_price = %s, upper_2.5sigma = %s, lower_2.5sigma = %s, trade_flag = %s" % (self.ewma5m50_slope, self.ewma5m200_value, self.ewma1h200_value, current_price, self.upper_sigma_5m25, self.lower_sigma_5m25, trade_flag))
        logging.info("upper 1h 3sigma = %s, lower 1h 3sigma = %s upper_sigma - lower_sigma = %s" % (self.upper_sigma_1h3, self.lower_sigma_1h3, (self.upper_sigma_1h3 - self.lower_sigma_1h3)))

        return trade_flag, trade_mode

    def decideReverseTrade(self, trade_flag, trade_mode, current_price):
         # bollingerバンド3シグマの幅が2以下、かつewma200の上にいること
         if (self.upper_sigma_1h3 - self.lower_sigma_1h3) < 2:
             if current_price > self.upper_sigma_1m25:
                 trade_flag = "sell" # 逆張り

         # bollingerバンド3シグマの幅が2以下、かつewma200の下にいること
         if (self.upper_sigma_1h3 - self.lower_sigma_1h3) < 2:
             if current_price < self.lower_sigma_1m25:
                 trade_flag = "buy"
         else:
             trade_flag = "pass"

         logging.info("####### decideTrade Logic base_time = %s #######" % base_time)
        logging.info("5m 200ewma = %s, current_price = %s, upper_2.5sigma = %s, lower_2.5sigma = %s, trade_flag = %s" % (self.ewma5m200_value, current_price, self.upper_sigma_1m25, self.lower_sigma_1m25, trade_flag))
        logging.info("upper 1h 3sigma = %s, lower 1h 3sigma = %s upper_sigma - lower_sigma = %s" % (self.upper_sigma_1h3, self.lower_sigma_1h3, (self.upper_sigma_1h3 - self.lower_sigma_1h3)))

        return trade_flag, trade_mode

    def decideTrailLogic(self, stl_flag, current_ask_price, current_bid_price, current_price, order_price):
        first_flag = self.config_data["first_trail_mode"]
        second_flag = self.config_data["second_trail_mode"]
        first_take_profit = 0.3
        second_take_profit = 0.5


        if first_flag == "on":
            # 最小利確0.3を超えたら、トレールストップモードをONにする
            if self.order_kind == "buy":
                if (current_bid_price - order_price) > first_take_profit:
                    logging.info("SET TRAIL FIRST FLAG ON")
                    self.trail_flag = True
            elif self.order_kind == "sell":
                if (order_price - current_ask_price) > first_take_profit:
                    logging.info("SET TRAIL FIRST FLAG ON")
                    self.trail_flag = True


            # trail_flagがONで、含み益がなくなったら決済する
            if self.trail_flag == True and self.order_kind == "buy":
                if (current_bid_price - order_price) < 0:
                    logging.info("EXECUTE FIRST TRAIL STOP")
                    stl_flag = True
            elif self.trail_flag == True and self.order_kind == "sell":
                if (order_price - current_ask_price) < 0:
                    logging.info("EXECUTE FIRST TRAIL STOP")
                    stl_flag = True


        if second_flag == "on":
            # 含み益0.5超えたら、トレールストップの二段階目をONにする
            if self.order_kind == "buy":
                if (current_bid_price - order_price) > second_take_profit:
                    logging.info("SET TRAIL SECOND FLAG ON")
                    self.trail_second_flag = True
            elif self.order_kind == "sell":
                if (order_price - current_ask_price) > second_take_profit:
                    logging.info("SET TRAIL SECOND FLAG ON")
                    self.trail_second_flag = True


            # second_flagがTrueで且つ、含み益が0.3以下になったら決済する
            if self.trail_second_flag == True and self.order_kind == "buy":
                if (current_bid_price - order_price) < 0.3:
                    logging.info("EXECUTE TRAIL SECOND STOP")
                    stl_flag = True
            elif self.trail_second_flag == True and self.order_kind == "sell":
                if (order_price - current_ask_price) < 0.3:
                    logging.info("EXECUTE TRAIL SECOND STOP")
                    stl_flag = True

        return stl_flag

    def setIndicator(self, base_time):
        self.setBollinger1m25(base_time)
        self.setBollinger1m3(base_time)
        self.setBollinger5m25(base_time)
        self.setBollinger1h3(base_time)
        self.setEwma5m50(base_time)
        self.setEwma5m200(base_time)
        self.setEwma1h200(base_time)
        self.setHighlowPrice(base_time)


