# coding: utf-8

####################################################
#
# 陽線 or 陰線が連続して発生しているかを検知するよう作成
# 価格の配列を、何分割かにして、陽線引け、陰線引けの判定をする
#
####################################################

class StepWiseAlgo(SuperAlgo):
    def __init__(self, trade_threshold, optional_threshold, instrument, base_path):
        super(trade_threshold, optional_threshold, instrument, base_path)
        self.base_path = base_path
        self.instrument = instrument
        config_data = instrument_init(self.instrument, self.base_path)
        self.step_wise_unit = config_data["step_wise_unit"]
        self.step_wise_coefficient_threshold = config_data["step_wise_coefficient_threshold"]

    def decideTrade(self):
        try:
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
                ask_start = self.ask_price_list[step_wise_index*i]
                # 60, 120, 180になるはず
                ask_end   = self.ask_price_list[step_wise_index*(i+1)]

                if ask_end - ask_start > step_wise_threshold:
                    buy_index = buy_index + 1

                elif ask_start - ask_end > step_wise_threshold:
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
                if buy_index_ratio > step_wise_coefficient_threshold:
                    trade_flag = "buy"
                    self.order_kind = trade_flag
                    self.order_flag = True
            elif total_bid_diffrence > self.trade_threshold:
                if sell_index / self.step_wise_unit > step_wise_coefficient_threshold:
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

            return stl_flag
        except:
            raise
