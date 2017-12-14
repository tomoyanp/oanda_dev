# coding: utf-8

import sys
import os
import traceback
import json

from datetime import datetime, timedelta
from step_wise_algo import StepWiseAlgo
from hi_low_algo import HiLowAlgo
from start_end_algo import StartEndAlgo
from time_trend_algo import TimeTrendAlgo
from bollinger_algo import BollingerAlgo
from evo_bollinger_algo import EvoBollingerAlgo
from oanda_wrapper import OandaWrapper
from common import instrument_init, account_init, decide_up_down_before_day
import time
import logging

class TradeWrapper:
    def __init__(self, instrument, mode, test_mode, base_path, config_name, args):
        # trueであれば、テストモードにする
        self.test_mode = test_mode

        # rootの絶対パス
        self.base_path = base_path

        # デモもしくは本番
        account_data = account_init(mode, self.base_path)
        self.account_id   = account_data["account_id"]
        self.token        = account_data["token"]
        self.env          = account_data["env"]

        # パラメータセット
        # configが一つだと、わかりづらいのでネーミングを変える instrument.config_timetrend, instrument.config_bollingerとかで使い分け
        self.config_name        = config_name
        self.config_data        = instrument_init(instrument, self.base_path, self.config_name)
        units                   = self.config_data["units"]
        self.instrument         = instrument
        # 使うものインスタンス化
        self.oanda_wrapper      = OandaWrapper(self.env, self.account_id, self.token, units)


        # 指値でいつの間にか決済されてしまったときはこれでスリープさせる
        self.stl_sleep_flag = False

        now = datetime.now()
        base_time = now.strftime("%Y%m%d%H%M%S")
        self.result_file = open("%s/result/%s.result" % (self.base_path, base_time), "w")
        self.result_file.write("#########################\n")
        tmp = ""
        for arg in args:
            tmp = tmp + arg + " "
        self.result_file.write("# %s\n" % tmp)
        lst = sorted(self.config_data)
        for elm in lst:
            self.result_file.write("# %s = %s\n" % (elm, self.config_data[elm]))
        self.result_file.flush()

    def setTradeAlgo(self, algo):
        if algo == "step":
            self.trade_algo = StepWiseAlgo(self.instrument, self.base_path, self.config_name)
        elif algo == "startend":
            self.trade_algo = StartEndAlgo(self.instrument, self.base_path, self.config_name)
        elif algo == "timetrend":
            self.trade_algo = TimeTrendAlgo(self.instrument, self.base_path, self.config_name)
        elif algo == "bollinger":
            self.trade_algo = BollingerAlgo(self.instrument, self.base_path, self.config_name)
        elif algo == "evo_bollinger":
            self.trade_algo = EvoBollingerAlgo(self.instrument, self.base_path, self.config_name)
