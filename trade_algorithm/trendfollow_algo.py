# coding: utf-8
####################################################
# トレード判断
#　5分足 × 50移動平均のslopeが閾値(0.3)以上の時（トレンド発生と判断）
#　現在価格と5分足 200日移動平均線の比較（上にいれば買い、下にいれば売り）
#　現在価格が、前日（06:00-05:59）の高値、安値圏から0.5以上幅があること
#　　前日が陰線引けであれば、安値圏と比較
#　　前日が陽線引けであれば、高値圏と比較
#　当日の高値、安値の差が1.0以内であること
#　　下落幅が1.0以上であれば、売りはなし
#　　上昇幅が1.0以上であれべ、買いはなし
#  現在価格が、ボリンジャーバンド2.5シグマにタッチすること
#
# 損切り判断
# １）反対側の3シグマにヒットしたら決済する
#
# 利確判断
# １）含み益が最低利益(10pips)を確保しているか確認
# ２）現在価格が移動平均線にタッチしたら決済する
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
                current_price = self.getCurrentPrice()

                # 前日高値、安値の計算
                hi_price = self.hi_low_price_dataset["hi_price"]
                low_price = self.hi_low_price_dataset["low_price"]


                # 当日始め値と現在価格の差を取得(現在価格-始値)

                # 移動平均じゃなく、トレンド発生＋2.5シグマ突破でエントリーに変えてみる
                upper_sigma = self.bollinger_2p5sigma_dataset["upper_sigma"]
                lower_sigma = self.bollinger_2p5sigma_dataset["lower_sigma"]
                base_line = self.bollinger_2p5sigma_dataset["base_line"]

                ewma50 = self.ewma50_5m_dataset["ewma_value"]
                slope = self.ewma50_5m_dataset["slope"]
                ewma200 = self.ewma200_5m_dataset["ewma_value"]
                ewma200_1h = self.ewma200_1h_dataset["ewma_value"]

                startend_price_threshold = 1.0
                hilow_price_threshold = 0.5
                baseline_touch_flag = False
                low_slope_threshold  = -0.3
                high_slope_threshold = 0.3

                # 高値安値チェックのみに引っかかった場合、breakモードに突入する
                if self.break_wait_flag == "buy":
                    logging.info("BUY RANGE BREAK MODE LOGIC current_price = %s, hi_price = %s, comp = %s" %(current_price, hi_price, (current_price - hi_price)))
                    if (current_price - hi_price) > 0.1:
                        logging.info("EXECUTE BUY RANGE BREAK MODE")
                        trade_flag = "buy"
                    else:
                        pass
                elif self.break_wait_flag == "sell":
                    logging.info("SELL RANGE BREAK MODE LOGIC current_price = %s, low_price = %s, comp = %s" %(current_price, low_price, (low_price - current_price)))
                    if (low_price - current_price) > 0.1:
                        logging.info("EXECUTE SELL RANGE BREAK MODE")
                        trade_flag = "sell"
                    else:
                        pass
                else:
                    pass

                # slopeが上向き、現在価格が移動平均(EWMA200(5分), EWMA200(1時間))より上、現在価格がbollinger3_sigmaより上にいる
                if ((slope - high_slope_threshold) > 0) and (ewma200 < current_price) and (current_price > upper_sigma) and (ewma200_1h < current_price):
                    # 現在価格が前日高値に対し0.5以内にいる or 当日の値動きが1.0以上ある場合、トレードしない
                    if float(hi_price - hilow_price_threshold) < float(current_price) < (float(hi_price) + 0.1):
                        self.break_wait_flag = "buy"
                        logging.info("MOVING RANGE BREAK MODE = buy")
                    else:
                        logging.info("EXECUTE BUY NORMAL MODE")
                        trade_flag = "buy"
                # slopeが下向き、現在価格が移動平均(EWMA200(5分), EWMA200(1時間)より下、現在価格がbollinger3_sigmaより下にいる
                elif ((slope - low_slope_threshold) < 0) and (ewma200 > current_price) and (current_price < lower_sigma) and (ewma200_1h > current_price):
                    # 現在価格が前日安値に対し0.5以内にいる or 当日の値動きが1.0以上ある場合、トレードしない
                    if float(low_price + hilow_price_threshold) > float(current_price) > (float(low_price) - 0.1):
                        self.break_wait_flag = "sell"
                        logging.info("MOVING RANGE BREAK MODE = sell")
                    else:
                        logging.info("EXECUTE SELL NORMAL MODE")
                        trade_flag = "sell"
                else:
                    trade_flag = "pass"

                logging.info("####### decideTrade Logic base_time = %s #######" % base_time)
                logging.info("break_wait_flag = %s" % (self.break_wait_flag))
                logging.info("hi_price = %s, low_price = %s" % (hi_price, low_price))
                logging.info("5m 50ewma slope = %s, 5m 200ewma = %s, 1h 200ewma = %s, current_price = %s, upper_2.5sigma = %s, lower_2.5sigma = %s, trade_flag = %s" % (slope, ewma200, ewma200_1h, current_price, upper_sigma, lower_sigma, trade_flag))

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
                    if ((slope - high_slope_threshold) > 0) and (current_price > upper_sigma) and self.order_kind == "sell":
                        logging.info("EXECUTE SETTLEMENT")
                        stl_flag = True
                    # slopeが下向き、現在価格がbollinger2.5_sigmaより下にいる
                    elif ((slope - low_slope_threshold) < 0) and (current_price < lower_sigma) and self.order_kind == "buy":
                        logging.info("EXECUTE SETTLEMENT")
                        stl_flag = True

                    # 最小利確0.3以上、移動平均にぶつかったら
                    min_take_profit = 0.3
                    if self.order_kind == "buy":
                        if (current_bid_price - order_price) > min_take_profit:
                            if -0.02 < (current_price - base_line) < 0.02:
                                logging.info("EXECUTE STL")
                                stl_flag = True
                    elif self.order_kind == "sell":
                        if (order_price - current_ask_price) > min_take_profit:
                            if -0.02 < (current_price - base_line) < 0.02:
                                logging.info("EXECUTE STL")
                                stl_flag = True

                    stl_flag = self.decideTrailLogic(stl_flag, current_ask_price, current_bid_price, current_price, order_price)
                    logging.info("######### decideStl Logic base_time = %s ##########" % base_time)
                    logging.info("upper_sigma = %s, current_price = %s, lower_sigma = %s, base_line = %s" %(upper_sigma, current_price, lower_sigma, base_line))
                    logging.info("order_price = %s, slope = %s" %(order_price, slope))
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




