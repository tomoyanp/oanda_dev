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

from datetime import datetime, timedelta
from common import decideMarket
from price_obj import PriceObj
from order_obj import OrderObj
from mysql_connector import MysqlConnector
from db_wrapper import DBWrapper
from oanda_wrapper import OandaWrapper
from send_mail import SendMail
from oandapy import oandapy
import time

account_id = 4093685
token = 'e93bdc312be2c3e0a4a18f5718db237a-32ca3b9b94401fca447d4049ab046fad'
env = 'live'

mysql_connector = MysqlConnector()
#start_time = "2018-01-06T00:00:00"
start_time = "2018-02-06T00:00:00"
start_time = datetime.strptime(start_time, "%Y-%m-%dT%H:%M:%S")
now = datetime.now()

while start_time < now:
    # 通貨
    instrument = "NZD_JPY"
    end_time = start_time + timedelta(minutes=10)
    market_flag = decideMarket(start_time)
    end_time = end_time.strftime("%Y-%m-%dT%H:%M:%S")
    start_time = start_time.strftime("%Y-%m-%dT%H:%M:%S")

    if market_flag == False:
        pass
    else:

        oanda = oandapy.API(environment=env, access_token=token)
        response = {}

        print "====== START TIME ======"
        print start_time
        print "======  END TIME  ======"
        print end_time
        try :
            response = oanda.get_history(
                instrument=instrument,
                start=start_time,
                end=end_time,
                granularity="S5",
                candleFormat="midpoint"
            )
        except ValueError as e:
            print e
            print start_time


        if len(response) > 0:
            instrument = response["instrument"]
            candles = response["candles"]
            insert_time_list = []
            price_list = []

            for candle in candles:
                ask_price = (candle["openMid"])
                bid_price = (candle["openMid"])
                insert_time = candle["time"].split(".")[0]
                insert_time = datetime.strptime(insert_time, "%Y-%m-%dT%H:%M:%S")
                insert_time = insert_time.strftime("%Y-%m-%d %H:%M:%S")

                sql = u"insert into %s_TABLE(ask_price, bid_price, insert_time) values(%s, %s, \'%s\')" % (instrument, ask_price, bid_price, insert_time)
                print sql
                #mysql_connector.insert_sql(sql)

    end_time = datetime.strptime(end_time, "%Y-%m-%dT%H:%M:%S")
    start_time = end_time


print "====== START TIME ======"
print start_time.strftime("%Y-%m-%d %H:%M:%S")
print "======  NOW TIME  ======"
print now.strftime("%Y-%m-%d %H:%M:%S")
