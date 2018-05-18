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
from logging import getLogger, FileHandler, DEBUG

now = datetime.now()
now = now.strftime("%Y%m%d%H%M%S")
debug_logfilename = "%s/log/%s.log" %(current_path, now)
result_logfilename = "%s/result/%s.log" %(current_path, now)

debug_logger = getLogger("debug")
result_logger = getLogger("result")

debug_fh = FileHandler(debug_logfilename, "a+")
result_fh = FileHandler(result_logfilename, "a+")

debug_logger.addHandler(debug_fh)
result_logger.addHandler(result_fh)
debug_logger.setLevel(DEBUG)
result_logger.setLevel(DEBUG)

if __name__ == '__main__':

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
        end_time = datetime.strptime("2018-03-27 00:00:00", "%Y-%m-%d %H:%M:%S")
#        end_time = datetime.strptime("2018-04-29 00:00:00", "%Y-%m-%d %H:%M:%S")
#        base_time = datetime.strptime("2018-03-01 00:00:00", "%Y-%m-%d %H:%M:%S")
        base_time = datetime.strptime("2017-03-01 00:00:00", "%Y-%m-%d %H:%M:%S")
#        base_time = datetime.strptime("2018-03-01 00:00:00", "%Y-%m-%d %H:%M:%S")
#        base_time = datetime.strptime("2018-03-01 00:00:00", "%Y-%m-%d %H:%M:%S")
        test_mode = True
    else:
        base_time = datetime.now()
        test_mode = False

    # ポーリング時間
    sleep_time = 10

    trade_wrapper = TradeWrapper(instrument, mode, test_mode, current_path, config_name, args)
    trade_wrapper.setTradeAlgo(algo, base_time)

    try:
      while True:
          print "test mode = %s" % test_mode
          print "base_time = %s" % base_time
          if test_mode:
              pass
          else:
              now = datetime.now()

          flag = decideMarket(base_time)

          if flag == False:
              sleep_time = 1
              base_time = sleepTransaction(sleep_time, test_mode, base_time)

          elif test_mode == False and base_time > now:
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
                  trade_wrapper.removeOnfile()
                  raise ValueError("Complete Back Test")


    except:
        message = traceback.format_exc()
        debug_logger.info(message)
        sendmail = SendMail("tomoyanpy@gmail.com", "tomoyanpy@softbank.ne.jp", property_path)
        sendmail.set_msg(message)
        sendmail.send_mail()
