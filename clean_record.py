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
now = datetime.now()

file = open("shortage_price.lst")
for insert_time in file:
    insert_time = insert_time.strip()
    # 通貨
    instrument = "USD_JPY"
    print insert_time
    
    insert_time = datetime.strptime(insert_time, "%Y-%m-%d %H:%M:%S")


    start_time = insert_time - timedelta(hours=9)
    end_time = start_time + timedelta(seconds=5)

    start_time = start_time.strftime("%Y-%m-%dT%H:%M:%S")
    end_time = end_time.strftime("%Y-%m-%dT%H:%M:%S")
    print insert_time
    print end_time
    oanda = oandapy.API(environment=env, access_token=token)

    response = {}
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


    if len(response) > 0:
        instrument = response["instrument"]
        candles = response["candles"]
        
        for candle in candles:
            ask_price = (candle["openMid"])
            bid_price = (candle["openMid"])
            print ask_price
            print bid_price
            sql = u"insert into %s_TABLE(ask_price, bid_price, insert_time) values(%s, %s, \'%s\')" % (instrument, ask_price, bid_price, insert_time)
            print sql
            print "================================"
            try:
                mysql_connector.insert_sql(sql)
            except Exception as e:
                print e
    else:
        print "No JsonData"
        print "================================="
    

