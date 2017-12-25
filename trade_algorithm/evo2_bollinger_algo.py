# coding: utf-8

####################################################
#
# bollinger algo改良版2
# トレンドを確認して、移動平均にぶつかったタイミングでトレード
# 上下の2シグマにぶつかったら決済する
#
####################################################

from super_algo import SuperAlgo
from common import instrument_init, account_init, decideMarket, getBollingerDataSet, extraBollingerDataSet
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
                slope = self.newCheckTrend(base_time)
                logging.info("time = %s, slope = %s" % (base_time, slope))

                # pandasの形式に変換
                ask_lst = pd.Series(self.ask_price_list)
                bid_lst = pd.Series(self.bid_price_list)
                lst = (ask_lst+bid_lst) / 2

                # window_size 28 * candle_width 600 （10分足で28本分）
                window_size = self.config_data["window_size"]
                candle_width = self.config_data["candle_width"]
                window_size = window_size * candle_width

                # 28本分の移動平均線
                base = lst.rolling(window=window_size).mean()

                # 過去5本分の移動平均と価格リストを取得
                sigma_length = self.config_data["sigma_length"]
                sigma_length = sigma_length * candle_width
                sigma_length = sigma_length * -1
                base = base[sigma_length:]
                lst = lst[sigma_length:]

                # 普通の配列型にキャストしないと無理だった
                lst = lst.values.tolist()
                base = base.values.tolist()
                print lst

                sigma_flag = False
                # 過去5本で移動平均線付近にいるか確認する
                for i in range(0, len(lst)):
                    if lst[i] - base[i] < 0.01 and lst[i] - base[i] > -0.01:
                        sigma_flag = True

                # トレンドが上向きであれば、買い
                # トレンドが下向きであれば、売り
                if sigma_flag and slope < 0:
                    trade_flag = "sell"
                elif sigma_flag and slope > 0:
                    trade_flag = "buy"
                else:
                    trade_flag = "pass"

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

                    # 過去5本分（50分）のsigmaだけ抽出
                    sigma_length = self.config_data["sigma_length"]

                    data_set = extraBollingerDataSet(data_set, sigma_length, candle_width)
                    upper_sigmas = data_set["upper_sigmas"]
                    lower_sigmas = data_set["lower_sigmas"]
                    price_list   = data_set["price_list"]
                    base_lines   = data_set["base_lines"]

                    # 現在価格の取得
                    current_ask_price = self.ask_price_list[-1]
                    current_bid_price = self.bid_price_list[-1]
                    current_ask_price = float(current_ask_price)
                    current_bid_price = float(current_bid_price)

                    # 上下どちらかのシグマにぶつかったら決済してしまう
                    # 利確、損切り兼任
                    stl_flag = False
                    if self.order_kind == "buy":
                        for i in range(0, len(upper_sigmas)):
                            if price_list[i] < lower_sigmas[i] or price_list[i] > upper_sigmas[i]:
                                stl_flag = True

                    elif self.order_kind == "sell":
                        for i in range(0, len(upper_sigmas)):
                            if price_list[i] < lower_sigmas[i] or price_list[i] > upper_sigmas[i]:
                                stl_flag = True

            else:
                pass

            return stl_flag
        except:
            raise