#        else:
#            self.trade_algo = HiLowAlgo(self.instrument, self.base_path, self.config_name)


    # 今ポジションを持っているか確認
    # なければ、フラグをリセットする
    def checkPosition(self):
        logging.info("=== Start TradeWrapper.checkPosition Logic ===")
        logging.info("test_mode flag=%s" % self.test_mode)
        if self.test_mode:
            pass
        else:
            position_flag = self.oanda_wrapper.get_trade_position(self.instrument)
            logging.info("trade_position flag=%s" % position_flag)
            if position_flag == False:
                # 決済した直後であればスリープする
                logging.info("stl_sleep_flag=%s" % self.stl_sleep_flag)
                trade_id = self.trade_algo.getTradeId()
                if self.stl_sleep_flag and trade_id != 0:

        else:
            self.trade_algo = HiLowAlgo(self.instrument, self.base_path, self.config_name)


    # 今ポジションを持っているか確認
    # なければ、フラグをリセットする
    def checkPosition(self):
        logging.info("=== Start TradeWrapper.checkPosition Logic ===")
        logging.info("test_mode flag=%s" % self.test_mode)
        if self.test_mode:
            pass
        else:
            position_flag = self.oanda_wrapper.get_trade_position(self.instrument)
            logging.info("trade_position flag=%s" % position_flag)
            if position_flag == False:
                # 決済した直後であればスリープする
                logging.info("stl_sleep_flag=%s" % self.stl_sleep_flag)
                trade_id = self.trade_algo.getTradeId()
                if self.stl_sleep_flag and trade_id != 0:

                    nowftime = self.trade_algo.getCurrentTime()
                    self.result_file.write("===== EXECUTE SETTLEMENT STOP OR LIMIT ORDER at %s ======\n" % nowftime)
                    order_kind = self.trade_algo.getOrderKind()
                    order_price = self.trade_algo.getOrderPrice()
                    stl_price = self.trade_algo.getCurrentPrice()
                    self.trade_algo.setStlPrice(order_price)

                    if order_kind == "buy":
                        profit = stl_price - order_price
                    else:
                        profit = order_price - stl_price

                    logging.info("order_kind=%s" % order_kind)
                    logging.info("order_price=%s" % order_price)
                    logging.info("stl_price=%s" % stl_price)
                    logging.info("profit=%s" % profit)
                    if profit > 0:
                        sleep_time = self.config_data["stl_sleep_vtime"]
                    else:
                        sleep_time = self.config_data["stl_sleep_ltime"]

                    self.result_file.write("ORDER_PRICE=%s, STL_PRICE=%s, ORDER_KIND=%s, PROFIT=%s\n" % (order_price, stl_price, order_kind, profit))
                    self.result_file.write("PROFIT=%s\n" % profit)
                    self.result_file.write("======================================================\n")
                    self.result_file.flush()
                    time.sleep(sleep_time)
                    self.stl_sleep_flag = False

                self.trade_algo.resetFlag()
            else:
                self.trade_algo.setOrderFlag(True)
                self.stl_sleep_flag = True

            logging.info("=== End TradeWrapper.checkPosition Logic ===")

    def setInstrumentRespoonse(self, base_time):
        logging.info("=== Start TradeWrapper.setInstrumentRespoonse Logic ===")
        logging.info("base_time=%s" % base_time)
        self.trade_algo.setPriceTable(base_time)
        #self.trade_algo.setNewPriceTable(base_time)

        logging.info("=== End TradeWrapper.setInstrumentRespoonse Logic ===")

    def stlDecisionWrapper(self, base_time):
        logging.info("=== Start TradeWrapper.stlDecisionWrapper Logic ===")

        sleep_time = self.config_data["sleep_time"]
        order_flag = self.trade_algo.getOrderFlag()
        logging.info("sleep_time=%s" % sleep_time)
        logging.info("order_flag=%s" % order_flag)

        # 建玉があれば、決済するかどうか判断
        if order_flag:
            stl_flag = self.trade_algo.decideStl(base_time)
            trade_id = self.trade_algo.getTradeId()
            logging.info("stl_flag=%s" % stl_flag)
            logging.info("trade_id=%s" % trade_id)
            logging.info("test_mode=%s" % self.test_mode)

            #trade_idがある場合もしくはテストモードであれば
            if self.test_mode == True or trade_id != 0:

                # テストモードであれば、指値のチェックをフォローしてあげる
                test_stl_flag = False
                if stl_flag == False and self.test_mode:
                    test_stl_flag = self.trade_algo.decideReverceStl()
                    stl_flag = test_stl_flag

                logging.info("stl_flag=%s" % stl_flag)
                # stl_flagが立ってたら決済する
                if stl_flag:
                    nowftime = self.trade_algo.getCurrentTime()
                    order_kind = self.trade_algo.getOrderKind()
                    order_price = self.trade_algo.getOrderPrice()
                    stl_price = self.trade_algo.getCurrentPrice()
                    self.trade_algo.setStlPrice(order_price)
                    logging.info("nowftime=%s" % nowftime)
                    logging.info("order_kind=%s" % order_kind)
                    logging.info("order_price=%s" % order_price)
                    logging.info("stl_price=%s" % stl_price)

                    # 決済注文
                    if self.test_mode:
                        pass
                    else:
                        trade_id = self.trade_algo.getTradeId()
                        response = self.oanda_wrapper.close_trade(trade_id)
                        logging.info("close_trade_response=%s" % response)
                        stl_price = response["price"]
                        logging.info("response.stl_price=%s" % stl_price)

                    # 利益計算
                    if order_kind == "buy":
                        profit = stl_price - order_price
                    elif order_kind == "sell":
                        profit = order_price - stl_price
                    else:
                        raise ValueError("order_kind is invalid. value=%s" % order_kind)

                    # stl_sleep_ltimeはストップオーダーした時だけ使うようにしてみる
                    sleep_time = self.config_data["stl_sleep_vtime"]

                    # testモードの時はちゃんとsleepしないとダメ
                    if self.test_mode and test_stl_flag:
                        if profit > 0:
                            sleep_time = self.config_data["stl_sleep_vtime"]
                        else:
                            sleep_time = self.config_data["stl_sleep_ltime"]

                    logging.info("sleep_time=%s" % sleep_time)

                    # 計算した利益を結果ファイルに出力
                    self.result_file.write("===== EXECUTE SETTLEMENT at %s ======\n" % nowftime)
                    self.result_file.write("ORDER_PRICE=%s, STL_PRICE=%s, ORDER_KIND=%s, PROFIT=%s\n" % (order_price, stl_price, order_kind, profit))
                    self.result_file.write("PROFIT=%s\n" % profit)
                    self.result_file.write("======================================================\n")
                    self.result_file.flush()

                    # flagの初期化
                    self.trade_algo.resetFlag()
                    self.stl_sleep_flag = False

                else:
                    pass
            else:
                pass
        else:
            pass

        polling_time = sleep_time
        logging.info("=== End TradeWrapper.stlDecisionWrapper Logic ===")
        return polling_time

    def tradeDecisionWrapper(self, base_time):
        logging.info("=== Start TradeWrapper.tradeDecisionWrapper Logic ===")
        order_flag = self.trade_algo.getOrderFlag()
        logging.info("order_flag=%s" % order_flag)

        if order_flag:
            pass
        else:
            trade_flag = self.trade_algo.decideTrade(base_time)
            logging.info("decideTrade.trade_flag=%s" % trade_flag)
            trade_flag = self.trade_algo.decideTradeTime(base_time, trade_flag)
            logging.info("decideTradeTime.trade_flag=%s" % trade_flag)
            trade_flag = self.trade_algo.checkTrend(base_time, trade_flag)
            logging.info("checkTrend.trade_flag=%s" % trade_flag)

            if trade_flag == "pass":
                self.trade_algo.resetFlag()
            else:
                nowftime = self.trade_algo.getCurrentTime()
                logging.info("nowftime=%s" % nowftime)
                order_price = self.trade_algo.getCurrentPrice()
                logging.info("order_price=%s" % order_price)
                threshold_list = self.trade_algo.calcThreshold(trade_flag)
                logging.info("threshold_list=%s" % threshold_list)

                logging.info("test_mode=%s" % self.test_mode)
                if self.test_mode or trade_flag == "pass":
                    pass
                else:
                    response = self.oanda_wrapper.order(trade_flag, self.instrument, threshold_list["stoploss"], threshold_list["takeprofit"])
                    logging.info("order_response=%s" % response)
                    order_price = response["price"]
                    logging.info("response.order_price=%s" % order_price)
                    self.trade_algo.setTradeId(response)
                    # 約定後はちょっとスリープしないとおかしなことになる
                    time.sleep(10)

                self.result_file.write("===== EXECUTE ORDER at %s ======\n" % nowftime)
                self.result_file.write("ORDER_PRICE=%s, TRADE_FLAG=%s\n" % (order_price, trade_flag))
                self.result_file.flush()
                order_flag = True
                self.trade_algo.setOrderData(trade_flag, order_price, order_flag)

            logging.info("=== End TradeWrapper.stlDecisionWrapper Logic ===")
