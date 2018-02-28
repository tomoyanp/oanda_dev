# coding: utf-8

import sys
import os
import traceback
import json

# 実行スクリプトのパスを取得して、追加
current_path = os.path.abspath(os.path.dirname(__file__))
sys.path.append(current_path)
sys.path.append(current_path + "/trade_algorithm")
sys.path.append(current_path + "/obj")
sys.path.append(current_path + "/lib")

property_path = current_path + "/property"
config_path = current_path + "/config"

from trade_wrapper import TradeWrapper
from datetime import datetime, timedelta
from send_mail import SendMail
from common import decideMarket, sleepTransaction
import time
import logging
now = datetime.now()
now = now.strftime("%Y%m%d%H%M%S")
logfilename = "%s/log/exec_%s.log" %(current_path, now)
logging.basicConfig(filename=logfilename, level=logging.INFO)

if __name__ == '__main__':

    # argv["main.py", "$1(GBP_JPY)","$2(demo)", "step", "timetrend", "test"]
    # argv[3] is "step" or "startend" or "hilow" or "timetrend"
    # argv[4] is config_filename. when "instrument.config_timetrend" it's "timetrend"
    # argv[4] is config_filename. when "instrument.config_2" it's "2"

    args = sys.argv


    # コマンドライン引数から、通貨とモード取得
    instrument = args[1]
    mode       = args[2]
    algo       = args[3]
    config_name     = args[4]
    base_time = datetime.now()

    if len(args) > 5:
        test_args  = args[5]
    else:
        test_args = "live"

    if test_args == "test":
        end_time = base_time - timedelta(days=0)
        base_time = datetime.strptime("2017-02-01 00:00:00", "%Y-%m-%d %H:%M:%S")
#        base_time = datetime.strptime("2018-02-28 00:00:00", "%Y-%m-%d %H:%M:%S")
        test_mode = True
    else:
        test_mode = False

    # ポーリング時間
    sleep_time = 10

    trade_wrapper = TradeWrapper(instrument, mode, test_mode, current_path, config_name, args)
    trade_wrapper.setTradeAlgo(algo, base_time)

    try:
      while True:
          logging.info("=== Start Main.Loop Logic ===")
          print "test mode = %s" % test_mode
          print "base_time = %s" % base_time
          if test_mode:
              pass
          else:
              base_time = datetime.now()
          flag = decideMarket(base_time)

          if flag == False:
              sleep_time = 1
              base_time = sleepTransaction(sleep_time, test_mode, base_time)

          else:
              # 基本sleep_time = 0を返す
              sleep_time = trade_wrapper.setInstrumentResponse(base_time)
              base_time = sleepTransaction(sleep_time, test_mode, base_time)

              # order_flagがない時は、sleep_timeを返す
              # 約定した時は、trade_sleep_timeを返す
              sleep_time = trade_wrapper.tradeDecisionWrapper(base_time)
              base_time = sleepTransaction(sleep_time, test_mode, base_time)

              # order_flagがある時は、stl_sleep_timeを返す
              # 決済した時は、stl_sleep_ltime or stl_sleep_vtimeを返す
              # その他はsleep_time = 0を返す
              sleep_time = trade_wrapper.stlDecisionWrapper(base_time)
              base_time = sleepTransaction(sleep_time, test_mode, base_time)

              # StopLossの時はstl_sleep_ltimeを返す
              # LimitOrderの時はstl_sleep_vtimeを返す
              # その他はsleep_time = 0を返す
              sleep_time = trade_wrapper.checkPosition()
              base_time = sleepTransaction(sleep_time, test_mode, base_time)

          if test_mode:
              now = datetime.now()

              if base_time > now or base_time > end_time:
                  raise ValueError("Complete Back Test")

          logging.info("=== End Main.Loop Logic ===")

    except:
        message = traceback.format_exc()
        print message
        sendmail = SendMail("tomoyanpy@gmail.com", "tomoyanpy@softbank.ne.jp", property_path)
        sendmail.set_msg(message)
        sendmail.send_mail()
        print message