#    def decideTrailLogic(self, stl_flag, current_ask_price, current_bid_price, current_price, order_price):
#        first_flag = self.config_data["first_trail_mode"]
#        #second_flag = self.config_data["second_trail_mode"]
#        first_take_profit = 0.3
#        #second_take_profit = 0.5
#
#
#        if first_flag == "on":
#            # 最小利確0.3を超えたら、トレールストップモードをONにする
#            if self.order_kind == "buy":
#                if (current_bid_price - order_price) > first_take_profit:
#                    logging.info("SET TRAIL FIRST FLAG ON")
#                    self.trail_flag = True
#                    self.trail_price = current_bid_price
#            elif self.order_kind == "sell":
#                if (order_price - current_ask_price) > first_take_profit:
#                    logging.info("SET TRAIL FIRST FLAG ON")
#                    self.trail_flag = True
#                    self.trail_price = current_ask_price
#
#            # trail_flagがONで、含み益がなくなったら決済する
#            if self.trail_flag == True and self.order_kind == "buy":
#                # 現在価格がtrail_priceより高かった場合、更新する
#                if current_bid_price > self.trail_price:
#                    self.trail_price = current_bid_price
#
#                # trail_priceよりも0.3以上下回ったら決済する
#                if (current_bid_price - (self.trail_price - first_take_profit)) < 0:
#                    logging.info("EXECUTE FIRST TRAIL STOP")
#                    stl_flag = True
#
#
#            elif self.trail_flag == True and self.order_kind == "sell":
#                # 現在価格がtrail_priceより安かったら更新する
#                if current_ask_price < self.trail_price:
#                    self.trail_price = current_ask_price
#
#                # tail_priceより0.3以上上回ったら決済する
#                if ((self.trail_price + first_take_profit) - current_ask_price) < 0:
#                    logging.info("EXECUTE FIRST TRAIL STOP")
#                    stl_flag = True
#
#        return stl_flag


    def getHiLowPriceBeforeDay(self, base_time)
        # 過去25時間分
        term = 25 * 3600
        # そのうち直近1時間は排除
        exclude_term = 1 * 3600 * -1

        # listから対象期間抽出
        ask_price_list = self.ask_price_list[term:]
        bid_price_list = self.bid_price_list[term:]

        # そのうち直近1時間排除
        ask_price_list = ask_price_list[:exclude_term]
        bid_price_list = bid_price_list[:exclude_term]

        ask_price_list = pd.Series(ask_price_list)
        bid_price_list = pd.Series(bid_price_list)
        current_price_list = (ask_price_list + bid_price_list) / 2
        high_price = current_price_list.max()
        min_price = current_price_list.min()

        retrun high_price, min_price

