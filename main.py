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


def decide_up_down_before_day(con):
    now = datetime.now()
    # 前日が陽線引けかどうかでbuy or sellを決める
    before_day = now - timedelta(days=1)
    before_day = before_day.strftime("%Y-%m-%d")
    before_end_day = now.strftime("%Y-%m-%d")
    sql = u"select ask_price from %s_TABLE where insert_time > \'%s 06:00:00\' and insert_time < \'%s 06:00:10\'" % (currency, before_day, before_day)
    print sql
    response = con.select_sql(sql)
    before_start_price = response[0][0]

    sql = u"select ask_price from %s_TABLE where insert_time > \'%s 05:59:49\' and insert_time < \'%s 05:59:59\'" % (currency, before_end_day, before_end_day)
    print sql
    response = con.select_sql(sql)
    tmp_list = []
    for line in response:
        tmp_list.append(line)
    before_end_price = response[0][0]

    if before_end_price - before_start_price > 0:
        before_flag = "buy"
    else:
        before_flag = "bid"

    before_flag = "buy"

    print "before_start_price : %s" % before_start_price
    print "before_end_price : %s" % before_end_price
    print "before_flag : %s" % before_flag
    return before_flag

if __name__ == '__main__':

    account_id = 2542764
    token = '85abe6d9c2646b9c56fbf01f0478a511-fe9cb897da06cd6219fde9b4c2052055'
    env = 'practice'
    oanda_wrapper = OandaWrapper(env, account_id, token)

    # 通貨
    instrument = "USD_JPY"
    polling_time = 1

    # 閾値（5pips）
    trade_threshold = 0.1
    optional_threshold = 0.1

    stop_loss = 0.5
    take_profit = 0.5

    stl_threshold = 0.5
    stop_threshold = 0.5
    time_width = 60
    stl_sleeptime = 5


#    stopLoss 
    con = MysqlConnector()
    db_wrapper = DBWrapper()
    trade_algo = TradeAlgo(trade_threshold, optional_threshold)
#    flag = decide_up_down_before_day(con)

    order_flag = False

    try:
      while True:
          while True:
              response = db_wrapper.getPrice(instrument, time_width)
              trade_algo.setResponse(response)
  
              # 現在価格の取得
              logging.info("======= GET PRICE OK ========")
  
              # 今建玉があるかチェック
  #            order_flag = trade_algo.getOrderFlag()
              # get_tradesして、0の場合は決済したものとみなす
              order_flag = oanda_wrapper.get_trade_flag()
  
              # 建玉があれば、決済するかどうか判断
              if order_flag:
                  print "#### DECIDE STL ###"
                  stl_flag = trade_algo.decideStl()
  
                  if stl_flag:
                      now = datetime.now()
                      now = now.strftime("%Y/%m/%d %H:%M:%S")
                      logging.info("===== EXECUTE SETTLEMENT at %s ======" % now)
                      logging.info("===== ORDER KIND is %s ======" % trade_algo.getOrderKind())
                      response = db_wrapper.getPrice(instrument, time_width)
                      if trade_flag == "buy":
                          order_price = response[len(response)-1][0]
                      else:
                          order_price = response[len(response)-1][0]
  
                      logging.info("===== CLOSE ORDER PRICE is %s ======" % order_price)
                      oanda_wrapper.close_trade()
                      break
                  else:
                      pass
  
              else:
                  trade_flag = trade_algo.decideTrade()
                  if trade_flag == "pass":
                      pass
                  else:
                      order_obj = oanda_wrapper.order(trade_flag, instrument, stop_loss, take_profit)
                      now = datetime.now()
                      now = now.strftime("%Y/%m/%d %H:%M:%S")
                      response = db_wrapper.getPrice(instrument, time_width)
                      if trade_flag == "buy":
                          order_price = response[len(response)-1][0]
                      else:
                          order_price = response[len(response)-1][0]
  
                      trade_algo.setOrderPrice(order_price)
  
                      logging.info("#### EXECUTE ORDER at %s ####" % now)
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
