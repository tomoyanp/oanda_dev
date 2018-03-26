# coding: utf-8
####################################################
# トレード判断
# bollinger 1h3sigmaの幅が1.5以下（expantionの判定）
# bollinger 5m3+0.1の突破
#
# 損切り判断
# １）とりあえず0.3に設定
#
# 利確判断
# １）含み益が最低利益(30pips)を確保しているか確認
# ２）現在価格が移動平均線にタッチしたら決済する
# ３）リミットオーダーは1.0
####################################################

from super_algo import SuperAlgo
from common import instrument_init, account_init, decideMarket, getBollingerDataSet, extraBollingerDataSet, getEWMA, countIndex, getSlope, getOriginalEWMA
from datetime import datetime, timedelta
import logging
import pandas as pd
import decimal


class ExpantionAlgo(SuperAlgo):
    def __init__(self, instrument, base_path, config_name, base_time):
        super(ExpantionAlgo, self).__init__(instrument, base_path, config_name, base_time)
        self.base_price = 0
        self.setPrice(base_time)
        self.setIndicator(base_time)

    def decideTrade(self, base_time):
        trade_flag = "pass"
        try:
            if self.order_flag:
                pass
            else:
                minutes = base_time.minute
                seconds = base_time.second
                # 1分足の終値付近で計算ロジックに入る
                if minutes % 5 == 4 and seconds > 50:
                    logging.info("%s :TrendExpantionLogic START" % base_time)
                    # 性能的に5分に一回呼び出しに変更
                    self.setIndicator(base_time)
                    current_price = self.getCurrentPrice()
                    trade_flag = self.decideExpantionTrade(trade_flag, current_price)

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
                    minutes = base_time.minute
                    seconds = base_time.second
                    current_price = self.getCurrentPrice()
                    # 1分足の終値付近で計算ロジックに入る
                    if seconds > 50:
                        logging.info("%s :ExpantionStlLogic START" % base_time)
                        self.setIndicator(base_time)
                        stl_flag = self.decideExpantionStl(stl_flag, current_price)
            else:
                pass

            return stl_flag
        except:
            raise

    def decideExpantionStl(self, stl_flag, current_price):
        # Stop Loss Algorithm
        order_price = self.getOrderPrice()

        # bollinger 逆側の向きが変わったら
        if self.order_kind == "buy":
            if self.bollinger1h3_lower_simga_slope > 0:
                stl_flag = True
        elif self.order_kind == "sell":
            if self.bollinger1h3_upper_sigma_slope < 0:
                stl_flag = True

        # 損切り逆方向にタッチしたら
        if self.order_kind == "buy":
            if current_price < self.lower_sigma_5m3:
                stl_flag = True
                logging.info("EXECUTE STLEMENT at Reverse Stl mode")
        elif self.order_kind == "sell":
            if current_price > self.upper_sigma_5m3:
                stl_flag = True
                logging.info("EXECUTE STLEMENT at Reverse Stl mode")

        stl_flag = self.decideTrailLogic(stl_flag, self.ask_price, self.bid_price, current_price, order_price)
        logging.info("stl_flag = %s" % stl_flag)

        return stl_flag

    def decideExpantionTrade(self, trade_flag, current_price):
        # Buy Logic at Trend Follow Mode
        slope_high_threshold = 0.3
        slope_low_threshold = -0.3

        # slopeは上を向いている場合は買いエントリしない。下を向いている場合は売りエントリしない
        if (self.upper_sigma_1h3 - self.lower_sigma_1h3) < 2:
            logging.info("1h3 bollinger logic: OK, upper_sigma = %s, lower_sigma = %s" % (self.upper_sigma_1h3, self.lower_sigma_1h3))
            if current_price > (self.upper_sigma_5m3) and self.bollinger1h3_slope < slope_high_threshold:
                trade_flag = "buy"
                logging.info("5m3 bollinger logic: OK, upper_sigma + 0.1 = %s , current_price = %s" % ((self.upper_sigma_5m3), current_price))
            elif current_price < (self.lower_sigma_5m3) and self.bollinger1h3_slope > slope_low_threshold:
                trade_flag = "sell"
                logging.info("5m3 bollinger logic: OK, lower_sigma + 0.1 = %s , current_price = %s" % ((self.lower_sigma_5m3), current_price))
            else:
                logging.info("5m3 bollinger logic: NG, upper_sigma = %s, lower_sigma = %s, current_price = %s" % (self.upper_sigma_5m3, self.lower_sigma_5m3, current_price))
        else:
            logging.info("1h3 bollinger logic: NG, upper_sigma = %s, lower_sigma = %s" % (self.upper_sigma_1h3, self.lower_sigma_1h3))

        return trade_flag

    def decideTrailLogic(self, stl_flag, current_ask_price, current_bid_price, current_price, order_price):
        first_flag = self.config_data["first_trail_mode"]
        second_flag = self.config_data["second_trail_mode"]
        first_take_profit = 0.3
        second_take_profit = 0.5


        if first_flag == "on":
            # 最小利確0.3を超えたら、トレールストップモードをONにする
            if self.order_kind == "buy":
                if (current_bid_price - order_price) > first_take_profit:
                    logging.info("SET TRAIL FIRST FLAG ON")
                    self.trail_flag = True
            elif self.order_kind == "sell":
                if (order_price - current_ask_price) > first_take_profit:
                    logging.info("SET TRAIL FIRST FLAG ON")
                    self.trail_flag = True


            # trail_flagがONで、含み益がなくなったら決済する
            if self.trail_flag == True and self.order_kind == "buy":
                if (current_bid_price - order_price) < 0:
                    logging.info("EXECUTE FIRST TRAIL STOP")
                    stl_flag = True
            elif self.trail_flag == True and self.order_kind == "sell":
                if (order_price - current_ask_price) < 0:
                    logging.info("EXECUTE FIRST TRAIL STOP")
                    stl_flag = True


        if second_flag == "on":
            # 含み益0.5超えたら、トレールストップの二段階目をONにする
            if self.order_kind == "buy":
                if (current_bid_price - order_price) > second_take_profit:
                    logging.info("SET TRAIL SECOND FLAG ON")
                    self.trail_second_flag = True
            elif self.order_kind == "sell":
                if (order_price - current_ask_price) > second_take_profit:
                    logging.info("SET TRAIL SECOND FLAG ON")
                    self.trail_second_flag = True


            # second_flagがTrueで且つ、含み益が0.3以下になったら決済する
            if self.trail_second_flag == True and self.order_kind == "buy":
                if (current_bid_price - order_price) < 0.3:
                    logging.info("EXECUTE TRAIL SECOND STOP")
                    stl_flag = True
            elif self.trail_second_flag == True and self.order_kind == "sell":
                if (order_price - current_ask_price) < 0.3:
                    logging.info("EXECUTE TRAIL SECOND STOP")
                    stl_flag = True

        return stl_flag

    def setIndicator(self, base_time):
        self.setBollinger5m3(base_time)
        self.setBollinger5m25(base_time)
        self.setBollinger1h3(base_time)
#        self.setSlopeEwma1h50(base_time)
        self.setSlopeBollinger1h3(base_time)
