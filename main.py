# coding: utf-8

import sys
import os

# 実行スクリプトのパスを取得して、追加
current_path = os.path.abspath(os.path.dirname(__file__))
sys.path.append(current_path)
sys.path.append(current_path + "/trade_algorithm")
sys.path.append(current_path + "/obj")
sys.path.append(current_path + "/lib")

from datetime import datetime, timedelta
from start_end_algo import StartEndAlgo
from price_obj import PriceObj
from order_obj import OrderObj
from mysql_connector import MysqlConnector
import oandapy
import time
import logging
now = datetime.now()
now = now.strftime("%Y%m%d%H%M%S")
logfilename = "%s/log/exec_%s.log" %(current_path, now)
logging.basicConfig(filename=logfilename, level=logging.INFO)

account_id = 2542764
token = '85abe6d9c2646b9c56fbf01f0478a511-fe9cb897da06cd6219fde9b4c2052055'
oanda = oandapy.API(environment="practice", access_token=token)
price_list = []

def order(l_side, currency):
    while True:
        try:
            response = oanda.create_order(account_id,
                instrument=currency,
                units=50000,
                side=l_side,
                type='market'
            )
            id = response.get("id")
            print "ORDER ID === %s" % id
            price = response.get("price")
            order_obj = OrderObj()
            order_obj.setOrderId(id)
            order_obj.setPrice(price)
            time.sleep(5)
            break
        except Exception as e:
            now = datetime.now()
            now = now.strftime("%Y/%m/%d %H:%M:%S")
            logging.error("========== %s ==========" % now)
            logging.error("Could not Order")
            logging.error(e.message)

    return order_obj

def get_tradeid(oanda):
    response = oanda.get_trades(account_id)
    for trade in response.get("trades"):
        print trade.get("id")

def close_trade():
    while True:
        try:
            response = oanda.get_trades(account_id)
            print response
            trade_id = response["trades"][0]["id"]
            oanda.close_trade(account_id, trade_id)
            break
        except Exception as e:
            now = datetime.now()
            now = now.strftime("%Y/%m/%d %H:%M:%S")
            logging.error("========== %s ==========" % now)
            logging.error("Could not Close Trade")
            logging.error(e.message)

#response = oanda.get_orders(account_id)
#約定していないものしか表示されない

#print response

#response = oanda.close_order(account_id, 10463873762)
#response = oanda.close_order(account_id, 10463873762)
#response = oanda.get_positions(account_id)
#response = oanda.get_trades(account_id)
#response = oanda.close_trade(account_id, 10463873762)
#print response

def update_price():
    price = get_price()


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
    # 通貨
    instrument = "GBP_JPY"
    polling_time = 1

    # 閾値（5pips）
    trade_threshold = 0.01
    stl_threshold = 0.01
    stop_threshold = 0.05
    time_width = 5

    con = MysqlConnector()
    db_wrapper = DBWrapper()
    trade_algo = TradeAlgo(trade_threshold, stl_threshold, stop_threshold)
#    flag = decide_up_down_before_day(con)

    while True:

        order_flag = False
        while True:
            response = db_wrapper.getPrice()
            trade_algo.setResponse(response)

            # 現在価格の取得
            logging.debug("======= GET PRICE OK ========")

            # 今建玉があるかチェック
            order_flag = trade_algo.getOrderFlag()

            if order_flag == False:
                trade_flag = trade_algo.decideTrade()
                if trade_flag == "pass":
                    pass
                else:
                    order_obj = order(trade_flag, currency)
                    now = datetime.now()
                    now = now.strftime("%Y/%m/%d %H:%M:%S")
                    response = db_wrapper.getPrice(instrument, base_time)
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

            # 建玉があれば、決済するかどうか判断
            elif order_flag == True:
                stl_flag = trade_algo.decideStl()

                if stl_flag:

                    now = datetime.now()
                    now = now.strftime("%Y/%m/%d %H:%M:%S")
                    logging.info("===== EXECUTE SETTLEMENT at %s ======" % now)
                    logging.info("===== ORDER KIND is %s ======" % trade_algo.getOrderKind())
                    response = db_wrapper.getPrice(instrument, base_time)
                    if trade_flag == "buy":
                        order_price = response[len(response)-1][0]
                    else:
                        order_price = response[len(response)-1][0]

                    logging.info("===== CLOSE ORDER PRICE is %s ======" % order_price)
                    close_trade()
                    break
                else:
                    pass

            # 建て玉がなければ、約定させるか判断
            else:
            time.sleep(polling_time)
