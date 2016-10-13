# coding: utf-8
from mysql_connector import mysqlConnector
import oandapy
import time

account_id = 2542764
token = '85abe6d9c2646b9c56fbf01f0478a511-fe9cb897da06cd6219fde9b4c2052055'
oanda = oandapy.API(environment="practice", access_token=token)
default_instrument = "USD_JPY"
db_connector = mysqlConnector()

def get_insert_price():
    while True:
        response = oanda.get_prices(instruments=default_instrument)
        prices = response.get("prices")
        ask_price = prices[0].get("ask")
        bid_price = prices[0].get("bid")
        db_connector.insert_price(default_instrument, ask_price, bid_price)
        time.sleep(10)

get_insert_price() 