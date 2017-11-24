# coding: utf-8

####################################################
#
# 大きい動きが出る時間帯だけウオッチし、その時出てるトレンドに乗っていく手法
#
####################################################

from super_algo import SuperAlgo
from common import instrument_init, account_init
from datetime import datetime, timedelta
import logging

class TimeTrendAlgo(SuperAlgo):
    def __init__(self, instrument, base_path, config_name):
        super(TimeTrendAlgo, self).__init__(instrument, base_path, config_name)

    def decideTrade(self, base_time):
        try:
            #cmp_time = int(cmp_time)
            #cmp_time_aft = base_time + timedelta(hours=self.timetrend_width)
            cmp_time = base_time.strftime("%Y-%m-%d")
            trade_flag = "pass"

#            timetrend_list = self.config_data["timetrend"]
            timetrend_list = self.config_data["enable_time"]
            #timetrend_width = self.config_data["timetrend_width"]
            # これ、多分一時間分取得するってことだな
            timetrend_width = 1
            for timetrend in timetrend_list:
#                price_list = []
#                time_list = []
                timetrend_bef = "%s %s" % (cmp_time, timetrend)
                timetrend_aft = datetime.strptime(timetrend_bef, "%Y-%m-%d %H:%M:%S")
                timetrend_aft = timetrend_aft + timedelta(hours=timetrend_width)
                timetrend_bef = datetime.strptime(timetrend_bef, "%Y-%m-%d %H:%M:%S")
                if timetrend_bef < base_time and timetrend_aft > base_time:
                    timetrend_bef = timetrend_bef - timedelta(seconds=300)
                    cmp_ask_bef = self.ask_price_list[0]
                    cmp_bid_bef = self.bid_price_list[0]
                    cmp_insert_time_bef = self.insert_time_list[0]
                    cmp_ask_aft = self.ask_price_list[len(self.ask_price_list)-1]
                    cmp_bid_aft = self.bid_price_list[len(self.bid_price_list)-1]
                    cmp_insert_time_aft = self.insert_time_list[len(self.insert_time_list)-1]

                    # 累計にしたくないときはここをコメントアウトする
                    for i in range(0, len(self.insert_time_list)):
                        if self.insert_time_list[i] > timetrend_bef:
                            cmp_ask_bef = self.ask_price_list[i]
                            cmp_bid_bef = self.bid_price_list[i]
                            cmp_insert_time_bef = self.insert_time_list[i]
                            break

                    logging.info("=======================")
                    logging.info("DECIDE ORDER")
                    logging.info("ASK_PRICE_BEFORE=%s" % cmp_ask_bef)
                    logging.info("INSERT_TIME=%s" % cmp_insert_time_bef)
                    logging.info("ASK_PRICE_AFTER=%s" % cmp_ask_aft)
                    logging.info("BASE_TIME=%s" % base_time)
                    logging.info("=======================")


                    if cmp_ask_aft - cmp_ask_bef > self.trade_threshold:
                        trade_flag = "buy"
                        self.order_kind = trade_flag
                        self.order_flag = True
                        logging.info("=======================")
                        logging.info("EXECUTE ORDER BUY")
                        logging.info("ASK_PRICE_BEFORE=%s" % cmp_ask_bef)
                        logging.info("INSERT_TIME=%s" % cmp_insert_time_bef)
                        logging.info("ASK_PRICE_AFTER=%s" % cmp_ask_aft)
                        logging.info("BASE_TIME=%s" % base_time)
                        logging.info("=======================")

                    elif cmp_bid_bef - cmp_bid_aft > self.trade_threshold:
                        trade_flag = "sell"
                        self.order_kind = trade_flag
                        self.order_flag = True
                        logging.info("=======================")
                        logging.info("EXECUTE ORDER SELL")
                        logging.info("BID_PRICE_BEFORE=%s" % cmp_bid_bef)
                        logging.info("INSERT_TIME=%s" % cmp_insert_time_bef)
                        logging.info("BID_PRICE_AFTER=%s" % cmp_bid_aft)
                        logging.info("BASE_TIME=%s" % base_time)
                        logging.info("=======================")

            return trade_flag

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
