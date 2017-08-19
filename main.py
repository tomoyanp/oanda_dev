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

def get_price(currency):
    while True:
        try:
            response = oanda.get_prices(instruments=currency)
            prices = response.get("prices")
            price_time = prices[0].get("time")
            instrument = prices[0].get("instrument")
            asking_price = prices[0].get("ask")
            selling_price = prices[0].get("bid")
            price_obj = PriceObj(instrument, price_time, asking_price, selling_price)
            break
        except Exception as e:
            print e.message
 
    return price_obj

#trade_expire = datetime.utcnow() + timedelta(days=1)
#trade_expire = trade_expire.isoformat("T") + "Z"

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
            print e.messages
    
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
            print e.message

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
    sql = u"select ask_price from %s_TABLE where insert_time = \'%s 00:00:00\'" % (currency, before_day)
    print sql
    response = con.select_sql(sql)
    before_start_price = response[0][0]

    sql = u"select ask_price from %s_TABLE where insert_time = \'%s 23:59:59\'" % (currency, before_day)
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

    print "before_start_price : %s" % before_start_price
    print "before_end_price : %s" % before_end_price
    print "before_flag : %s" % before_flag

if __name__ == '__main__':
    # 通貨
    currency = "GBP_JPY"

    # 閾値（5pips）
#    trade_threshold = 0.05
#    stl_threshold = 0.05

    trade_threshold = 0.1
    stl_threshold = 0.2
    price_list_size = 300

    con = MysqlConnector()
    flag = decide_up_down_before_day(con)

    while True:
        order_obj = OrderObj()
        st_algo = StartEndAlgo(trade_threshold, stl_threshold, price_list_size, before_flag)

        # 一分間隔で値を取得
        polling_time = 1

        # 約定後すぐに決済されちゃうので、ちょっと待つ
        stl_sleeptime = 300

        #### get_priceは子スレッドとして動かさないと厳しそう

        order_flag = False

        while True:

            # 現在価格の取得
            price_obj = get_price(currency)

            # アルゴリズムに価格を渡す
            st_algo.setPriceList(price_obj)

            # 今建玉があるかチェック
            order_flag = st_algo.getOrderFlag()

            # 建玉があれば、決済するかどうか判断
            if order_flag:
                stl_flag = st_algo.decideStl()

                if stl_flag:

                    ask_price = st_algo.getAskingPriceList()[price_list_size-1]
                    bid_price = st_algo.getBidPriceList()[price_list_size-1]
                    now = datetime.now()
                    now = now.strftime("%Y/%m/%d %H:%M:%S")
                    logging.info("===== EXECUTE SETTLEMENT at %s ======" % now)
                    logging.info("===== ORDER KIND is %s ======" % st_algo.getOrderKind())
                    logging.info("===== ORDER PRICE is %s ======" % order_obj.getPrice())
                    logging.info("===== CURRENT BID PRICE is %s ======" % bid_price)
                    logging.info("===== CURRENT ASK PRICE is %s ======" % bid_price)
                    close_trade()
                    break
                else:
                    pass
   
            # 建て玉がなければ、約定させるか判断
            else:
                trade_flag = st_algo.decideTrade()
                if trade_flag == "pass":
                    pass
                else:
                    order_obj = order(trade_flag, currency)
                    now = datetime.now()
                    now = now.strftime("%Y/%m/%d %H:%M:%S")
                    logging.info("#### EXECUTE ORDER at %s ####" % now)
                    logging.info("#### ORDER KIND is %s ####" % trade_flag)
                    logging.info("#### ORDER PRICE is %s ####" % order_obj.getPrice())

                    start_ask_price = st_algo.getAskingPriceList()[0]
                    start_bid_price = st_algo.getBidPriceList()[0]
                    ask_price = st_algo.getAskingPriceList()[price_list_size-1]
                    bid_price = st_algo.getBidPriceList()[price_list_size-1]
                    logging.info("#### START ASK PRICE is %s ####" % start_ask_price)
                    logging.info("#### START BID PRICE is %s ####" % start_bid_price)
                    logging.info("#### CURRENT ASK PRICE is %s ####" % ask_price)
                    logging.info("#### CURRENT BID PRICE is %s ####" % bid_price)

                    # アルゴリズムに約定価格をセットしておく
                    order_price = order_obj.getPrice()
                    st_algo.setOrderPrice(order_price)
                    # 約定後のスリープ
                    time.sleep(stl_sleeptime)

            time.sleep(polling_time)

