# coding: utf-8

###########################################################
#
# time_widthの高値、安値が閾値超えしているかどうか
# 時間指定が出来る
###########################################################

from super_algo import SuperAlgo
from datetime import datetime
import logging

class HiLowAlgo(SuperAlgo):
    def __init__(self, trade_threshold, optional_threshold, instrument, base_path):
        super(HiLowAlgo, self).__init__(trade_threshold, optional_threshold, instrument, base_path)
        self.base_path = base_path
        self.instrument = instrument
        config_data = instrument.init(self.instrument, self.base_path)
        self.enable_start_time = config_data["starttime"]
        self.enable_end_time = config_data["endtime"]


    # 高値と安値でトレードする
    def decideTrade(self, base_time):
        try:
            tmp_time = base_time.strftime("%Y-%m-%d")
            strenable_start_time = "%s %s" % (tmp_time, enable_start_time)
            strenable_end_time = "%s %s" % (tmp_time, enable_end_time)
            penable_start_time = datetime.strptime(strenable_start_time)
            penable_end_time = datetime.strptime(strenable_end_time)

            if penable_start_time > base_time and base_time < penable_end_time:
                sql = ""
            # trade_flag is pass or ask or bid
            now = datetime.now()
            now = now.strftime("%H%M%S")
            now = int(now)
            ask_mx = max(self.ask_price_list)
            ask_min = min(self.ask_price_list)
            ask_mx_index = self.ask_price_list.index(ask_mx)
            ask_min_index = self.ask_price_list.index(ask_min)

            bid_mx = max(self.bid_price_list)
            bid_min = min(self.bid_price_list)
            bid_mx_index = self.bid_price_list.index(bid_mx)
            bid_min_index = self.bid_price_list.index(bid_min)

            self.order_flag = False

            if (ask_mx - ask_min) > self.trade_threshold and ask_mx_index > ask_min_index:
                trade_flag = "buy"
                self.order_kind = trade_flag
                self.order_flag = True

            elif (bid_mx - bid_min) > self.trade_threshold and bid_mx_index < bid_min_index:
                trade_flag = "sell"
                self.order_kind = trade_flag
                self.order_flag = True
            else:
                trade_flag = "pass"
                self.order_flag = False

            logging.info("THIS IS TOO ORDER FLAG=%s" % self.order_flag)
            return trade_flag

        except:
            raise

    # 損切り、利確はオーダー時に出している
    # ここでは、急に逆方向に動いた時に決済出来るようにしている
    def decideStl(self):
        print "********** Decide Stl **********"
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

            return stl_flag
        except:
            raise
