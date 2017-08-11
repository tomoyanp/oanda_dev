# coding: utf-8
from mysql_connector import MysqlConnector

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



con = MysqlConnector()
currency = "GBP_JPY"
price_obj = get_price(currency)
ask_price = price_obj.getAskingPrice()
bid_price = price_obj.getSellingPrice()

sql = u"insert into GBP_JPY_TABLE(ask_price, bid_price) values(%s, %s)" % (ask_price, bid_price)


con.insert_sql(sql)
sql = u"select * from GBP_JPY_TABLE"
response = con.select_sql(sql)

for line in response:
    print type(line)
    for obj in line:
        print obj    
