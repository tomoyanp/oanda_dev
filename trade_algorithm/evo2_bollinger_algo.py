# coding: utf-8

####################################################
#
# bollinger algo改良版2
# トレンドを確認して、移動平均にぶつかったタイミングでトレード
# 上下の2シグマにぶつかったら決済する
#
####################################################

from super_algo import SuperAlgo
from common import instrument_init, account_init, decideMarket, getBollingerDataSet, extraBollingerDataSet, getWMA, countIndex
from datetime import datetime, timedelta
import logging
import pandas as pd
import decimal

class Evo2BollingerAlgo(SuperAlgo):
    def __init__(self, instrument, base_path, config_name):
        super(Evo2BollingerAlgo, self).__init__(instrument, base_path, config_name)
        self.base_price = 0

    def decideTrade(self, base_time):
        try:
            if self.order_flag:
                pass
            else:
                # トレンドのチェック
#                slope = self.newCheckTrend(base_time)
#                logging.info("time = %s, slope = %s" % (base_time, slope))

                # window_size 28 * candle_width 600 （10分足で28本分）
                window_size = self.config_data["window_size"]
                candle_width = self.config_data["candle_width"]
                sigma_valiable = self.config_data["bollinger_sigma"]

                data_set = getBollingerDataSet(self.ask_price_list,
                                               self.bid_price_list,
                                               window_size,
                                               sigma_valiable,
                                               candle_width)

                # 過去5本分（50分）のsigmaだけ抽出
                sigma_length = self.config_data["sigma_length"]
                data_set     = extraBollingerDataSet(data_set, sigma_length, candle_width)
                upper_sigmas = data_set["upper_sigmas"]
                lower_sigmas = data_set["lower_sigmas"]
                price_list   = data_set["price_list"]
                base_lines   = data_set["base_lines"]

                sigma_flag = False
                # 過去5本で移動平均線付近にいるか確認する
                for i in range(0, len(price_list)):
                    if price_list[i] - base_lines[i] <= 0.05 and price_list[i] - base_lines[i] >= -0.05:
                        sigma_flag = True

                # 現在価格が移動平均より上であれば、買い
                # 現在価格が移動平均より下であれば、売り
                # 全然正確に計算できない。。。
                wma_length = 200
                
                flag, self.wma_index = countIndex(self.wma_index, candle_width)
                if flag:
                    self.wma_value = getWMA(self.ask_price_list, self.bid_price_list, wma_length, candle_width)
                
                current_price = (self.ask_price_list[-1] + self.bid_price_list[-1]) / 2
                logging.info("DECIDE TRADE base_line = %s, price = %s" %(base_lines[-1], current_price))
                logging.info("DECIDE TRADE wma_value = %s, price = %s, trade_flag = %s" %(self.wma_value, current_price, trade_flag))
                if sigma_flag and self.wma_value < current_price:
                    trade_flag = "buy"
                    logging.info("EXECUTE BUY ORDER")
                if sigma_flag and self.wma_value > current_price:
                    trade_flag = "sell"
                    logging.info("EXECUTE SELL ORDER")
                else:
                    trade_flag = "pass"

                # トレンドが上向きであれば、買い
                # トレンドが下向きであれば、売り
                # 回帰分析を使ったパターンの方
#                if sigma_flag and slope < 0:
#                    trade_flag = "sell"
#                    logging.info("DECIDE ORDER")
#                    logging.info("base_line = %s, price = %s, trade_flag = %s, slope = %s" %(base_lines[-1], price_list[-1], trade_flag, slope))
#                elif sigma_flag and slope > 0:
#                    trade_flag = "buy"
#                    logging.info("DECIDE ORDER")
#                    logging.info("base_line = %s, price = %s, trade_flag = %s, slope = %s" %(base_lines[-1], price_list[-1], trade_flag, slope))
#                else:
#                    trade_flag = "pass"
#
               # ボリンジャーバンドの幅が一定以上であれば
#                if upper_sigmas[-1] - lower_sigmas[-1] < 0.1:
#                    trade_flag = "pass"
                
                #logging.info("wma_value = %s" % self.wma_value)
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
                    window_size = self.config_data["window_size"]
                    sigma_valiable = self.config_data["bollinger_sigma"]
                    candle_width = self.config_data["candle_width"]
                    data_set = getBollingerDataSet(self.ask_price_list,
                                                   self.bid_price_list,
                                                   window_size,
                                                   sigma_valiable,
                                                   candle_width)

#                    # 過去5本分（50分）のsigmaだけ抽出
#                    sigma_length = self.config_data["sigma_length"]
#
#                    data_set = extraBollingerDataSet(data_set, sigma_length, candle_width)
                    upper_sigmas = data_set["upper_sigmas"]
                    lower_sigmas = data_set["lower_sigmas"]
                    price_list   = data_set["price_list"]
                    base_lines   = data_set["base_lines"]

                    # 現在価格の取得
                    current_ask_price = self.ask_price_list[-1]
                    current_bid_price = self.bid_price_list[-1]
                    current_ask_price = float(current_ask_price)
                    current_bid_price = float(current_bid_price)

                    lower_sigma = lower_sigmas[-1]
                    upper_sigma = upper_sigmas[-1]
                    logging.info("DECIDE STL upper_sigma = %s, ask_price = %s, bid_price = %s, lower_sigma = %s" %(upper_sigma, current_ask_price, current_bid_price, lower_sigma))

                    # 上下どちらかのシグマにぶつかったら決済してしまう
                    # 利確、損切り兼任
                    stl_flag = False
                    if self.order_kind == "buy":
                        if current_bid_price < lower_sigma or current_bid_price > upper_sigma:
                           logging.info("EXECUTE STL")
                           stl_flag = True

                    elif self.order_kind == "sell":
                        if current_ask_price < lower_sigma or current_ask_price > upper_sigma:
                           logging.info("EXECUTE STL")
                           stl_flag = True


#                    stl_flag = False
#                    if self.order_kind == "buy":
#                        for i in range(0, len(upper_sigmas)):
#                            if price_list[i] < lower_sigmas[i] or price_list[i] > upper_sigmas[i]:
#                                logging.info("DECIDE STL")
#                                logging.info("upper_sigma = %s, price = %s, lower_sigma = %s" %(upper_sigmas[i], price_list[i], lower_sigmas[i]))
#                                stl_flag = True
#
#                    elif self.order_kind == "sell":
#                        for i in range(0, len(upper_sigmas)):
#                            if price_list[i] < lower_sigmas[i] or price_list[i] > upper_sigmas[i]:
#                                logging.info("DECIDE STL")
#                                logging.info("upper_sigma = %s, price = %s, lower_sigma = %s" %(upper_sigmas[i], price_list[i], lower_sigmas[i]))
#                                stl_flag = True

            else:
                pass

            return stl_flag
        except:
            raise
