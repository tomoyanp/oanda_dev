# coding: utf-8

####################################################
#
# 過去3日の昼間の平均値幅を算出
# 値幅の高値に到達しそうになったら売り
# 値幅の安値に到達しそうになったら買い
#
####################################################

from super_algo import SuperAlgo
from common import instrument_init, account_init
from datetime import datetime, timedelta
import logging

class RangeAlgo(SuperAlgo):
    def __init__(self, trade_threshold, optional_threshold, instrument, base_path):
        super(StepWiseAlgo, self).__init__(trade_threshold, optional_threshold, instrument, base_path)
        self.base_path = base_path
        self.instrument = instrument
        config_data = instrument_init(self.instrument, self.base_path)
        self.step_wise_unit = config_data["step_wise_unit"]
        self.step_wise_coefficient_threshold = config_data["step_wise_coefficient_threshold"]

    def initPriceRange(self):

    def decideTrade(self):
        try:
            start_price_list = []
            end_price_list = []
            start_time_list = []
            end_time_list = []
            # trade_flag is pass or ask or bid
            now = datetime.now()
            now = now.strftime("%H%M%S")
            now = int(now)
            list_size = len(self.ask_price_list)-1
            # ローソクを何本判断に使うか => step_wise_unit
            # 180秒を1分足3本にバラす場合、 step_wise_index = 180/3 == 60
            step_wise_index = list_size / self.step_wise_unit
            step_wise_threshold = self.trade_threshold / self.step_wise_unit

            # buy_indexが2/3で以上の場合にトレードするよう計算するとする
            # buy_index / step_wise_unit == 0.66666以上になればOKという理解
            # step_wise_coefficient_threshold
            # buyindexの割合と、比較する閾値
            buy_index = 0
            sell_index = 0
            for i in range(0, self.step_wise_unit):
                # 0, 60, 120になるはず
                print step_wise_index * i
                print len(self.ask_price_list) - 1
                ask_start = self.ask_price_list[step_wise_index*i]
                insert_time_start = self.insert_time_list[step_wise_index*i]
                # 60, 120, 180になるはず
                ask_end   = self.ask_price_list[step_wise_index*(i+1)]
                insert_time_end = self.insert_time_list[step_wise_index*(i*1)]

                if ask_end - ask_start > step_wise_threshold:
                    start_price_list.append(ask_start)
                    end_price_list.append(ask_end)
                    start_time_list.append(insert_time_start)
                    end_time_list.append(insert_time_start)
                    buy_index = buy_index + 1

                elif ask_start - ask_end > step_wise_threshold:
                    start_price_list.append(ask_start)
                    end_price_list.append(ask_end)
                    start_time_list.append(insert_time_start)
                    end_time_list.append(insert_time_start)

                    sell_index = sell_index + 1

            total_ask_start = self.ask_price_list[0]
            total_ask_end = self.ask_price_list[len(self.ask_price_list)-1]

            total_ask_difference = total_ask_end - total_ask_start
            total_bid_diffrence = total_ask_start - total_ask_end
            buy_index_ratio = buy_index / self.step_wise_unit
            sell_index_ratio = sell_index / self.step_wise_unit

            trade_flag = "pass"
            self.order_flag = False

            if total_ask_difference > self.trade_threshold:
                if buy_index_ratio > self.step_wise_coefficient_threshold:
                    trade_flag = "buy"
                    self.order_kind = trade_flag
                    self.order_flag = True

                    logging.info("===========================================")
                    logging.info("ORDER_FLAG=%s" % self.order_flag)
                    logging.info("START_PRICE_LIST=%s" % start_price_list)
                    logging.info("START_TIME_LIST=%s" % start_time_list)
                    logging.info("END_PRICE_LIST=%s" % end_price_list)
                    logging.info("END_TIME_LIST=%s" % end_time_list)
                    logging.info("===========================================")

            elif total_bid_diffrence > self.trade_threshold:
                if sell_index / self.step_wise_unit > self.step_wise_coefficient_threshold:
                    trade_flag = "sell"
                    self.order_kind = trade_flag
                    self.order_flag = True

                    logging.info("===========================================")
                    logging.info("ORDER_FLAG=%s" % self.order_flag)
                    logging.info("START_PRICE_LIST=%s" % start_price_list)
                    logging.info("START_TIME_LIST=%s" % start_time_list)
                    logging.info("END_PRICE_LIST=%s" % end_price_list)
                    logging.info("END_TIME_LIST=%s" % end_time_list)
                    logging.info("===========================================")

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

            logging.info("stl_flag=%s" % stl_flag)
            return stl_flag
        except:
            raise
