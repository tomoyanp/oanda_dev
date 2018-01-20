# coding: utf-8

####################################################
# トレード判断
# １）1h ewma21*10 のslopeを計算（閾値2.0）
#　２－１）slopeが閾値以内の時（もみ合いと判断）
#　３－１）30m足のupper_2sigmaタッチで売り、lower_2sigmaタッチで買い
#
#　２－２）slopeが閾値以上の時（トレンド発生と判断）
#　２－３）短期トレンドの確認（５０日移動平均線の傾き）
#　２－４）現在価格と２００日移動平均線の比較（上にいれば買い、下にいれば売り）
#　２－５）現在価格が単純移動平均線付近にある場合は売買する
#
# 損切り判断
# １）反対側の２シグマにヒットしたら決済する
#
# 利確判断
# １）含み益が最低利益を確保しているか確認
# ２）現在価格が移動平均線にタッチしたら決済する
####################################################

from super_algo import SuperAlgo
from common import instrument_init, account_init, decideMarket, getBollingerDataSet, extraBollingerDataSet, getEWMA, countIndex, getSlope
from datetime import datetime, timedelta
import logging
import pandas as pd
import decimal

low_slope_threshold  = -0.3
high_slope_threshold = 0.3

class Evo2BollingerAlgo(SuperAlgo):
    def __init__(self, instrument, base_path, config_name, base_time):
        super(Evo2BollingerAlgo, self).__init__(instrument, base_path, config_name, base_time)
        self.base_price = 0

    def decideTrade(self, base_time):
        trade_flag = "pass"
        window_size = self.config_data["window_size"]
        candle_width = self.config_data["candle_width"]
        sigma_valiable = self.config_data["bollinger_sigma"]
        try:
            if self.order_flag:
                pass
            else:

                #############################################
                # Get 1h * 21 WMA and check long time trend #
                #############################################

                # 移動平均の取得（WMA21（1時間足））
                wma_length = 21
                ewma21_3600 = getEWMA(self.ask_price_list, self.bid_price_list, wma_length, 3600)

                # トレンドの取得 20から10に変えてみる
                #slope_length = (10 * 3600) * -1
                # 長期トレンドを5に変えてみる
                slope_length = (5 * 3600) * -1
                slope_list = ewma21_3600[slope_length:]
                slope = getSlope(slope_list)

                # 3600の21日移動平均の傾きが、2.0以上であれば売買ロジックに入る
                high_trend_threshold = 1.0
                low_trend_threshold = -1.0
                if float(high_trend_threshold) < float(slope):
                    trend_flag = "buy"
                elif float(low_trend_threshold) > float(slope):
                    trend_flag = "sell"
                else:
                    trend_flag = "range"

                logging.info("%s 1h*21 ewma slope(10s) slope = %s, trend_flag = %s" % (base_time, slope, trend_flag))
                current_price = self.getCurrentPrice()
                if trend_flag == "range":
                    pass
