# coding: utf-8
####################################################
# トレード判断
#　5分足 × 50移動平均のslopeが閾値(0.3)以上の時（トレンド発生と判断）
#　現在価格と5分足 200日移動平均線の比較（上にいれば買い、下にいれば売り）
#　現在価格が、前日（06:00-05:59）の高値、安値圏から0.5以上幅があること
#　　前日が陰線引けであれば、安値圏と比較
#　　前日が陽線引けであれば、高値圏と比較
#　当日の高値、安値の差が1.0以内であること
#　　下落幅が1.0以上であれば、売りはなし
#　　上昇幅が1.0以上であれべ、買いはなし
#  現在価格が、ボリンジャーバンド2.5シグマにタッチすること
#
# 損切り判断
# １）反対側の3シグマにヒットしたら決済する
#
# 利確判断
# １）含み益が最低利益(10pips)を確保しているか確認
# ２）現在価格が移動平均線にタッチしたら決済する
####################################################

from super_algo import SuperAlgo
from common import instrument_init, account_init, decideMarket, getBollingerDataSet, extraBollingerDataSet, getEWMA, countIndex, getSlope, getOriginalEWMA
from datetime import datetime, timedelta
import logging
import pandas as pd
import decimal


class Evo2BollingerAlgo(SuperAlgo):
    def __init__(self, instrument, base_path, config_name, base_time):
        super(Evo2BollingerAlgo, self).__init__(instrument, base_path, config_name, base_time)
        self.base_price = 0

    def decideTrade(self, base_time):
        trade_flag = "pass"
        try:
            if self.order_flag:
                pass
            else:
                current_price = self.getCurrentPrice()

                # 前日高値、安値の計算
                hi_price = self.hi_low_price_dataset["hi_price"]
                low_price = self.hi_low_price_dataset["low_price"]


                # 当日始め値と現在価格の差を取得(現在価格-始値)
                start_price = self.start_end_price_dataset["start_price"]
                end_price = self.start_end_price_dataset["end_price"]

                # 移動平均じゃなく、トレンド発生＋2.5シグマ突破でエントリーに変えてみる
                upper_sigma = self.bollinger_2p5sigma_dataset["upper_sigma"]
                lower_sigma = self.bollinger_2p5sigma_dataset["lower_sigma"]
                base_line = self.bollinger_2p5sigma_dataset["base_line"]

                ewma50 = self.ewma50_5m_dataset["ewma_value"]
                slope = self.ewma50_5m_dataset["slope"]
                ewma200 = self.ewma200_5m_dataset["ewma_value"]
                ewma200_1h = self.ewma200_1h_dataset["ewma_value"]

                startend_price_threshold = 1.0
                hilow_price_threshold = 0.5
                baseline_touch_flag = False
                low_slope_threshold  = -0.3
                high_slope_threshold = 0.3

                # 高値安値チェックのみに引っかかった場合、breakモードに突入する
                if self.break_wait_flag == "buy":
                    if (current_price - high_price) > 0.1:
                        logging.info("EXECUTE BUY RANGE BREAK MODE")
                        trade_flag = "buy"
                    else:
                        pass
                elif self.break_wait_flag == "sell":
                    if (low_price - current_price) > 0.1:
                        logging.info("EXECUTE SELL RANGE BREAK MODE")
                        trade_flag = "sell"
                    else:
                        pass
                else:
                    pass

                # slopeが上向き、現在価格が移動平均(EWMA200(5分), EWMA200(1時間))より上、現在価格がbollinger3_sigmaより上にいる
                if ((slope - high_slope_threshold) > 0) and (ewma200 < current_price) and (current_price > upper_sigma) and (ewma200_1h < current_price):
                    # 現在価格が前日高値に対し0.5以内にいる or 当日の値動きが1.0以上ある場合、トレードしない
                    if float(hi_price - hilow_price_threshold) < float(current_price) < float(hi_price):
                        self.break_wait_flag = "buy"
                        logging.info("MOVING RANGE BREAK MODE = buy")
                    else:
                        logging.info("EXECUTE BUY NORMAL MODE")
                        trade_flag = "buy"
                # slopeが下向き、現在価格が移動平均(EWMA200(5分), EWMA200(1時間)より下、現在価格がbollinger3_sigmaより下にいる
                elif ((slope - low_slope_threshold) < 0) and (ewma200 > current_price) and (current_price < lower_sigma) and (ewma200 > current_price):
                    # 現在価格が前日安値に対し0.5以内にいる or 当日の値動きが1.0以上ある場合、トレードしない
                    if float(low_price + hilow_price_threshold) > float(current_price) > float(low_price):
                        self.break_wait_flag = "sell"
                        logging.info("MOVING RANGE BREAK MODE = sell")
                    else:
                        logging.info("EXECUTE SELL NORMAL MODE")
                        trade_flag = "sell"
                else:
                    trade_flag = "pass"

                logging.info("####### decideTrade Logic base_time = %s #######" % base_time)
                logging.info("break_wait_flag = %s" % (self.break_wait_flag))
                logging.info("start_price = %s, end_price = %s" % (start_price, end_price))
                logging.info("hi_price = %s, low_price = %s" % (hi_price, low_price))
                logging.info("5m 50ewma slope = %s, 5m 200ewma = %s, 1h 200ewma = %s, current_price = %s, upper_2.5sigma = %s, lower_2.5sigma = %s, trade_flag = %s" % (slope, ewma200, ewma200_1h, current_price, upper_sigma, lower_sigma, trade_flag))

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

                    # Stop Loss Algorithm
                    # get Bollinger Band sigma 2.5
                    upper_sigma = self.bollinger_2p5sigma_dataset["upper_sigma"]
                    lower_sigma = self.bollinger_2p5sigma_dataset["lower_sigma"]
                    base_line = self.bollinger_2p5sigma_dataset["base_line"]

                    current_ask_price = self.ask_price_list[-1]
                    current_bid_price = self.bid_price_list[-1]
                    current_price = self.getCurrentPrice()
                    order_price = self.getOrderPrice()

                    # 買いの場合はlower_sigmaにぶつかったら決済
                    # 売りの場合はupper_sigmaにぶつかったら決済

                    # 移動平均の取得(WMA50)
                    ewma50 = self.ewma50_5m_dataset["ewma_value"]
                    slope = self.ewma50_5m_dataset["slope"]

                    low_slope_threshold  = -0.3
                    high_slope_threshold = 0.3

                    # 損切り
                    # slopeが上向き、現在価格がbollinger3_sigmaより上にいる
                    if ((slope - high_slope_threshold) > 0) and (current_price > upper_sigma) and self.order_kind == "sell":
                        logging.info("EXECUTE SETTLEMENT")
                        stl_flag = True
                    # slopeが下向き、現在価格がbollinger3_sigmaより下にいる
                    elif ((slope - low_slope_threshold) < 0) and (current_price < lower_sigma) and self.order_kind == "buy":
                        logging.info("EXECUTE SETTLEMENT")
                        stl_flag = True

                    # 最小利確0.3以上、移動平均にぶつかったら
                    min_take_profit = 0.3
                    if self.order_kind == "buy":
                        if (current_bid_price - order_price) > min_take_profit:
                            if -0.02 < (current_price - base_line) < 0.02:
                                logging.info("EXECUTE STL")
                                stl_flag = True
                    elif self.order_kind == "sell":
                        if (order_price - current_ask_price) > min_take_profit:
                            if -0.02 < (current_price - base_line) < 0.02:
                                logging.info("EXECUTE STL")
                                stl_flag = True


                    # 最小利確0.3を超えたら、トレールストップモードをONにする
                    if self.order_kind == "buy":
                        if (current_bid_price - order_price) > min_take_profit:
                            logging.info("SET TRAIL FLAG ON")
                            self.trail_flag = True
                    elif self.order_kind == "sell":
                        if (order_price - current_ask_price) > min_take_profit:
                            logging.info("SET TRAIL FLAG ON")
                            self.trail_flag = True

                    if self.trail_flag == True and self.order_kind == "buy":
                        if (current_bid_price - order_price) < 0:
                            logging.info("EXECUTE TRAIL STOP")
                            stl_flag = True
                    elif self.trail_flag == True and self.order_kind == "sell":
                        if (order_price - current_ask_price) < 0:
                            logging.info("EXECUTE TRAIL STOP")
                            stl_flag = True

                    logging.info("######### decideStl Logic base_time = %s ##########" % base_time)
                    logging.info("upper_sigma = %s, current_price = %s, lower_sigma = %s, base_line = %s" %(upper_sigma, current_price, lower_sigma, base_line))
                    logging.info("order_price = %s, slope = %s" %(order_price, slope))
            else:
                pass

            return stl_flag
        except:
            raise
