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

            reverce_flag = self.config_data["reverce_decide_flag"]
            if (ask_end - ask_start) > self.trade_threshold:
                logging.info("ask_start=%s" % ask_start)
                logging.info("ask_end=%s" % ask_end)
                logging.info("start_time=%s" % self.insert_time_list[0])
                logging.info("end_time=%s" % self.insert_time_list[len(self.insert_time_list)-1])

                if reverce_flag == "on":
                    trade_flag = "sell"
                else:
                    trade_flag = "buy"

            elif (bid_start - bid_end) > self.trade_threshold:
                logging.info("bid_start=%s" % bid_start)
                logging.info("bid_end=%s" % bid_end)
                logging.info("start_time=%s" % self.insert_time_list[0])
                logging.info("end_time=%s" % self.insert_time_list[len(self.insert_time_list)-1])

                if reverce_flag == "on":
                    trade_flag = "buy"
                else:
                    trade_flag = "sell"
            else:
                trade_flag = "pass"

            return trade_flag

        except:
            raise

    # 時間切りで決済しちゃう
    def decideStl(self, base_time):
        try:
            stl_flag = False
            ex_stlmode = self.config_data["ex_stlmode"]

            if ex_stlmode == "on":
                startend_stl_time = self.config_data["ex_stl_time"]
                hour = base_time.hour
                if hour == startend_stl_time:
                    stl_flag = True
                else:
                    pass
            else:
                pass

            return stl_flag
        except:
            raise
