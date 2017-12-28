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
from common import decideMarket
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
    if len(args) > 5:
        test_args  = args[5]
    else:
        test_args = "live"

    if test_args == "test":
        test_mode = True
    else:
        test_mode = False
    logging.info("=== Start Main Logic ===")
    logging.info(args)

    # ポーリング時間
    polling_time = 1
    trade_wrapper = TradeWrapper(instrument, mode, test_mode, current_path, config_name, args)
    trade_wrapper.setTradeAlgo(algo)

    base_time = datetime.now()
    end_time = base_time - timedelta(days=3)
    base_time = base_time - timedelta(days=7)

    try:
      while True:
          logging.info("=== Start Main.Loop Logic ===")
          polling_time = int(polling_time)
          if test_mode:
              base_time = base_time + timedelta(seconds=polling_time)
          else:
              time.sleep(polling_time)
              base_time = datetime.now()
          logging.info("base_time=%s" % base_time)

          flag = decideMarket(base_time)
          logging.info("decideMarket flag=%s" % flag)
          if flag == False:
              pass

          else:
              sleep_time = trade_wrapper.setInstrumentRespoonse(base_time)
              base_time = sleepPolling(sleep_time, test_mode, base_time)

              sleep_time = trade_wrapper.tradeDecisionWrapper(base_time)
              base_time = sleepPolling(sleep_time, test_mode, base_time)

              sleep_time = trade_wrapper.stlDecisionWrapper(base_time)
              base_time = sleepPolling(sleep_time, test_mode, base_time)

              sleep_time = trade_wrapper.checkPosition()
              base_time = sleepPolling(sleep_time, test_mode, base_time)

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
