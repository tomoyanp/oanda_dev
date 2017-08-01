# coding: utf-8

import sys
import os

# 実行スクリプトのパスを取得して、追加
current_path = os.path.abspath(os.path.dirname(__file__))
sys.path.append(current_path)
sys.path.append(current_path + "/trade_algorithm")
sys.path.append(current_path + "/obj")

from datetime import datetime, timedelta
from start_end_algo import StartEndAlgo
from price_obj import PriceObj
from order_obj import OrderObj
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
    response = oanda.get_prices(instruments=currency)
    prices = response.get("prices")
    price_time = prices[0].get("time")
    instrument = prices[0].get("instrument")
    asking_price = prices[0].get("ask")
    selling_price = prices[0].get("bid")
    price_obj = PriceObj(instrument, price_time, asking_price, selling_price)
    return price_obj

#trade_expire = datetime.utcnow() + timedelta(days=1)
#trade_expire = trade_expire.isoformat("T") + "Z"

def order(l_side, currency):
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
    return order_obj

def get_tradeid(oanda):
    response = oanda.get_trades(account_id)
    for trade in response.get("trades"):
        print trade.get("id")

def close_trade():
    response = oanda.get_trades(account_id)
    print response
    trade_id = response["trades"][0]["id"]
    oanda.close_trade(account_id, trade_id)

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

if __name__ == '__main__':
    # 通貨
    currency = "GBP_JPY"

    # 閾値（5pips）
#    trade_threshold = 0.05
#    stl_threshold = 0.05

    trade_threshold = 0.1
    stl_threshold = 0.2

    while True:
        order_obj = OrderObj()
        st_algo = StartEndAlgo(trade_threshold, stl_threshold)

        # 一分間隔で値を取得
        polling_time = 1

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

                    ask_price = st_algo.getAskingPriceList()[59]
                    bid_price = st_algo.getBidPriceList()[59]
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

                    # アルゴリズムに約定価格をセットしておく
                    order_price = order_obj.getPrice()
                    st_algo.setOrderPrice(order_price)

            time.sleep(polling_time)

