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
import decimal

class BollingerAlgo(SuperAlgo):
    def __init__(self, instrument, base_path):
        super(BollingerAlgo, self).__init__(instrument, base_path)
        self.base_price = 0
        #self.base_path = base_path
        #self.instrument = instrument
        #self.config_data = instrument_init(self.instrument, self.base_path)
        #self.timetrend_list = self.config_data["timetrend"]
        #self.timetrend_width = self.config_data["timetrend_width"]

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
#

    def decideTrade(self, base_time):
        try:

            trade_flag = "pass"

            lst = pd.Series(self.ask_price_list)
            window_size = self.config_data["window_size"]
            window_size = window_size * 60
            # 28分の移動平均線
            base = lst.rolling(window=window_size).mean()

            # 28本分の標準偏差
            sigma = lst.rolling(window=window_size).std(ddof=0)

            # ±2σの計算
            upper2_sigmas = base + (sigma*2.5)
            lower2_sigmas = base - (sigma*2.5)

#            upper2_sigmas = base + (sigma*3)
#            lower2_sigmas = base - (sigma*3)

            upper2_sigma = upper2_sigmas[len(upper2_sigmas)-1]
            lower2_sigma = lower2_sigmas[len(lower2_sigmas)-1]

            # ±3σの計算
            upper3_sigmas = base + (sigma*3)
            lower3_sigmas = base - (sigma*3)

            upper3_sigma = upper3_sigmas[len(upper3_sigmas)-1]
            lower3_sigma = lower3_sigmas[len(lower3_sigmas)-1]

#            for i in self.insert_time_list:
#                logging.info(i)
#
#            logging.info(window_size)
#            tmp = window_size * -1
#            logging.info(self.insert_time_list[tmp])

            cmp_price = lst[len(lst)-1]

            self.base_price = base[len(base)-1]

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
                self.order_time = self.insert_time_list[len(self.insert_time_list)-1]

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
                self.order_time = self.insert_time_list[len(self.insert_time_list)-1]
            else:
                trade_flag = "pass"

            return trade_flag

        except:
            raise

    # 損切り、利確はオーダー時に出している
    # ここでは、急に逆方向に動いた時に決済出来るようにしている
    def decideStl(self):
        try:

#            ask_lst = pd.Series(self.ask_price_list)
#            bid_lst = pd.Series(self.bid_price_list)
#
#            window_size = self.config_data["window_size"]
#            window_size = window_size * 60
#            # 28分の移動平均線
#            ask_base_list = ask_lst.rolling(window=window_size).mean()
#            bid_base_list = bid_lst.rolling(window=window_size).mean()
#
#            current_ask_price = self.ask_price_list[-1]
#            current_bid_price = self.bid_price_list[-1]
#
#            ask_base = ask_base_list[len(ask_base_list)-1]
#            bid_base = bid_base_list[len(ask_base_list)-1]
#
#            current_ask_price = float(current_ask_price)
#            current_bid_price = float(current_bid_price)
#            ask_base = float(ask_base)
#            bid_base = float(bid_base)
#
            stl_flag = False
#            current_time = self.insert_time_list[len(self.insert_time_list)-1]
#            cmp_time = self.order_time + timedelta(minutes=10)
#            logging.info("DECIDE TIME COMP= %s" % current_time)
#            logging.info("CURRENT TIME = %s" % current_time)
#            logging.info("CMP TIME = %s" % cmp_time)
#            logging.info(type(cmp_time))
#            logging.info(type(current_time))
#            logging.info("=============================================")
##            if current_time > cmp_time:
##                logging.info("****************EXECUTE TIME COMP= %s" % current_time)
##                logging.info("CURRENT TIME = %s" % current_time)
##                logging.info("CMP TIME = %s" % cmp_time)
##                self.order_flag = False
##                self.order_kind = ""
##                stl_flag = True
#
##            elif self.order_kind == "buy":
#            if self.order_kind == "buy":
#                if current_bid_price > bid_base:
#                    logging.info("***************EXECUTE BASE")
#                    logging.info("CURRENT BID PRICE = %s" % current_bid_price)
#                    logging.info("CURRENT BID BASE = %s" % bid_base)
#                    self.order_flag = False
#                    self.order_kind = ""
#                    stl_flag = True
#
#            elif self.order_kind == "sell":
#                if current_ask_price < ask_base:
#                    logging.info("***************EXECUTE BASE")
#                    logging.info("CURRENT ASK PRICE = %s" % current_ask_price)
#                    logging.info("CURRENT ASK BASE = %s" % ask_base)
#                    self.order_flag = False
#                    self.order_kind = ""
#                    stl_flag = True

            #logging.info("stl_flag=%s" % stl_flag)
            return stl_flag
        except:
            raise