#    def getHiLowPriceBeforeDay(self, base_time):
#        before_day = base_time - timedelta(days=1)

#        # 高値安値は直近1時間まで見てみる
#        before_end_time = base_time - timedelta(hours=1)
#        before_end_time = before_end_time.strftime("%Y-%m-%d %H:%M:%S")

#        before_start_time = before_day.strftime("%Y-%m-%d 07:00:00")
#        before_start_time = datetime.strptime(before_start_time, "%Y-%m-%d %H:%M:%S")
#        if decideMarket(before_start_time):
#            before_start_time = before_day.strftime("%Y-%m-%d 07:00:00")
#        else:
#            before_start_day = base_time - timedelta(days=3)
#            before_start_time = before_start_day.strftime("%Y-%m-%d 07:00:00")

#        sql = "select max(ask_price), max(bid_price) from %s_TABLE where insert_time > \'%s\' and insert_time < \'%s\'" % (self.instrument, before_start_time, before_end_time)
#        print sql
#        response = self.mysqlConnector.select_sql(sql)

#        for res in response:
#            ask_price = res[0]
#            bid_price = res[1]

#        hi_price = (ask_price + bid_price)/2

#        sql = "select min(ask_price), min(bid_price) from %s_TABLE where insert_time > \'%s\' and insert_time < \'%s\'" % (self.instrument, before_start_time, before_end_time)
#        print sql
#        response = self.mysqlConnector.select_sql(sql)

#        for res in response:
#            ask_price = res[0]
#            bid_price = res[1]

#        min_price = (ask_price + bid_price)/2

#        return hi_price, min_price

#    def getStartEndPrice(self, base_time):
#        # 日またぎの場合
#        if 0 <= int(base_time.hour) <= 6:
#            start_day = base_time - timedelta(days=1)
#            start_time = start_day.strftime("%Y-%m-%d 07:00:00")
#        else:
#            start_time = base_time.strftime("%Y-%m-%d 07:00:00")

#        end_time = base_time.strftime("%Y-%m-%d %H:%M:%S")

#        sql = "select ask_price, bid_price from %s_TABLE where insert_time = \'%s\'" % (self.instrument, start_time)

#        response = self.mysqlConnector.select_sql(sql)
#        for res in response:
#            ask_price = res[0]
#            bid_price = res[1]

#        start_price = (ask_price + bid_price)/2

#        sql = "select ask_price, bid_price from %s_TABLE where insert_time = \'%s\'" % (self.instrument, end_time)

#        response = self.mysqlConnector.select_sql(sql)
#        for res in response:
#            ask_price = res[0]
#            bid_price = res[1]

#        end_price = (ask_price + bid_price)/2

