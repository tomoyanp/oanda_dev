# coding: utf-8

import sys
import os
import traceback
import json
import commands

# 実行スクリプトのパスを取得して、追加
current_path = os.path.abspath(os.path.dirname(__file__))
sys.path.append(current_path)

import time
import logging
now = datetime.now()
now = now.strftime("%Y%m%d%H%M%S")
logfilename = "/var/log/oanda_dev/stop_service_%s.log" %(now)
logging.basicConfig(filename=logfilename, level=logging.INFO)

if __name__ == '__main__':
    cmd = "ps -ef |grep main.py |grep -v grep”
    process_list = commands.getoutput(cmd)
    
    >>> flag = True
>>> while flag:
...   flag = False
...   for i in range(0, len(pslist)):
...     if pslist[i] == "":
...       flag = True
...       pslist.pop(i)
...       break

    # argv["main.py", "$1(GBP_JPY)","$2(demo)", "step", "test"]
    # argv[3] is "step" or "startend" or "hilow"
    args = sys.argv

    # コマンドライン引数から、通貨とモード取得
    instrument = args[1]
    mode       = args[2]
    algo       = args[3]
    if len(args) > 4:
        test_args  = args[4]
    else:
        test_args = "live"

    if test_args == "test":
        test_mode = True
    else:
        test_mode = False

    # ポーリング時間
    polling_time = 1
    trade_wrapper = TradeWrapper(instrument, mode, test_mode, current_path)
    trade_wrapper.setTradeAlgo(algo)

    base_time = datetime.now()
    #base_time = base_time - timedelta(days=20)
    base_time = base_time - timedelta(days=10)

    try:
      while True:
          polling_time = int(polling_time)
          if test_mode:
              base_time = base_time + timedelta(seconds=polling_time)
          else:
              time.sleep(polling_time)
              base_time = datetime.now()

          flag = decideMarket(base_time)
          if flag == False:
              pass

          else:
              trade_wrapper.checkPosition()
              trade_wrapper.setInstrumentRespoonse(base_time)
              trade_wrapper.tradeDecisionWrapper(base_time)
              polling_time = trade_wrapper.stlDecisionWrapper()

          if test_mode:
              now = datetime.now()
              if base_time > now:
                  raise ValueError("Complete Back Test")

    except:
        message = traceback.format_exc()
        print message
        sendmail = SendMail("tomoyanpy@gmail.com", "tomoyanpy@softbank.ne.jp", property_path)
        sendmail.set_msg(message)
        sendmail.send_mail()
        print message
