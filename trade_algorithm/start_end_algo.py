# coding: utf-8

#################################################
#
# time_widthの始め値と終わり値が閾値超えしているかどうか
#
#################################################

from super_algo import SuperAlgo
from datetime import datetime, timedelta
import logging

class StartEndAlgo(SuperAlgo):
    def __init__(self, instrument, base_path, config_name):
        super(StartEndAlgo, self).__init__(instrument, base_path, config_name)

    # 始め値と終わり値でトレードする
    def decideTrade(self, base_time):
        try:
            # trade_flag is pass or ask or bid
            ask_start = self.ask_price_list[0]
            ask_end = self.ask_price_list[len(self.ask_price_list)-1]
            bid_start = self.bid_price_list[0]
            bid_end = self.bid_price_list[len(self.bid_price_list)-1]

            if (ask_end - ask_start) > self.trade_threshold:
                logging.info("ask_start=%s" % ask_start)
                logging.info("ask_end=%s" % ask_end)
                logging.info("start_time=%s" % self.insert_time_list[0])
                logging.info("end_time=%s" % self.insert_time_list[len(self.insert_time_list)-1])

                trade_flag = "buy"

            elif (bid_start - bid_end) > self.trade_threshold:
                logging.info("bid_start=%s" % bid_start)
                logging.info("bid_end=%s" % bid_end)
                logging.info("start_time=%s" % self.insert_time_list[0])
                logging.info("end_time=%s" % self.insert_time_list[len(self.insert_time_list)-1])
                trade_flag = "sell"
            else:
                trade_flag = "pass"

            return trade_flag

        except:
            raise

    # 損切り、利確はオーダー時に出している
    # ここでは、急に逆方向に動いた時に決済出来るようにしている
    def decideStl(self):
        try:
#            ask_mx = max(self.ask_price_list)
#            ask_min = min(self.ask_price_list)
#            ask_mx_index = self.ask_price_list.index(ask_mx)
#            ask_min_index = self.ask_price_list.index(ask_min)
#
#            bid_mx = max(self.bid_price_list)
#            bid_min = min(self.bid_price_list)
#            bid_mx_index = self.bid_price_list.index(bid_mx)
#            bid_min_index = self.bid_price_list.index(bid_min)
#
#            now = datetime.now()
#            now = now.strftime("%Y-%m-%d %H:%M:%S")
#
            stl_flag = False
#            if self.order_kind == "buy":
#                if (bid_mx - bid_min) > self.optional_threshold and bid_mx_index < bid_min_index:
#                    self.order_flag = False
#                    stl_flag = True
#
#            elif self.order_kind == "sell":
#                if (ask_mx - ask_min) > self.optional_threshold and ask_mx_index > ask_min_index:
#                    self.order_flag = False
#                    stl_flag = True
#
            return stl_flag
        except:
            raise
