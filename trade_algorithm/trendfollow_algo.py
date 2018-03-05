# coding: utf-8
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

    def decideTrade(self, base_time):
        trade_flag = "pass"
        try:
            if self.order_flag:
                pass
            else:
                minutes = base_time.minute
                seconds = base_time.second
                # 5分足の終値付近で計算ロジックに入る
                if (minutes % 5 == 4) and seconds > 50:
                    current_price = self.getCurrentPrice()
                    startend_price_threshold = 1.0
                    hilow_price_threshold = 0.5
                    baseline_touch_flag = False
                    low_slope_threshold  = -0.3
                    high_slope_threshold = 0.3

                    # 高値安値チェックのみに引っかかった場合、breakモードに突入する
                    if self.break_wait_flag == "buy":
                        logging.info("BUY RANGE BREAK MODE LOGIC current_price = %s, hi_price = %s, comp = %s" %(current_price, self.high_price, (current_price - self.high_price)))
                        if (current_price - self.high_price) > 0.1:
                            logging.info("EXECUTE BUY RANGE BREAK MODE")
                            trade_flag = "buy"
                        else:
                            pass
                    elif self.break_wait_flag == "sell":
                        logging.info("SELL RANGE BREAK MODE LOGIC current_price = %s, low_price = %s, comp = %s" %(current_price, self.low_price, (self.low_price - current_price)))
                        if (self.low_price - current_price) > 0.1:
                            logging.info("EXECUTE SELL RANGE BREAK MODE")
                            trade_flag = "sell"
                        else:
                            pass
                    else:
                        pass

                    # slopeが上向き、現在価格が移動平均(EWMA200(5分), EWMA200(1時間))より上、現在価格がbollinger3_sigmaより上にいる
                    if ((self.slope - high_slope_threshold) > 0) and (self.ewma5m200_value < current_price) and (current_price > self.5m25_upper_sigma) and (self.ewma1h200_value < current_price):
                        # 現在価格が前日高値に対し0.5以内にいる or 当日の値動きが1.0以上ある場合、トレードしない
                        if float(self.high_price - hilow_price_threshold) < float(current_price) < (float(self.high_price) + 0.1):
                            self.break_wait_flag = "buy"
                            logging.info("MOVING RANGE BREAK MODE = buy")
                        else:
                            logging.info("EXECUTE BUY NORMAL MODE")
                            trade_flag = "buy"
                    # slopeが下向き、現在価格が移動平均(EWMA200(5分), EWMA200(1時間)より下、現在価格がbollinger3_sigmaより下にいる
                    elif ((self.slope - low_slope_threshold) < 0) and (self.ewma5m200_value > current_price) and (current_price < self.5m25_lower_sigma) and (self.ewma1h200_value > current_price):
                        # 現在価格が前日安値に対し0.5以内にいる or 当日の値動きが1.0以上ある場合、トレードしない
                        if float(self.low_price + hilow_price_threshold) > float(current_price) > (float(self.low_price) - 0.1):
                            self.break_wait_flag = "sell"
                            logging.info("MOVING RANGE BREAK MODE = sell")
                        else:
                            logging.info("EXECUTE SELL NORMAL MODE")
                            trade_flag = "sell"

                    else:
                        trade_flag = "pass"

                    logging.info("####### decideTrade Logic base_time = %s #######" % base_time)
                    logging.info("break_wait_flag = %s" % (self.break_wait_flag))
                    logging.info("hi_price = %s, low_price = %s" % (self.high_price, self.low_price))
                    logging.info("5m 50ewma slope = %s, 5m 200ewma = %s, 1h 200ewma = %s, current_price = %s, upper_2.5sigma = %s, lower_2.5sigma = %s, trade_flag = %s" % (self.slope, self.ewma5m200_value, self.ewma1h200_value, current_price, self.5m25_upper_sigma, self.5m25_lower_sigma, trade_flag))

                else:
                    pass

                logging.info("####### decideTrade Logic base_time = %s #######" % base_time)
                logging.info("Not end time")

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
                    # 5分足の終値付近で計算ロジックに入る
                    if (minutes % 5 == 4) and seconds > 50:

                        # Stop Loss Algorithm
                        # get Bollinger Band sigma 2.5
                        upper_sigma = self.bollinger_2p5sigma_dataset["upper_sigma"]
                        lower_sigma = self.bollinger_2p5sigma_dataset["lower_sigma"]
                        base_line = self.bollinger_2p5sigma_dataset["base_line"]

                        current_ask_price = self.ask_price_list[-1]
                        current_bid_price = self.bid_price_list[-1]
                        current_price = self.getCurrentPrice()
                        order_price = self.getOrderPrice()

                        # 移動平均の取得(WMA50)
                        ewma50 = self.ewma50_5m_dataset["ewma_value"]
                        slope = self.ewma50_5m_dataset["slope"]

                        low_slope_threshold  = -0.3
                        high_slope_threshold = 0.3

                        # 損切り
                        # slopeが上向き、現在価格がbollinger2.5_sigmaより上にいる
                        if ((self.slope - high_slope_threshold) > 0) and (current_price > self.upper_sigma) and self.order_kind == "sell":
                            logging.info("EXECUTE SETTLEMENT")
                            stl_flag = True
                        # slopeが下向き、現在価格がbollinger2.5_sigmaより下にいる
                        elif ((self.slope - low_slope_threshold) < 0) and (current_price < self.lower_sigma) and self.order_kind == "buy":
                            logging.info("EXECUTE SETTLEMENT")
                            stl_flag = True

                        # 最小利確0.3以上、移動平均にぶつかったら
                        min_take_profit = 0.3
                        if self.order_kind == "buy":
                            if (current_bid_price - order_price) > min_take_profit:
                                if -0.02 < (current_price - self.5m25_base_line) < 0.02:
                                    logging.info("EXECUTE STL")
                                    stl_flag = True
                        elif self.order_kind == "sell":
                            if (order_price - current_ask_price) > min_take_profit:
                                if -0.02 < (current_price - self.5m25_base_line) < 0.02:
                                    logging.info("EXECUTE STL")
                                    stl_flag = True

                        stl_flag = self.decideTrailLogic(stl_flag, current_ask_price, current_bid_price, current_price, order_price)
                        logging.info("######### decideStl Logic base_time = %s ##########" % base_time)
                        logging.info("upper_sigma = %s, current_price = %s, lower_sigma = %s, base_line = %s" %(self.2m25_upper_sigma, current_price, self.5m25_lower_sigma, self.5m25_base_line))
                        logging.info("order_price = %s, slope = %s" %(order_price, self.slope))
            else:
                pass

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
        # bollinger 5m 2.5sigma
        ind_type = "bollinger5m2.5"
        sql = "select upper_sigma, lower_sigma, base_line from INDICATOR_TABLE where insert_time <= \'%s\' and type = \'%s\' order by insert_time DESC " % (self.instrument, base_time, ind_type)
        response = self.mysql_connector.select_sql(sql)
        self.5m25_upper_sigma = response[0][0]
        self.5m25_lower_sigma = response[0][1]
        self.5m25_base_line = response[0][2]

        # bollinger 1h 3sigma
        ind_type = "bollinger1h3"
        sql = "select upper_sigma, lower_sigma, base_line from INDICATOR_TABLE where instrument = \'%s\' and insert_time <= \'%s\' and type = \'%s\' order by insert_time DESC " % (self.instrument, base_time, ind_type)
        response = self.mysql_connector.select_sql(sql)
        self.1h3_upper_sigma = response[0][0]
        self.1h3_lower_sigma = response[0][1]
        self.1h3_base_line = response[0][2]

        # ewma5m50
        ind_type = "ewma5m50"
        sql = "select ewma_value, slope from INDICATOR_TABLE where instrument = \'%s\' and insert_time <= \'%s\' and type = \'%s\' order by insert_time DESC " % (self.instrument, base_time, ind_type)
        response = self.mysql_connector.select_sql(sql)
        self.ewma5m50_value = response[0][0]
        self.ewma5m50_slope = response[0][1]

        # ewma5m200
        ind_type = "ewma5m200"
        sql = "select ewma_value from INDICATOR_TABLE where instrument = \'%s\' and insert_time <= \'%s\' and type = \'%s\' order by insert_time DESC " % (self.instrument, base_time, ind_type)
        response = self.mysql_connector.select_sql(sql)
        self.ewma5m200_value = response[0][0]

        # ewma1h200
        ind_type = "ewma1h200"
        sql = "select ewma_value from INDICATOR_TABLE where instrument = \'%s\' and insert_time <= \'%s\' and type = \'%s\' order by insert_time DESC " % (self.instrument, base_time, ind_type)
        response = self.mysql_connector.select_sql(sql)
        self.ewma1h200_value = response[0][0]

        # high low price
        ind_type = "highlow"
        sql = "select high_price, low_price from INDICATOR_TABLE where instrument = \'%s\' and insert_time <= \'%s\' and type = \'%s\' order by insert_time DESC " % (self.instrument, base_time, ind_type)
        response = self.mysql_connector.select_sql(sql)
        self.high_price = response[0][0]
        self.low_price = response[0][1]