#        return start_price, end_price



    def getLongEwma(self, base_time):
        # 移動平均の取得(WMA200 * 1h candles)
        wma_length = 200
        candle_width = 3600

        index = wma_length * candle_width * -1

        # listから対象期間抽出
        ask_price_list = self.ask_price_list[index:]
        bid_price_list = self.bid_price_list[index:]

        ewma200 = getEWMA(ask_price_list, bid_price_list, wma_length, candle_width)

        return ewma200

    def setInitialIndicator(self, base_time):
        # 前日高値、安値の計算
        hi_price, low_price = self.getHiLowPriceBeforeDay(base_time)
        self.hi_low_price_dataset = {"hi_price": hi_price,
                                     "low_price": low_price,
                                     "get_time": base_time}

        # 1時間足200日移動平均線を取得する
        ewma200_1h = self.getLongEwma(base_time)
        self.ewma200_1h_dataset = {"ewma_value": ewma200_1h[-1],
                               "get_time": base_time}

        # 移動平均じゃなく、トレンド発生＋3シグマ突破でエントリーに変えてみる
        window_size = 28
        candle_width = 300
        sigma_valiable = 2.5
        data_set = getBollingerDataSet(self.ask_price_list, self.bid_price_list, window_size, sigma_valiable, candle_width)
        self.bollinger_2p5sigma_dataset = {"upper_sigma": data_set["upper_sigmas"][-1],
                                           "lower_sigma": data_set["lower_sigmas"][-1],
                                           "base_line": data_set["base_lines"][-1],
                                           "get_time": base_time}

        # 移動平均の取得(WMA50)
        wma_length = 50
        ewma50 = getEWMA(self.ask_price_list, self.bid_price_list, wma_length, candle_width)
        # 短期トレンドの取得
        slope_length = (10 * candle_width) * -1
        slope_list = ewma50[slope_length:]
        slope = getSlope(slope_list)
        self.ewma50_5m_dataset = {"ewma_value": ewma50[-1],
                               "slope": slope,
                               "get_time": base_time}

        # 移動平均の取得(WMA200)
        wma_length = 200
        ewma200 = getEWMA(self.ask_price_list, self.bid_price_list, wma_length, candle_width)
        self.ewma200_5m_dataset = {"ewma_value": ewma200[-1],
                                "get_time": base_time}

        logging.info("######### setInitialIndicator base_time = %s ############" % base_time)
        logging.info("self.hi_low_price_dataset = %s" % self.hi_low_price_dataset)
        logging.info("self.bollinger_2p5sigma_dataset = %s" % self.bollinger_2p5sigma_dataset)
        logging.info("self.ewma50_5m_dataset = %s" % self.ewma50_5m_dataset)
        logging.info("self.ewma200_5m_dataset = %s" % self.ewma200_5m_dataset)

    def setIndicator(self, base_time):
        #logging.info("######### setIndicator base_time = %s ############" % base_time)
        polling_time = 1
        cmp_time = self.hi_low_price_dataset["get_time"] + timedelta(hours=polling_time)
        if cmp_time < base_time:
            # 前日高値、安値の計算
            hi_price, low_price = self.getHiLowPriceBeforeDay(base_time)
            self.hi_low_price_dataset = {"hi_price": hi_price,
                                         "low_price": low_price,
                                         "get_time": base_time}

            # 1時間足200日移動平均線を取得する
            ewma200_1h = self.getLongEwma(base_time)
            self.ewma200_1h_dataset = {"ewma_value": ewma200_1h[-1],
                                       "get_time": base_time}


        polling_time = 300
        cmp_time = self.bollinger_2p5sigma_dataset["get_time"] + timedelta(seconds=polling_time)
        if cmp_time < base_time:
            # bollinger_band 2.5sigma
            window_size = 28
            candle_width = 300
            sigma_valiable = 2.5
            data_set = getBollingerDataSet(self.ask_price_list, self.bid_price_list, window_size, sigma_valiable, candle_width)
            self.bollinger_2p5sigma_dataset = {"upper_sigma": data_set["upper_sigmas"][-1],
                                               "lower_sigma": data_set["lower_sigmas"][-1],
                                               "base_line": data_set["base_lines"][-1],
                                               "get_time": base_time}

            # 移動平均の取得(WMA50)
            wma_length = 50
            ewma50 = getEWMA(self.ask_price_list, self.bid_price_list, wma_length, candle_width)
            # 短期トレンドの取得
            slope_length = (10 * candle_width) * -1
            slope_list = ewma50[slope_length:]
            slope = getSlope(slope_list)
            self.ewma50_5m_dataset = {"ewma_value": ewma50[-1],
                                   "slope": slope,
                                   "get_time": base_time}

            # 移動平均の取得(WMA200)
            wma_length = 200
            ewma200 = getEWMA(self.ask_price_list, self.bid_price_list, wma_length, candle_width)
            self.ewma200_5m_dataset = {"ewma_value": ewma200[-1],
                                    "get_time": base_time}
