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

def account_init(mode):
    property_file = open("%s/account.properties" % property_path, "r")
    jsonData = json.load(property_file)
    account_data = jsonData[mode]
    return account_data

if __name__ == '__main__':

    mode = "production"
    account_data = account_init(mode)
    account_id = account_data["account_id"]
    token = account_data["token"]
    env = account_data["env"]
    # 通貨量
    units = 50000

    print account_id
    print token
    print env

    oanda_wrapper = OandaWrapper(env, account_id, token, units)

    # 通貨
    instrument = "USD_JPY"
    polling_time = 1

    # 閾値（5pips）
    trade_threshold = 0.1
    optional_threshold = 0.1

    stop_loss = 0.3
    take_profit = 0.3

    time_width = 30
    stl_time_width = 60

    stl_sleeptime = 300

    con = MysqlConnector()
    db_wrapper = DBWrapper()
    trade_algo = TradeAlgo(trade_threshold, optional_threshold)

    order_flag = False

    try:
      while True:
          while True:
              position_flag = oanda_wrapper.get_trade_position()

              if position_flag == 0:
                  trade_algo.resetFlag()
                  logging.info("NOT POSITION and RESET FLAG")
              else:
                  trade_algo.setOrderFlag(True)
                  logging.info("POSITION EXISTS and SET FLAG")

              logging.info("THIS IS ORDER FLAG=%s" %trade_algo.getOrderFlag())
              now = datetime.now()
              if trade_algo.getOrderFlag():
                  response = db_wrapper.getPrice(instrument, stl_time_width, now)
              else:
                  response = db_wrapper.getPrice(instrument, time_width, now)

              trade_algo.setResponse(response)

              # 今建玉があるかチェック
              order_flag = trade_algo.getOrderFlag()
              logging.info("ORDER_FLAG=%s" % order_flag)

              # 建玉があれば、決済するかどうか判断
              if order_flag:
                  stl_flag = trade_algo.decideStl()
                  trade_id = trade_algo.getTradeId()
                  trade_response = oanda_wrapper.get_trade_response(trade_id)
                  logging.info("trade_response=%s" % trade_response)

                  if stl_flag:
                      nowftime = now.strftime("%Y/%m/%d %H:%M:%S")
                      logging.info("===== EXECUTE SETTLEMENT at %s ======" % nowftime)
                      logging.info("===== ORDER KIND is %s ======" % trade_algo.getOrderKind())
                      order_price = 1234

                      logging.info("===== CLOSE ORDER PRICE is %s ======" % order_price)
                      trade_id = trade_algo.getTradeId()
                      oanda_wrapper.close_trade(trade_id)
                      # 決済後のスリープ
                      time.sleep(stl_sleeptime)
                      break
                  else:
                      pass

              else:
                  trade_flag = trade_algo.decideTrade()
                  logging.info("TRADE_FLAG=%s" % trade_flag)
                  if trade_flag == "pass":
                      pass
                  else:
                      threshold_list = trade_algo.calcThreshold(stop_loss, take_profit, trade_flag)
                      response = oanda_wrapper.order(trade_flag, instrument, threshold_list["stoploss"], threshold_list["takeprofit"])
                      logging.info("order_response=%s" % response)
                      trade_algo.setTradeId(response)
                      nowftime = now.strftime("%Y/%m/%d %H:%M:%S")
                      order_price = 1234

                      trade_algo.setOrderPrice(order_price)

                      logging.info("#### EXECUTE ORDER at %s ####" % nowftime)
                      logging.info("#### ORDER KIND is %s ####" % trade_flag)
                      logging.info("#### ORDER_PRICE is %s ####" % order_price)
                      # 約定後のスリープ
                      time.sleep(stl_sleeptime)

              time.sleep(polling_time)
    except:
        message = traceback.format_exc()
        sendmail = SendMail("tomoyanpy@gmail.com", "tomoyanpy@softbank.ne.jp", property_path)
        sendmail.set_msg(message)
        sendmail.send_mail()
