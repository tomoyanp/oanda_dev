# coding: utf-8
# 実は逆張りモードのやつ
####################################################
# トレード判断
#　5分足 × 50移動平均のslopeが閾値(0.3)以上の時（トレンド発生と判断）
#　現在価格と5分足 200日移動平均線の比較（上にいれば買い、下にいれば売り）
#  現在価格の5分足終わり値が、ボリンジャーバンド2.5シグマにタッチすること
#
# 損切り判断
# １）反対側へのトレード判断がTrueの場合決済
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


class TrendFollowAlgo(SuperAlgo):
    def __init__(self, instrument, base_path, config_name, base_time):
        super(TrendFollowAlgo, self).__init__(instrument, base_path, config_name, base_time)
        self.base_price = 0
        self.setPrice(base_time)
        self.setIndicator(base_time)

    def decideTrade(self, base_time):
        trade_flag = "pass"
        try:
            if self.order_flag:
                pass
            else:
                seconds = base_time.second
                # 1分足の終値付近で計算ロジックに入る
                if seconds > 50:
                    self.setIndicator(base_time)
                    current_price = self.getCurrentPrice()
                    startend_price_threshold = 1.0
                    hilow_price_threshold = 0.5
                    baseline_touch_flag = False
                    low_slope_threshold  = -0.3
                    high_slope_threshold = 0.3

                    # bollingerバンド3シグマの幅が2以下、かつewma200の上にいること
                    if (self.upper_sigma_1h3 - self.lower_sigma_1h3) > 2 and self.ewma5m200_value < current_price:
                        if current_price > self.upper_sigma_1m25:
                            trade_flag = "sell" # 逆張り

                    # bollingerバンド3シグマの幅が2以下、かつewma200の下にいること
                    if (self.upper_sigma_1h3 - self.lower_sigma_1h3) > 2 and self.ewma5m200_value > current_price:
                        if current_price < self.lower_sigma_1m25:
                            trade_flag = "buy"
                    else:
                        trade_flag = "pass"

                    logging.info("####### decideTrade Logic base_time = %s #######" % base_time)
                    logging.info("5m 200ewma = %s, current_price = %s, upper_2.5sigma = %s, lower_2.5sigma = %s, trade_flag = %s" % (self.ewma5m200_value, current_price, self.upper_sigma_1m25, self.lower_sigma_1m25, trade_flag))
                    logging.info("upper 1h 3sigma = %s, lower 1h 3sigma = %s upper_sigma - lower_sigma = %s" % (self.upper_sigma_1h3, self.lower_sigma_1h3, (self.upper_sigma_1h3 - self.lower_sigma_1h3)))

                else:
                    pass


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
                    seconds = base_time.second
                    # 1分足の終値付近で計算ロジックに入る
                    if seconds > 50:
                        self.setIndicator(base_time)

                        # Stop Loss Algorithm
                        current_price = self.getCurrentPrice()
                        if self.order_kind == "buy":
                            if current_price < self.lower_sigma_1m3:
                                stl_flag = True
                            elif current_price > self.upper_sigma_1m25:
                                stl_flag = True

                        elif self.order_kind == "sell":
                            if current_price > self.upper_sigma_1m3:
                                stl_flag = True
                            elif current_price < self.lower_sigma_1m25:
                                stl_flag = True

                        logging.info("######### decideStl Logic base_time = %s ##########" % base_time)
                        logging.info("upper_sigma1m25 = %s, current_price = %s, lower_sigma1m25 = %s" %(self.upper_sigma_1m25, current_price, self.lower_sigma_1m25))
                        logging.info("upper_sigma1m3 = %s,lower_sigma1m3 = %s" %(self.upper_sigma_1m3, self.lower_sigma_1m3))


            return stl_flag
        except:
            raise


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
        # bollinger 1m 2.5sigma
        ind_type = "bollinger1m2.5"
        sql = "select upper_sigma, lower_sigma, base_line from INDICATOR_TABLE where instrument = \'%s\' and insert_time <= \'%s\' and type = \'%s\' order by insert_time DESC limit 1" % (self.instrument, base_time, ind_type)
        response = self.mysql_connector.select_sql(sql)
        self.upper_sigma_1m25 = response[0][0]
        self.lower_sigma_1m25 = response[0][1]
        self.base_line_1m25 = response[0][2]

         # bollinger 1m 3sigma
        ind_type = "bollinger1m3"
        sql = "select upper_sigma, lower_sigma, base_line from INDICATOR_TABLE where instrument = \'%s\' and insert_time <= \'%s\' and type = \'%s\' order by insert_time DESC limit 1" % (self.instrument, base_time, ind_type)
        response = self.mysql_connector.select_sql(sql)
        self.upper_sigma_1m3 = response[0][0]
        self.lower_sigma_1m3 = response[0][1]
        self.base_line_1m3 = response[0][2]


        # bollinger 5m 2.5sigma
        ind_type = "bollinger5m2.5"
        sql = "select upper_sigma, lower_sigma, base_line from INDICATOR_TABLE where instrument = \'%s\' and insert_time <= \'%s\' and type = \'%s\' order by insert_time DESC limit 1" % (self.instrument, base_time, ind_type)
        response = self.mysql_connector.select_sql(sql)
        self.upper_sigma_5m25 = response[0][0]
        self.lower_sigma_5m25 = response[0][1]
        self.base_line_5m25 = response[0][2]

        # bollinger 1h 3sigma
        ind_type = "bollinger1h3"
        sql = "select upper_sigma, lower_sigma, base_line from INDICATOR_TABLE where instrument = \'%s\' and insert_time <= \'%s\' and type = \'%s\' order by insert_time DESC limit 1" % (self.instrument, base_time, ind_type)
        response = self.mysql_connector.select_sql(sql)
        self.upper_sigma_1h3 = response[0][0]
        self.lower_sigma_1h3 = response[0][1]
        self.base_line_1h3 = response[0][2]

        # ewma5m50
        ind_type = "ewma5m50"
        sql = "select ewma_value, slope from INDICATOR_TABLE where instrument = \'%s\' and insert_time <= \'%s\' and type = \'%s\' order by insert_time DESC limit 1" % (self.instrument, base_time, ind_type)
        response = self.mysql_connector.select_sql(sql)
        self.ewma5m50_value = response[0][0]
        self.ewma5m50_slope = response[0][1]

        # ewma5m200
        ind_type = "ewma5m200"
        sql = "select ewma_value from INDICATOR_TABLE where instrument = \'%s\' and insert_time <= \'%s\' and type = \'%s\' order by insert_time DESC  limit 1" % (self.instrument, base_time, ind_type)
        response = self.mysql_connector.select_sql(sql)
        self.ewma5m200_value = response[0][0]

        # ewma1h200
        ind_type = "ewma1h200"
        sql = "select ewma_value from INDICATOR_TABLE where instrument = \'%s\' and insert_time <= \'%s\' and type = \'%s\' order by insert_time DESC  limit 1" % (self.instrument, base_time, ind_type)
        response = self.mysql_connector.select_sql(sql)
        self.ewma1h200_value = response[0][0]

        # high low price
        ind_type = "highlow"
#        span = 24 * 5
        span = 24
        end_time = base_time - timedelta(hours=1)
        sql = "select high_price, low_price from INDICATOR_TABLE where instrument = \'%s\' and insert_time <= \'%s\' and type = \'%s\' order by insert_time DESC limit %s" % (self.instrument, base_time, ind_type, span)
        response = self.mysql_connector.select_sql(sql)
        high_price_list = []
        low_price_list = []
        for res in response:
            high_price_list.append(res[0])
            low_price_list.append(res[1])

        self.high_price = max(high_price_list)
        self.low_price =  min(low_price_list)

