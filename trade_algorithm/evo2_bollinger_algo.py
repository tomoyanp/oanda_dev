# coding: utf-8

####################################################
#
# bollinger algo改良版
# 1.8シグマ、2.0シグマを推移しているものをキャッチする
# 2.0シグマ、3.0シグマを推移しているトレンドの終わりをキャッチする
#
####################################################

from super_algo import SuperAlgo
from common import instrument_init, account_init, decideMarket
from datetime import datetime, timedelta
import logging
import pandas as pd
import decimal

class Evo2BollingerAlgo(SuperAlgo):
    def __init__(self, instrument, base_path, config_name):
        super(Evo2BollingerAlgo, self).__init__(instrument, base_path, config_name)
        self.base_price = 0

        # オーバーライドする
#    def calcThreshold(self, trade_flag):
#        window_size = self.config_data["window_size"]
#        window_size = int(window_size) * -1
#        ask_price_list = self.ask_price_list[window_size:]
#
#        stop_loss_val = self.config_data["stop_loss"]
#        current_ask_price = self.ask_price_list[-1]
#        current_bid_price = self.bid_price_list[-1]
#
#        threshold_list = {}
#        if trade_flag == "sell":
#            threshold_list["stoploss"] = current_ask_price + stop_loss_val
#            threshold_list["takeprofit"] = self.base_price
#
#        elif trade_flag == "buy":
#            threshold_list["stoploss"] = current_bid_price - stop_loss_val
#            threshold_list["takeprofit"] = self.base_price
#        else:
#            pass
#
#        threshold_list["stoploss"] = '{:.3f}'.format(threshold_list["stoploss"])
#        threshold_list["takeprofit"] = '{:.3f}'.format(threshold_list["takeprofit"])
#
#        logging.info("===========================================")
#        logging.info("STOP LOSS RATE = %s" % threshold_list["stoploss"])
#        logging.info("TAKE PROFIT RATE = %s" % threshold_list["takeprofit"])
#
#        self.stoploss_rate = threshold_list["stoploss"]
#        self.takeprofit_rate = threshold_list["takeprofit"]
#
#        return threshold_list

    def decideTrade(self, base_time):
        try:
            if self.order_flag:
                pass
            else:
                # トレンドのチェック
                slope = self.tmpCheckTrend(base_time)

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
                    if lst[i] - base[i] < 0.05 and lst[i] - base[i] > -0.05:
                        sigma_flag = True

                # トレンドが上向きであれば、買い
                # トレンドが下向きであれば、売り
                if sigma_flag and slope < 0:
                    trade_flag = "sell"
                elif sigma_flag and slope > 0:
                    trade_flag = "buy"
                else:
                    trade_flag = "pass"

#                self.base_price = base[len(base)-1]
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


#    def getInitialSql(self, base_time):
#        logging.info("=== Start SuperAlgo.getInitialSql Logic ===")
#        time_width = self.config_data["time_width"]
#        start_time = base_time - timedelta(seconds=time_width)
#        logging.info("start_time=%s" % start_time)
#        # マーケットが休みの場合、48時間さかのぼってSQLを実行する
#        flag = decideMarket(start_time)
#        logging.info("decideMarket.flag=%s" % flag)
#        if flag == False:
#            start_time = start_time - timedelta(hours=48)
#
#        start_time = start_time.strftime("%Y-%m-%d %H:%M:%S")
#        end_time = base_time.strftime("%Y-%m-%d %H:%M:%S")
#
#        # 10分ごとにする
#        sql = "select ask_price, bid_price, insert_time from %s_TABLE where insert_time > \'%s\' and insert_time < \'%s\' and insert_time like \'%%0:00\' order by insert_time " % (self.instrument, start_time, end_time)
#        logging.info("sql=%s" % sql)
#        logging.info("=== End SuperAlgo.getInitialSql Logic ===")
#        print sql
#        return sql
