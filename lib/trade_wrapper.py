# coding: utf-8

import sys
import os
import traceback
import json

from datetime import datetime, timedelta
from trendfollow_algo import TrendFollowAlgo
from trendreverse_algo import TrendReverseAlgo
from expantion_algo import ExpantionAlgo
from daytime_algo import DaytimeAlgo
from oanda_wrapper import OandaWrapper
from common import instrument_init, account_init
import commands
import time
from logging import getLogger, FileHandler, DEBUG

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
        self.onfile_path = ""

        self.debug_logger = getLogger("debug")
        self.result_logger = getLogger("result")
        self.result_logger.info("#########################")
        tmp = ""
        for arg in args:
            tmp = tmp + arg + " "
        self.result_logger.info("# %s" % tmp)
        lst = sorted(self.config_data)
        for elm in lst:
            self.result_logger.info("# %s = %s" % (elm, self.config_data[elm]))

    def setTradeAlgo(self, algo, base_time):
        if algo == "trendfollow":
            self.trade_algo = TrendFollowAlgo(self.instrument, self.base_path, self.config_name, base_time)
        elif algo == "trendreverse":
            self.trade_algo = TrendReverseAlgo(self.instrument, self.base_path, self.config_name, base_time)
        elif algo == "expantion":
            self.trade_algo = ExpantionAlgo(self.instrument, self.base_path, self.config_name, base_time)
        elif algo == "daytime":
            self.trade_algo = DaytimeAlgo(self.instrument, self.base_path, self.config_name, base_time)
        else:
            self.trade_algo = HiLowAlgo(self.instrument, self.base_path, self.config_name, base_time)

        self.onfile_path = "%s/onfile/%s" % (self.base_path, algo)
        self.setCurrentTrade()

    def setCurrentTrade(self):
        if self.test_mode:
            pass
        else:
            response = self.oanda_wrapper.get_current_trades()
            onfile_flag = self.checkOnfile()

            if len(response["trades"]) > 0 and onfile_flag:
                trade_data = response["trades"][0]
                order_price = trade_data["price"]
                order_kind = trade_data["side"]
                trade_id = trade_data["id"]
                order_flag = True
                self.trade_algo.setOrderData(order_kind, order_price, order_flag, trade_id)
                self.debug_logger.info("setCurrentTrade = True")
            else:
                pass

    def removeOnfile(self):
        commands.getoutput("rm -f %s/onfile" % self.onfile_path)

    def createOnfile(self):
        commands.getoutput("touch %s/onfile" % self.onfile_path)

    def checkOnfile(self):
        onfile_exists = commands.getoutput("ls %s/ | wc -l" % self.onfile_path)
        onfile_exists = int(onfile_exists)

        flag = False
        if onfile_exists > 0:
            flag = True

        return flag

    def settlementLogWrite(self, profit, msg):
        nowftime = self.trade_algo.getCurrentTime()
        order_kind = self.trade_algo.getOrderKind()
        order_price = self.trade_algo.getOrderPrice()
        stl_price = self.trade_algo.getCurrentPrice()
        footer = "at %s" % nowftime
        self.result_logger.info(msg + footer)
        self.result_logger.info("# ORDER_PRICE=%s, STL_PRICE=%s, ORDER_KIND=%s, PROFIT=%s" % (order_price, stl_price, order_kind, profit))
        self.result_logger.info("# PROFIT=%s" % profit)

    def tradeLogWrite(self, trade_flag):
        nowftime = self.trade_algo.getCurrentTime()
        order_price = self.trade_algo.getCurrentPrice()
        threshold_list = self.trade_algo.calcThreshold(trade_flag)
        self.result_logger.info("# EXECUTE ORDER at %s" % nowftime)
        self.result_logger.info("# ORDER_PRICE=%s, TRADE_FLAG=%s" % (order_price, trade_flag))

    # 今ポジションを持っているか確認
    # なければ、フラグをリセットする
    def checkPosition(self):
        sleep_time = 0

        # test modeの場合は考慮不要
        if self.test_mode:
            pass
        else:
            position_flag = self.oanda_wrapper.get_trade_position(self.instrument)
            onfile_flag = self.checkOnfile()

            # positionがないのに、onfileがあった場合、決済されたと判断
            if position_flag == False and onfile_flag:
                # 決済した直後であればスリープする
                trade_id = self.trade_algo.getTradeId()
                if self.stl_sleep_flag and trade_id != 0:
                    profit, sleep_time = self.trade_algo.calcProfit()

                    msg = "# EXECUTE SETTLEMENT STOP OR LIMIT ORDER "
                    self.settlementLogWrite(profit, msg)
                    self.stl_sleep_flag = False
                    self.trade_algo.resetFlag()
                    self.removeOnfile()
            else:
                self.stl_sleep_flag = True

        return sleep_time

    def setInstrumentResponse(self, base_time):
        sleep_time = 0
        self.trade_algo.setPrice(base_time)

        return sleep_time

    def stlDecisionWrapper(self, base_time):
        sleep_time = 0
        order_flag = self.trade_algo.getOrderFlag()

        # 建玉があれば、決済するかどうか判断
        if order_flag:
            sleep_time = self.config_data["stl_sleep_time"]
            stl_flag = self.trade_algo.decideStl(base_time)
            trade_id = self.trade_algo.getTradeId()
            onfile_flag = self.checkOnfile()

            #trade_idがある場合もしくはテストモードであれば
            if (self.test_mode == True or trade_id != 0) and onfile_flag:

                # テストモードであれば、指値のチェックをフォローしてあげる
                test_stl_flag = False
                if stl_flag == False and self.test_mode:
                    test_stl_flag = self.trade_algo.decideReverceStl()
                    stl_flag = test_stl_flag
                    #self.result_logger.info("# EXECUTE STOP OR LIMIT ORDER")

                # stl_flagが立ってたら決済する
                if stl_flag:
                    self.trade_algo.setStlPrice(self.trade_algo.getCurrentPrice)

                    # 決済注文
                    if self.test_mode:
                        pass
                    else:
                        trade_id = self.trade_algo.getTradeId()
                        response = self.oanda_wrapper.close_trade(trade_id)
                        stl_price = response["price"]
                        self.trade_algo.setStlPrice(stl_price)

                    profit, sleep_time = self.trade_algo.calcProfit()

                    # 計算した利益を結果ファイルに出力
                    msg = "# EXECUTE SETTLEMENT "
                    self.settlementLogWrite(profit, msg)

                    # flagの初期化
                    self.trade_algo.resetFlag()
                    self.removeOnfile()
                    self.stl_sleep_flag = False
                else:
                    pass
            else:
                pass
        else:
            pass

        return sleep_time

    def tradeDecisionWrapper(self, base_time):
        sleep_time = 0
        order_flag = self.trade_algo.getOrderFlag()

        if order_flag:
            pass
        else:
            trade_flag = self.trade_algo.decideTrade(base_time)
            trade_flag = self.trade_algo.decideTradeTime(base_time, trade_flag)

            if trade_flag == "pass":
                sleep_time = self.config_data["sleep_time"]
            else:
                sleep_time = self.config_data["trade_sleep_time"]
                order_price = self.trade_algo.getCurrentPrice()
                if self.test_mode:
                    # dummy trade id for test mode
                    trade_id = 12345
                else:
                    threshold_list = self.trade_algo.calcThreshold(trade_flag)
                    response = self.oanda_wrapper.order(trade_flag, self.instrument, threshold_list["stoploss"], threshold_list["takeprofit"])
                    order_price = response["price"]
                    trade_id = response["tradeOpened"]["id"]

                self.tradeLogWrite(trade_flag)
                order_flag = True
                self.trade_algo.setOrderData(trade_flag, order_price, order_flag, trade_id)
                self.createOnfile()

        return sleep_time
