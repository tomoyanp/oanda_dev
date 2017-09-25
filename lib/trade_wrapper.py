# coding: utf-8

import sys
import os
import traceback
import json

from datetime import datetime, timedelta
from trade_algo import TradeAlgo
from mysql_connector import MysqlConnector
from db_wrapper import DBWrapper
from oanda_wrapper import OandaWrapper
from common import instrument_init, account_init
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
        self.trade_algo    = TradeAlgo(self.trade_threshold, self.optional_threshold)

        # 初期化
        self.order_flag = False

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

    def checkPosition(self):
        if self.test_mode:
            pass
        else:
            position_flag = self.oanda_wrapper.get_trade_position()
            if position_flag == 0:
                self.trade_algo.resetFlag()
                #logging.info("NOT POSITION and RESET FLAG")
            else:
                self.trade_algo.setOrderFlag(True)
                #logging.info("POSITION EXISTS and SET FLAG")

        # 今建玉があるかチェック
        self.order_flag = self.trade_algo.getOrderFlag()
        # logging.info("ORDER_FLAG=%s" % self.order_flag)

    def setInstrumentRespoonse(self, base_time):
        # logging.info("THIS IS ORDER FLAG=%s" % self.trade_algo.getOrderFlag())
        #now = datetime.now()
        if self.trade_algo.getOrderFlag():
            response = self.db_wrapper.getPrice(self.instrument, self.stl_time_width, base_time)
        else:
            #response = self.db_wrapper.getStartEndPrice(self.instrument, self.time_width, base_time)
            response = self.db_wrapper.getPrice(self.instrument, self.time_width, base_time)
            #response = db_wrapper.getPrice(instrument, time_width, now)
        #print response
        self.trade_algo.setResponse(response)



    def stlDecisionWrapper(self):
        test_return_index = 1
        # 建玉があれば、決済するかどうか判断
        if self.order_flag:
            stl_flag = self.trade_algo.decideStl()
            trade_id = self.trade_algo.getTradeId()

            if stl_flag == False and self.test_mode:
                stl_flag = self.trade_algo.decideReverceStl()

           # trade_response = self.oanda_wrapper.get_trade_response(trade_id)
           #  logging.info("trade_response=%s" % trade_response)

            if stl_flag:
                #nowftime = now.strftime("%Y/%m/%d %H:%M:%S")
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

    def tradeDecisionWrapper(self):
        if self.order_flag:
            pass
        else:
            #trade_flag = trade_algo.decideTrade()
            #trade_flag = self.trade_algo.decideStartEndTrade()
            trade_flag = self.trade_algo.decideHiLowTrade()
            #logging.info("TRADE_FLAG=%s" % trade_flag)
            if trade_flag == "pass":
                pass
            else:
                #nowftime = now.strftime("%Y/%m/%d %H:%M:%S")
                nowftime = self.trade_algo.getCurrentTime()
                order_price = self.trade_algo.getCurrentPrice()
                self.trade_algo.setOrderPrice(order_price)
                self.result_file.write("===== EXECUTE ORDER at %s ======\n" % nowftime)
                self.result_file.write("ORDER_PRICE=%s, TRADE_FLAG=%s\n" % (order_price, trade_flag))
                self.result_file.flush()
                threshold_list = self.trade_algo.calcThreshold(self.stop_loss, self.take_profit, trade_flag)

                if self.test_mode:
                    pass
                else:
                    response = self.oanda_wrapper.order(trade_flag, self.instrument, threshold_list["stoploss"], threshold_list["takeprofit"])
                    #logging.info("order_response=%s" % response)
                    self.trade_algo.setTradeId(response)
                    # 約定後のスリープ
                    time.sleep(self.stl_sleeptime)
