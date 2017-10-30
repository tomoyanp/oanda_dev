# coding: utf-8

####################################################
#
# 日中のレンジ相場をつかって逆張りする手法
# ボリンジャーバンド+2σを超えたあたりで逆張りしてく
#
####################################################

from super_algo import SuperAlgo
from common import instrument_init, account_init
from datetime import datetime, timedelta
import logging
import pandas as pd

class BollingerAlgo(SuperAlgo):
    def __init__(self, instrument, base_path):
        super(BollingerAlgo, self).__init__(instrument, base_path)
        #self.base_path = base_path
        #self.instrument = instrument
        #self.config_data = instrument_init(self.instrument, self.base_path)
        #self.timetrend_list = self.config_data["timetrend"]
        #self.timetrend_width = self.config_data["timetrend_width"]

    # オーバーライドする
    #def calcThreshold(self, trade_flag):




    def decideTrade(self, base_time):
        try: 

            # enable_timeの中でトレードするようにする
            enable_time_mode = self.config_data["enable_time_mode"]
            if enable_time_mode == "on":
                trade_time_flag = self.decideTradeTime(base_time)
            else:
                trade_time_flag = True

            if trade_time_flag:
                lst = pd.Series(self.ask_price_list)
                window_size = self.config_data["window_size"]
                window_size = window_size * 60
                # 28分の移動平均線
                base = lst.rolling(window=window_size).mean()

                # 28本分の標準偏差
                sigma = lst.rolling(window=window_size).std(ddof=0)

                # ±2σの計算
                upper2_sigmas = base + (sigma*3)
                lower2_sigmas = base - (sigma*3)

                upper2_sigma = upper2_sigmas[len(upper2_sigmas)-1]
                lower2_sigma = lower2_sigmas[len(lower2_sigmas)-1]

                # ±3σの計算
                upper3_sigmas = base + (sigma*3)
                lower3_sigmas = base - (sigma*3)

                upper3_sigma = upper3_sigmas[len(upper3_sigmas)-1]
                lower3_sigma = lower3_sigmas[len(lower3_sigmas)-1]

                cmp_price = lst[len(lst)-1]


                logging.info("=======================")
                logging.info("DECIDE ORDER")
                logging.info("ASK_PRICE=%s" % cmp_price)
                logging.info("UPPER_SIGMA=%s" % upper2_sigma)
                logging.info("lower_SIGMA=%s" % lower2_sigma)
                logging.info("BASE_TIME=%s" % base_time)
                logging.info("=======================")


                if cmp_price > upper2_sigma:
                    trade_flag = "sell"
                    self.order_flag = True
                    self.order_kind = trade_flag
                    logging.info("=======================")
                    logging.info("EXECUTE ORDER SELL")
                    logging.info("ASK_PRICE=%s" % cmp_price)
                    logging.info("UPPER_SIGMA=%s" % upper2_sigma)
                    logging.info("BASE_TIME=%s" % base_time)
                    logging.info("=======================")

                elif cmp_price < lower2_sigma:
                    trade_flag = "buy"
                    self.order_flag = True
                    self.order_kind = trade_flag
                    logging.info("=======================")
                    logging.info("EXECUTE ORDER BUY")
                    logging.info("ASK_PRICE=%s" % cmp_price)
                    logging.info("LOWER_SIGMA=%s" % lower2_sigma)
                    logging.info("BASE_TIME=%s" % base_time)
                    logging.info("=======================")
                else:
                    trade_flag = "pass"

                trend_follow_mode = self.config_data["trend_follow_mode"]

                if trend_follow_mode = "on":
                    trend_flag = self.checkTrend(base_time)
                else:
                    trend_flag = trade_flag

                if trend_flag == trade_flag:
                    pass
                else:
                    trade_flag = "pass"


                return trade_flag
            else:
                pass

            except:
                raise

    # 損切り、利確はオーダー時に出している
    # ここでは、急に逆方向に動いた時に決済出来るようにしている
    def decideStl(self):
        try:
            ask_mx = max(self.ask_price_list)
            ask_min = min(self.ask_price_list)
            ask_mx_index = self.ask_price_list.index(ask_mx)
            ask_min_index = self.ask_price_list.index(ask_min)

            bid_mx = max(self.bid_price_list)
            bid_min = min(self.bid_price_list)
            bid_mx_index = self.bid_price_list.index(bid_mx)
            bid_min_index = self.bid_price_list.index(bid_min)

            now = datetime.now()
            now = now.strftime("%Y-%m-%d %H:%M:%S")

            stl_flag = False
            if self.order_kind == "buy":
                if (bid_mx - bid_min) > self.optional_threshold and bid_mx_index < bid_min_index:
                    self.order_flag = False
                    stl_flag = True

            elif self.order_kind == "sell":
                if (ask_mx - ask_min) > self.optional_threshold and ask_mx_index > ask_min_index:
                    self.order_flag = False
                    stl_flag = True

            #logging.info("stl_flag=%s" % stl_flag)
            return stl_flag
        except:
            raise
