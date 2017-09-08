# coding: utf-8

import sys
import os
import traceback

# 実行スクリプトのパスを取得して、追加
current_path = os.path.abspath(os.path.dirname(__file__))
sys.path.append(current_path)
sys.path.append(current_path + "/trade_algorithm")
sys.path.append(current_path + "/obj")
sys.path.append(current_path + "/lib")

from datetime import datetime, timedelta
from trade_algo import TradeAlgo
from price_obj import PriceObj
from order_obj import OrderObj
from mysql_connector import MysqlConnector
from db_wrapper import DBWrapper
from oanda_wrapper import OandaWrapper
from send_mail import SendMail
import time
import logging
now = datetime.now()
now = now.strftime("%Y%m%d%H%M%S")
logfilename = "%s/log/exec_%s.log" %(current_path, now)
logging.basicConfig(filename=logfilename, level=logging.INFO)

if __name__ == '__main__':

    account_id = 2542764
    token = '85abe6d9c2646b9c56fbf01f0478a511-fe9cb897da06cd6219fde9b4c2052055'
    env = 'practice'
    oanda_wrapper = OandaWrapper(env, account_id, token)

    # 通貨
    instrument = "USD_JPY"
    polling_time = 1

    # 閾値（5pips）
#    trade_threshold = 0.1
    trade_threshold = 0.005

# 0.1だと全然決済されないので、0.07にしてみる
#    optional_threshold = 0.1

    optional_threshold = 0.005

    stop_loss = 0.5
    take_profit = 0.5

    stl_threshold = 0.5
    stop_threshold = 0.5
#    time_width = 60
    time_width = 180
# 決済時の値幅
    stl_time_width = 60
    stl_sleeptime = 300


#    stopLoss
    con = MysqlConnector()
    db_wrapper = DBWrapper()
    trade_algo = TradeAlgo(trade_threshold, optional_threshold)
#    flag = decide_up_down_before_day(con)

    order_flag = False

    try:
      while True:
          while True:
              now = datetime.now()
              if trade_algo.getOrderFlag():
                  response = db_wrapper.getPrice(instrument, stl_time_width, now)
              else:
                  response = db_wrapper.getPrice(instrument, time_width, now)

              trade_algo.setResponse(response)

              # 現在価格の取得
              logging.info("======= GET PRICE OK ========")

              # 今建玉があるかチェック
              order_flag = trade_algo.getOrderFlag()
              # get_tradesして、0の場合は決済したものとみなす
              #order_flag = oanda_wrapper.get_trade_flag()

              # 建玉があれば、決済するかどうか判断
              if order_flag:
                  print "#### DECIDE STL ###"
                  stl_flag = trade_algo.decideStl()

                  trade_id = trade_algo.getTradeId()
                  print "-----------------------------"
                  print trade_id
                  trade_response = oanda_wrapper.get_trade_response(trade_id)
                  print trade_response
                  if len(trade_response) == 0:
                    trade_algo.resetFlag()
                    break

                  if stl_flag:
                      nowftime = now.strftime("%Y/%m/%d %H:%M:%S")
                      logging.info("===== EXECUTE SETTLEMENT at %s ======" % nowftime)
                      logging.info("===== ORDER KIND is %s ======" % trade_algo.getOrderKind())
                      if trade_flag == "buy":
                          order_price = response[len(response)-1][1]
                      else:
                          order_price = response[len(response)-1][0]

                      logging.info("===== CLOSE ORDER PRICE is %s ======" % order_price)
                      trade_id = trade_algo.getTradeId()
                      oanda_wrapper.close_trade(trade_id)
                      # 決済後のスリープ
                      time.sleep(stl_sleeptime)
                      break
                  else:
                      pass

              else:
                  print "Decide stl"
                  trade_flag = trade_algo.decideTrade()
                  if trade_flag == "pass":
                      pass
                  else:
                      threshold_list = trade_algo.calcThreshold(stop_loss, take_profit, trade_flag)
                      response = oanda_wrapper.order(trade_flag, instrument, threshold_list["stoploss"], threshold_list["takeprofit"])
                      print response
                      trade_algo.setTradeId(response)
                      nowftime = now.strftime("%Y/%m/%d %H:%M:%S")
                      if trade_flag == "buy":
                          order_price = response[len(response)-1][0]
                      else:
                          order_price = response[len(response)-1][1]

                      trade_algo.setOrderPrice(order_price)

                      logging.info("#### EXECUTE ORDER at %s ####" % nowftime)
                      logging.info("#### ORDER KIND is %s ####" % trade_flag)
                      logging.info("#### ORDER_PRICE is %s ####" % order_price)
                      # 約定後のスリープ
                      time.sleep(stl_sleeptime)

              time.sleep(polling_time)
    except:
        message = traceback.format_exc()
        sendmail = SendMail("tomoyanpy@gmail.com", "tomoyanpy@softbank.ne.jp")
        sendmail.set_msg(message)
        sendmail.send_mail()
