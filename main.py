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
import oandapy
import time


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

def order(l_side):
    response = oanda.create_order(account_id,
        instrument="USD_JPY",
        units=1000,
        side=l_side,
        type='market'
    )
    id = response.get("id")
    price = response.get("price")
    orderInstance = orderObj(id, price)
    return orderInstance


def get_tradeid(oanda):
    response = oanda.get_trades(account_id)
    for trade in response.get("trades"):
        print trade.get("id")


def settlement(oanda, orderInstance):
    while True:
        price = get_price(oanda)
        buy_price = orderInstance.getPrice()
# 損切り
        if price - buy_price < -0.2:
            oanda.close_trade(account, orderInstance.getId())
# 利確
        elif price - buy_price > 0.2:
            oanda.close_trade(account, orderInstance.getId())
# 継続
        else:
            pass


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
    currency = "GBP_JPY"

    # 閾値（5pips）
    trade_threshold = 0.05
    st_algo = StartEndAlgo(trade_threshold)

    # 一分間隔で値を取得
    polling_time = 1

    #### get_priceは子スレッドとして動かさないと厳しそう

    while True:
        price_obj = get_price(currency)
        st_algo.setPriceList(price_obj)
        trade_flag = st_algo.decideTrade()

        if trade_flag == "pass":
            pass
        else:
            order(trade_flag)

        ask_price_list = st_algo.getAskingPriceList()
        bid_price_list = st_algo.getBidPriceList()

        print ask_price_list
        print bid_price_list
        time.sleep(polling_time)