#                    data_set = getBollingerDataSet(self.ask_price_list, self.bid_price_list, window_size, sigma_valiable, 1800)
#                    if current_price > data_set["upper_sigmas"][-1]:
#                        trade_flag = "sell"
#                    elif current_price < data_set["lower_sigmas"][-1]:
#                        trade_flag = "buy"
#                    else:
#                        trade_flag = "pass"
#
#                    logging.info("%s 30m bollinger band upper_sigma = %s, lower_sigma = %s" % (base_time, data_set["upper_sigmas"][-1], data_set["lower_sigmas"][-1]))

                else:
                    data_set = getBollingerDataSet(self.ask_price_list, self.bid_price_list, window_size, sigma_valiable, candle_width)

                    # 移動平均の取得(WMA50)
                    wma_length = 50
                    ewma50 = getEWMA(self.ask_price_list, self.bid_price_list, wma_length, candle_width)
                    wma_length = 200
                    ewma200 = getEWMA(self.ask_price_list, self.bid_price_list, wma_length, candle_width)

                    # 短期トレンドの取得
                    slope_length = (10 * candle_width) * -1
                    slope_list = ewma50[slope_length:]
                    slope = getSlope(slope_list)
                    baseline_touch_flag = False

                    # 移動平均線付近かどうか
                    cmp_value = current_price - data_set["base_lines"][-1]
                    if -0.01 < cmp_value < 0.01:
                        baseline_touch_flag = True

                    # slopeが上向き、現在価格が移動平均(EWMA200)より上、現在価格が移動平均(SMA)付近にいる
                    if slope - high_slope_threshold > 0 and ewma200[-1] < current_price and baseline_touch_flag and trend_flag == "buy":
                        trade_flag = "buy"
                        logging.info("EXECUTE TRADE")
                    # slopeが下向き、現在価格が移動平均(EWMA200)より下、現在価格が移動平均(SMA)付近にいる
                    elif slope - low_slope_threshold < 0 and ewma200[-1] > current_price and baseline_touch_flag and trend_flag == "sell":
                        trade_flag = "sell"
                        logging.info("EXECUTE TRADE")
                    else:
                        trade_flag = "pass"

                    logging.info("%s 5m 50 ewma slope = %s, trend_flag = %s" % (base_time, slope, trend_flag))
                    logging.info("%s current_price = %s, 5m 200 ewma = %s" % (base_time, current_price, ewma200[-1]))
                    logging.info("%s current_price = %s, base_line = %s" % (base_time, current_price, data_set["base_lines"][-1]))
                    logging.info("%s trade_flag = %s" % (base_time, trade_flag))

                return trade_flag

        except:
            raise

    # 損切り、利確はオーダー時に出している
    # ここでは、急に逆方向に動いた時に決済出来るようにしている
    def decideStl(self, base_time):
        try:
            stl_flag = False
            ex_stlmode = self.config_data["ex_stlmode"]
            window_size = self.config_data["window_size"]
            sigma_valiable = self.config_data["bollinger_sigma"]
            candle_width = self.config_data["candle_width"]

            if self.order_flag:
                if ex_stlmode == "on":

                    # 移動平均の取得(WMA50)
                    wma_length = 50
                    ewma50 = getEWMA(self.ask_price_list, self.bid_price_list, wma_length, candle_width)

                    # トレンドの取得 20から10に変えてみる
                    slope_length = (5 * candle_width) * -1
                    slope_list = ewma50[slope_length:]
                    #logging.info(slope_list)
                    slope = getSlope(slope_list)
                    logging.info("time = %s, slope = %s" % (base_time, slope))

                    # Stop Loss Algorithm
                    # get Bollinger Band sigma 2
                    sigma_valiable = 3
                    data_set = getBollingerDataSet(self.ask_price_list,
                                                   self.bid_price_list,
                                                   window_size,
                                                   sigma_valiable,
                                                   candle_width)

                    sigma_length = self.config_data["sigma_length"]
                    # Extra Bollinger Band for 5 minutes
                    data_set = extraBollingerDataSet(data_set, sigma_length, candle_width)
                    upper_sigmas = data_set["upper_sigmas"]
                    lower_sigmas = data_set["lower_sigmas"]
                    price_list   = data_set["price_list"]
                    base_lines   = data_set["base_lines"]

                    lower_sigma = lower_sigmas[-1]
                    upper_sigma = upper_sigmas[-1]
                    base_line = base_lines[-1]
                    current_ask_price = self.ask_price_list[-1]
                    current_bid_price = self.bid_price_list[-1]
                    current_price = self.getCurrentPrice()
                    order_price = self.getOrderPrice()
                    logging.info("DECIDE STL upper_sigma = %s, current_price = %s, lower_sigma = %s, base_line = %s" %(upper_sigma, current_price, lower_sigma, base_line))
                    logging.info("DECIDE STL order_price = %s, low_slope_threshold = %s, slope = %s, high_slope_threshold = %s" %(order_price, low_slope_threshold, slope, high_slope_threshold))
                    logging.info("DECIDE STL low_slope_threshold_type = %s, slope_type = %s, high_slope_threshold_type = %s" %(type(low_slope_threshold), type(slope), type(high_slope_threshold)))

                    # 買いの場合はlower_sigmaにぶつかったら決済
                    # 売りの場合はupper_sigmaにぶつかったら決済
                    stl_flag = False

                    if self.order_kind == "buy":
                        if current_price < lower_sigma:
                           logging.info("EXECUTE STL")
                           stl_flag = True

                    elif self.order_kind == "sell":
                        if current_price > upper_sigma:
                           logging.info("EXECUTE STL")
                           stl_flag = True

                    #########################
                    # Take Profit Algorithm #
                    #########################

#                    # When current price don't touch bollinger band sigma 1, Execute Settlement.
#
#                    # min_take_profit = self.config_data["min_take_profit"]
#                    logging.info("DECIDE STL current_bid_price = %s, current_ask_price = %s, order_price = %s" %(current_bid_price, current_ask_price, order_price))
#
#                    # get Bollinger Band sigma 1
#                    sigma_valiable = 1
#                    data_set = getBollingerDataSet(self.ask_price_list,
#                                                   self.bid_price_list,
#                                                   window_size,
#                                                   sigma_valiable,
#                                                   candle_width)
#
#                    #sigma_length = self.config_data["sigma_length"]
#                    # Extra Bollinger Band for 5 minutes
#                    sigma_length = 1
#                    data_set = extraBollingerDataSet(data_set, sigma_length, candle_width)
#                    upper_sigmas = data_set["upper_sigmas"]
#                    lower_sigmas = data_set["lower_sigmas"]
#                    price_list   = data_set["price_list"]
#                    base_lines   = data_set["base_lines"]
#
#
#                    min_take_profit = 0.1
#                    bollinger_flag = False
#                    if self.order_kind == "buy":
#                        if (float(current_bid_price) - float(order_price)) > float(min_take_profit):
#                            for i in range(0, len(price_list)):
#                                if price_list[i] > upper_sigmas[i]:
#                                    bollinger_flag = True
#                                    logging.info("price > upper_sigma, price = %s, upper_sigma = %s" % (price_list[i], upper_sigmas[i]))
#                            if bollinger_flag:
#                                pass
#                            else:
#                                stl_flag = True
#                    elif self.order_kind == "sell":
#                        if (float(order_price) - float(current_ask_price)) > float(min_take_profit):
#                            for i in range(0, len(price_list)):
#                                if price_list[i] < lower_sigmas[i]:
#                                    bollinger_flag = True
#                                    logging.info("price < lower_sigma, price = %s, lower_sigma = %s" % (price_list[i], lower_sigmas[i]))
#                            if bollinger_flag:
#                                pass
#                            else:
#                                stl_flag = True










                    # min_take_profit = self.config_data["min_take_profit"]
                    # When current_price is matched moving average price, execute Settlement

                    min_take_profit = 0.1
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



            else:
                pass

            return stl_flag
        except:
            raise
