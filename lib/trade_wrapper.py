# coding: utf-8

import sys
import os
import traceback
import json

from datetime import datetime, timedelta
from step_wise_algo import StepWiseAlgo
from start_end_algo import StartEndAlgo
from time_trend_algo import TimeTrendAlgo
from bollinger_algo import BollingerAlgo
from oanda_wrapper import OandaWrapper
from common import instrument_init, account_init, decide_up_down_before_day
import time
import logging

class TradeWrapper:
    def __init__(self, instrument, mode, test_mode, base_path, config_name):
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

        # 初期化
        self.order_flag = False

        # 指値でいつの間にか決済されてしまったときはこれでスリープさせる
        self.stl_sleep_flag = False

        now = datetime.now()
        base_time = now.strftime("%Y%m%d%H%M%S")
        self.result_file = open("%s/result/%s_result.log" % (self.base_path, base_time), "w")
        self.result_file.write("#########################\n")
        for elm in self.config_data:
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
        else:
            self.trade_algo = HiLowAlgo(self.instrument, self.base_path, self.config_name)


    # 今ポジションを持っているか確認
    # なければ、フラグをリセットする
    def checkPosition(self):
        if self.test_mode:
            pass
        else:
            position_flag = self.oanda_wrapper.get_trade_position(self.instrument)
            if position_flag == False:
                #logging.info("POSITION FLAG FFFFFFFFFFFFFFFFFFALSE!!!!!!!")
                #logging.info("stl_sleep_flag=%s!!!!" % self.stl_sleep_flag)
                self.trade_algo.resetFlag()
                # 決済した直後であればスリープする
                if self.stl_sleep_flag:

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

                    if profit > 0:
                        sleep_time = self.config_data["stl_sleep_vtime"]
                    else:
                        sleep_time = self.config_data["stl_sleep_ltime"]

                    self.result_file.write("ORDER_PRICE=%s, STL_PRICE=%s, ORDER_KIND=%s, PROFIT=%s\n" % (order_price, stl_price, order_kind, profit))
                    self.result_file.write("PROFIT=%s\n" % profit)
                    self.result_file.write("======================================================\n")
                    self.result_file.flush()
                    self.trade_algo.setOrderKind("")
                    #logging.info("SLEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEP!!!!!!!")

                    time.sleep(sleep_time)
                    self.stl_sleep_flag = False
            else:
                #logging.info("POSITION FLAG TTTTTTTTTTTTTTTTTTTTTTTTRUUUE!!!!!!!")
                self.trade_algo.setOrderFlag(True)
                self.stl_sleep_flag = True
                #logging.info("stl_sleep_flag=%s!!!!" % self.stl_sleep_flag)

        # 今建玉があるかチェック
        self.order_flag = self.trade_algo.getOrderFlag()
        logging.info("AFTER CHECK POSITION ORDER FLAG = %s" % self.order_flag)

    def setInstrumentRespoonse(self, base_time):
        self.trade_algo.setPriceTable(base_time)
        #self.trade_algo.setNewPriceTable(base_time)

    def stlDecisionWrapper(self):
        sleep_time = self.config_data["sleep_time"]

        # 建玉があれば、決済するかどうか判断
        logging.info("STL DECISION WRAPPER ORDER FLAG = %s" % self.order_flag)
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

                if profit > 0:
                    sleep_time = self.config_data["stl_sleep_vtime"]
                else:
                    sleep_time = self.config_data["stl_sleep_ltime"]

                self.result_file.write("ORDER_PRICE=%s, STL_PRICE=%s, ORDER_KIND=%s, PROFIT=%s\n" % (order_price, stl_price, order_kind, profit))
                self.result_file.write("PROFIT=%s\n" % profit)
                self.result_file.write("======================================================\n")
                self.result_file.flush()
                self.trade_algo.setOrderKind("")

                if self.test_mode:
                    pass
                else:
                    trade_id = self.trade_algo.getTradeId()
                    self.oanda_wrapper.close_trade(trade_id)
#                    # 決済後のスリープ
#                    time.sleep(self.stl_sleeptime)

            else:
                pass
        else:
            pass

        polling_time = sleep_time
        logging.info("POLLING_TIME%s" % polling_time)
        return polling_time

    def tradeDecisionWrapper(self, base_time):
        logging.info("TRADE DECISION WRAPPER ORDER FLAG = %s" % self.order_flag)
        if self.order_flag:
            pass
        else:
            trade_flag = self.trade_algo.decideTrade(base_time)
            #logging.info("AFTER DECIDE TRADE ORDER_FLAG = %s" % self.trade_algo.getOrderFlag())
            trade_flag = self.trade_algo.decideTradeTime(base_time, trade_flag)
            #logging.info("AFTER TRADE TIME ORDER_FLAG = %s" % self.trade_algo.getOrderFlag())
            trade_flag = self.trade_algo.checkTrend(base_time, trade_flag)
            #logging.info("AFTER CHECK TREND ORDER_FLAG = %s" % self.trade_algo.getOrderFlag())

            if trade_flag == "pass":
                self.trade_algo.resetFlag()
            else:
                # ここのbefore_flag次第で、前日のトレンドを有効にするかどうか
                #before_flag = decide_up_down_before_day(self.con, base_time, self.instrument)
                nowftime = self.trade_algo.getCurrentTime()
                order_price = self.trade_algo.getCurrentPrice()
                self.trade_algo.setOrderPrice(order_price)
                self.result_file.write("===== EXECUTE ORDER at %s ======\n" % nowftime)
                #self.result_file.write("===== BEFORE_FLAG = %s ====\n" % before_flag)
                self.result_file.write("ORDER_PRICE=%s, TRADE_FLAG=%s\n" % (order_price, trade_flag))
                self.result_file.flush()
                threshold_list = self.trade_algo.calcThreshold(trade_flag)

                if self.test_mode or trade_flag == "pass":
                    pass
                else:
                    response = self.oanda_wrapper.order(trade_flag, self.instrument, threshold_list["stoploss"], threshold_list["takeprofit"])
                    self.trade_algo.setTradeId(response)
                    # 約定後のスリープ
                    #time.sleep(self.sleeptime)
