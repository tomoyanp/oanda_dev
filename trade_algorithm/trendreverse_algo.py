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


class TrendReverseAlgo(SuperAlgo):
    def __init__(self, instrument, base_path, config_name, base_time):
        super(TrendReverseAlgo, self).__init__(instrument, base_path, config_name, base_time)
        self.base_price = 0
        self.setPrice(base_time)
        self.setIndicator(base_time)

    def decideTrade(self, base_time):
        trade_flag = "pass"
        try:
            if self.order_flag:
                pass
            else:
                minutes = base_time.minute
                seconds = base_time.second

                # 1分足の終値付近で計算ロジックに入る
                if seconds > 50:
#                if minutes % 5 == 4 and seconds > 50:
                    logging.info("%s :TrendReverseTradeLogic START" % base_time)
                    self.setIndicator(base_time)
                    current_price = self.getCurrentPrice()
                    trade_flag = self.decideTrendReverseTrade(trade_flag, current_price)

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

#                    if seconds > 50:
                    if seconds >= 0:
                        logging.info("%s :TrendReverseStlLogic START" % base_time)
                        self.setIndicator(base_time)
                        stl_flag = self.decideTrendReverseStlTakeProfit(stl_flag, current_price)

#                    if minutes % 5 == 4 and seconds > 50:
                    if seconds > 50:
                        logging.info("%s :TrendReverseStlLogic START" % base_time)
                        self.setIndicator(base_time)
                        stl_flag = self.decideTrendReverseStlStopOrder(stl_flag, current_price)
            else:
                pass

            return stl_flag
        except:
            raise


    def decideTrendReverseStlTakeProfit(self, stl_flag, current_price):
        if self.order_kind == "buy":
            if current_price > self.upper_sigma_1m25:
                logging.info("EXECUTE STLEMENT at Trend Reverse Mode")
                stl_flag = True

        elif self.order_kind == "sell":
            if current_price < self.lower_sigma_1m25:
                logging.info("EXECUTE STLEMENT at Trend Reverse Mode")
                stl_flag = True

        logging.info("upper_sigma_1m3 = %s, lower_sigma_1m3 = %s, order_kind = %s, stl_flag = %s" %(self.upper_sigma_1m3, self.lower_sigma_1m3, self.order_kind, stl_flag))

        return stl_flag

    def decideTrendReverseStlStopOrder(self, stl_flag, current_price):
        # Stop Loss Algorithm
        if self.order_kind == "buy":
            if current_price < self.lower_sigma_1m3:
                logging.info("EXECUTE STLEMENT at Trend Reverse Mode")
                stl_flag = True

        elif self.order_kind == "sell":
            if current_price > self.upper_sigma_1m3:
                logging.info("EXECUTE STLEMENT at Trend Reverse Mode")
                stl_flag = True

        logging.info("upper_sigma_1m3 = %s, lower_sigma_1m3 = %s, order_kind = %s, stl_flag = %s" %(self.upper_sigma_1m3, self.lower_sigma_1m3, self.order_kind, stl_flag))

        return stl_flag

    def decideTrendReverseTrade(self, trade_flag, current_price):
        # bollingerバンド3シグマの幅が2以下、かつewma200の上にいること
        if (self.upper_sigma_1h3 - self.lower_sigma_1h3) < 2:
            logging.info("bollinger 3 sigma logic: OK, upper_sigma_1h3 = %s, lower_sigma_1h3 = %s, upper_sigma - lower_sigma = %s" % (self.upper_sigma_1h3, self.lower_sigma_1h3, (self.upper_sigma_1h3 - self.lower_sigma_1h3)))
#            if current_price > self.upper_sigma_1m25:
            if current_price > self.upper_sigma_1m25 and current_price < self.ewma5m200_value:
                logging.info("upper_sigma logic: OK, current_price = %s, upper_sigma_1m25 = %s" % (current_price, self.upper_sigma_1m25))
                logging.info("EXECUTE ORDER SELL at Trend Reverse Mode")
                trade_flag = "sell" # 逆張り
            else:
                logging.info("upper_sigma logic: NG, current_price = %s, upper_sigma_1m25 = %s" % (current_price, self.upper_sigma_1m25))
        else:
            logging.info("bollinger 3 sigma logic: NG, upper_sigma_1h3 = %s, lower_sigma_1h3 = %s, upper_sigma - lower_sigma = %s" % (self.upper_sigma_1h3, self.lower_sigma_1h3, (self.upper_sigma_1h3 - self.lower_sigma_1h3)))


        # bollingerバンド3シグマの幅が2以下、かつewma200の下にいること
        if (self.upper_sigma_1h3 - self.lower_sigma_1h3) < 2:
            logging.info("bollinger 3 sigma logic: OK, upper_sigma_1h3 = %s, lower_sigma_1h3 = %s, upper_sigma - lower_sigma = %s" % (self.upper_sigma_1h3, self.lower_sigma_1h3, (self.upper_sigma_1h3 - self.lower_sigma_1h3)))
#            if current_price < self.lower_sigma_1m25:
            if current_price < self.lower_sigma_1m25 and current_price > self.ewma5m200_value:
                logging.info("lower_sigma logic: OK, current_price = %s, lower_sigma_1m25 = %s" % (current_price, self.lower_sigma_1m25))
                logging.info("EXECUTE ORDER BUY at Trend Reverse Mode")
                trade_flag = "buy"
            else:
                logging.info("lower_sigma logic: NG, current_price = %s, lower_sigma_1m25 = %s" % (current_price, self.lower_sigma_1m25))
        else:
            logging.info("bollinger 3 sigma logic: NG, upper_sigma_1h3 = %s, lower_sigma_1h3 = %s, upper_sigma - lower_sigma = %s" % (self.upper_sigma_1h3, self.lower_sigma_1h3, (self.upper_sigma_1h3 - self.lower_sigma_1h3)))

        return trade_flag

    def decideTrailLogic(self, stl_flag, current_ask_price, current_bid_price, current_price, order_price):
        first_flag = self.config_data["first_trail_mode"]
        second_flag = self.config_data["second_trail_mode"]
        first_take_profit = 0.2
        second_take_profit = 0.3


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
        self.setBollinger1h3(base_time)
        self.setEwma5m200(base_time)
