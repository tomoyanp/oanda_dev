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
    def __init__(self, instrument, base_path):
        super(TimeTrendAlgo, self).__init__(instrument, base_path)
        #self.base_path = base_path
        #self.instrument = instrument
        #self.config_data = instrument_init(self.instrument, self.base_path)
        #self.timetrend_list = self.config_data["timetrend"]
        #self.timetrend_width = self.config_data["timetrend_width"]

    def decideTrade(self, base_time):
        try:
            #cmp_time = int(cmp_time)
            #cmp_time_aft = base_time + timedelta(hours=self.timetrend_width)
            cmp_time = base_time.strftime("%Y-%m-%d")
            trade_flag = "pass"

            timetrend_list = self.config_data["timetrend"]
            timetrend_width = self.config_data["timetrend_width"]
            for timetrend in timetrend_list:
#                price_list = []
#                time_list = []
                timetrend_bef = "%s %s" % (cmp_time, timetrend)
                timetrend_aft = datetime.strptime(timetrend_bef, "%Y-%m-%d %H:%M:%S")
                timetrend_aft = timetrend_aft + timedelta(hours=timetrend_width)
                timetrend_bef = datetime.strptime(timetrend_bef, "%Y-%m-%d %H:%M:%S")
                if timetrend_bef < base_time and timetrend_aft > base_time:
#                    timetrend_bef = timetrend_bef - timedelta(seconds=60)
#                    timetrend_bef = timetrend_bef.strftime("%Y-%m-%d %H:%M:%S")
#                    target_time = base_time.strftime("%Y-%m-%d %H:%M:%S")
#                    sql = "select ask_price, insert_time from %s_TABLE where insert_time > \'%s\' and insert_time < \'%s\'" % (self.instrument, timetrend_bef, target_time)
#                    logging.info(sql)
#                    response = self.mysqlConnector.select_sql(sql)
#                    for res in response:
#                        price_list.append(res[0])
#                        time_list.append(res[1])

#                    logging.info(price_list)
#                    logging.info(time_list)

                    if (self.ask_price_list[len(self.ask_price_list)-1] - self.ask_price_list[0]) > self.trade_threshold:
                        trade_flag = "buy"
                        self.order_kind = trade_flag
                        self.order_flag = True

                    elif (self.bid_price_list[0] - self.bid_price_list[len(self.bid_price_list)-1]) > self.trade_threshold:
                        trade_flag = "sell"
                        self.order_kind = trade_flag
                        self.order_flag = True

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
