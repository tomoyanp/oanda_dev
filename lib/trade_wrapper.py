# coding: utf-8

import sys
import os
import traceback
import json

from datetime import datetime, timedelta
from step_wise_algo import StepWiseAlgo
from start_end_algo import StartEndAlgo
from mysql_connector import MysqlConnector
from db_wrapper import DBWrapper
from oanda_wrapper import OandaWrapper
from common import instrument_init, account_init, decide_up_down_before_day
import time
import logging

class TradeWrapper:
    def __init__(self, instrument, mode, test_mode, base_path):
        # trueであれば、テストモードにする
        self.test_mode = test_mode

        # rootの絶対パス
        self.base_path = base_path

        # デモもしくは本番
        account_data = account_init(mode, self.base_path)
        self.account_id   = account_data["account_id"]
        self.token        = account_data["token"]
        self.env          = account_data["env"]

        # ポーリング時間
        #polling_time = 1

        # パラメータセット
        config_data        = instrument_init(instrument, self.base_path)
        self.instrument = instrument
        self.trade_threshold    = config_data["trade_threshold"]
        self.optional_threshold = config_data["optional_threshold"]
        self.stop_loss          = config_data["stop_loss"]
        self.take_profit        = config_data["take_profit"]
        self.time_width         = config_data["time_width"]
        self.stl_time_width     = config_data["stl_time_width"]
        self.stl_sleeptime      = config_data["stl_sleeptime"]
        self.units              = config_data["units"]

        # 使うものインスタンス化
        self.oanda_wrapper = OandaWrapper(self.env, self.account_id, self.token, self.units)
        self.con           = MysqlConnector()
        self.db_wrapper    = DBWrapper()
        #self.trade_algo    = TradeAlgo(self.trade_threshold, self.optional_threshold)
        self.trade_algo    = StepWiseAlgo(self.trade_threshold, self.optional_threshold, self.instrument, self.base_path)

        # 初期化
        self.order_flag = False

        # 指値でいつの間にか決済されてしまったときはこれでスリープさせる
        self.stl_sleep_flag = False

        now = datetime.now()
        base_time = now.strftime("%Y%m%d%H%M%S")
        self.result_file = open("%s/result/%s_result.log" % (self.base_path, base_time), "w")
        self.result_file.write("#########################\n")
        self.result_file.write("# instrument = %s\n" % self.instrument)
        self.result_file.write("# trade_threshold = %s\n" % self.trade_threshold)
        self.result_file.write("# optional_threshold = %s\n" % self.optional_threshold)
        self.result_file.write("# stop_loss = %s\n" % self.stop_loss)
        self.result_file.write("# take_profit = %s\n" % self.take_profit)
        self.result_file.write("# time_width = %s\n" % self.time_width)
        self.result_file.write("# stl_time_width = %s\n" % self.stl_time_width)
        self.result_file.write("# stl_sleep_time = %s\n" % self.stl_sleeptime)
        self.result_file.flush()

    def setTradeAlgo(self, algo):
        if algo == "step":
            self.trade_algo = StepWiseAlgo(self.trade_threshold, self.optional_threshold, self.instrument, self.base_path)
        elif algo == "startend":
            self.trade_algo = StartEndAlgo(self.trade_threshold, self.optional_threshold, self.instrument, self.base_path)
        else:
            self.trade_algo = HiLowAlgo(self.trade_threshold, self.optional_threshold, self.instrument, self.base_path)

    # 今ポジションを持っているか確認
    # なければ、フラグをリセットする
    def checkPosition(self):
        if self.test_mode:
            pass
        else:
            position_flag = self.oanda_wrapper.get_trade_position(self.instrument)
            if position_flag == False:
                logging.info("POSITION FLAG FFFFFFFFFFFFFFFFFFALSE!!!!!!!")
                logging.info("stl_sleep_flag=%s!!!!" % self.stl_sleep_flag)
                self.trade_algo.resetFlag()
                # 決済した直後であればスリープする
                if self.stl_sleep_flag:
                    logging.info("SLEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEP!!!!!!!")
                    time.sleep(self.stl_sleeptime)
                    self.stl_sleep_flag = False
            else:
                logging.info("POSITION FLAG TTTTTTTTTTTTTTTTTTTTTTTTRUUUE!!!!!!!")
                self.trade_algo.setOrderFlag(True)
                self.stl_sleep_flag = True
                logging.info("stl_sleep_flag=%s!!!!" % self.stl_sleep_flag)

        # 今建玉があるかチェック
        self.order_flag = self.trade_algo.getOrderFlag()

    def setInstrumentRespoonse(self, base_time):
        if self.trade_algo.getOrderFlag():
            response = self.db_wrapper.getPrice(self.instrument, self.stl_time_width, base_time)
        else:
            response = self.db_wrapper.getPrice(self.instrument, self.time_width, base_time)

        self.trade_algo.setResponse(response)

    def stlDecisionWrapper(self):
        test_return_index = 1
        # 建玉があれば、決済するかどうか判断
        if self.order_flag:
            stl_flag = self.trade_algo.decideStl()
            trade_id = self.trade_algo.getTradeId()

            # テストモードであれば、指値のチェックをフォローしてあげる
            if stl_flag == False and self.test_mode:
                stl_flag = self.trade_algo.decideReverceStl()

            if stl_flag:
                nowftime = self.trade_algo.getCurrentTime()
                self.result_file.write("===== EXECUTE SETTLEMENT at %s ======\n" % nowftime)
                order_kind = self.trade_algo.getOrderKind()
                order_price = self.trade_algo.getOrderPrice()
                stl_price = self.trade_algo.getCurrentPrice()
                self.trade_algo.setStlPrice(order_price)
                if order_kind == "buy":
                    profit = stl_price - order_price
                else:
                    profit = order_price - stl_price

                self.result_file.write("ORDER_PRICE=%s, STL_PRICE=%s, ORDER_KIND=%s, PROFIT=%s\n" % (order_price, stl_price, order_kind, profit))
                self.result_file.write("PROFIT=%s\n" % profit)
                self.result_file.write("======================================================\n")
                self.result_file.flush()
                test_return_index = self.stl_sleeptime

                if self.test_mode:
                    pass
                else:
                    trade_id = self.trade_algo.getTradeId()
                    self.oanda_wrapper.close_trade(trade_id)
                    # 決済後のスリープ
                    time.sleep(self.stl_sleeptime)
            else:
                pass
        else:
            pass

        return test_return_index

    def tradeDecisionWrapper(self, base_time):
        if self.order_flag:
            pass
        else:
            trend_flag = self.trade_algo.checkTrend(base_time)
            trade_flag = self.trade_algo.decideTrade()
            if trade_flag == "pass":
                pass
            elif trend_flag == trade_flag:
                # ここのbefore_flag次第で、前日のトレンドを有効にするかどうか
                #before_flag = decide_up_down_before_day(self.con, base_time, self.instrument)
                nowftime = self.trade_algo.getCurrentTime()
                order_price = self.trade_algo.getCurrentPrice()
                self.trade_algo.setOrderPrice(order_price)
                self.result_file.write("===== EXECUTE ORDER at %s ======\n" % nowftime)
                self.result_file.write("===== BEFORE_FLAG = %s ====\n" % before_flag)
                self.result_file.write("ORDER_PRICE=%s, TRADE_FLAG=%s\n" % (order_price, trade_flag))
                self.result_file.flush()
                threshold_list = self.trade_algo.calcThreshold(self.stop_loss, self.take_profit, trade_flag)

                if self.test_mode or trade_flag == "pass":
                    pass
                else:
                    response = self.oanda_wrapper.order(trade_flag, self.instrument, threshold_list["stoploss"], threshold_list["takeprofit"])
                    self.trade_algo.setTradeId(response)
                    # 約定後のスリープ
                    time.sleep(self.stl_sleeptime)
            else:
                self.trade_algo.resetFlag()
                trade_flag == "pass"
