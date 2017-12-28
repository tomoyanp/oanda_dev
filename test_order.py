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
#from trade_algo import TradeAlgo
from price_obj import PriceObj
from order_obj import OrderObj
from mysql_connector import MysqlConnector
from db_wrapper import DBWrapper
from oanda_wrapper import OandaWrapper
from send_mail import SendMail
from oandapy import oandapy
import time

#demo_account_id = 2542764
account_id = 4093685
token = 'e93bdc312be2c3e0a4a18f5718db237a-32ca3b9b94401fca447d4049ab046fad'
#demo_token = '85abe6d9c2646b9c56fbf01f0478a511-fe9cb897da06cd6219fde9b4c2052055'
#env = 'practice'
env = 'live'
#oanda_wrapper = OandaWrapper(env, account_id, token)

# 通貨
instrument = "USD_JPY"

oanda = oandapy.API(environment=env, access_token=token)
#response = oanda.get_positions(account_id)
#response = oanda.get_account(account_id)
#response = oanda.get_transaction_history(account_id)
response = oanda.get_history(account_id,
    instrument="USD_JPY",
    granularity="S1",
    candleFormat="midpoint",
    count="5"
)
#print response

#response = oanda.get_historical_position_ratios()
#response = oanda.get_history(instrument)
#response = oanda.get_position(account_id, instrument)
print response

#response = oanda_wrapper.order("buy", instrument, 0, 0)
#print response
#
#order_id = response["tradeOpened"]["id"]
#time.sleep(5)
#response = oanda_wrapper.close_trade(order_id)
#print response
