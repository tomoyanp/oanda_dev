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


# python extra_record_sql.py GBP_JPY[instrument] 2018-02-16[start_day] 00:00:00[start_time]
args = sys.argv
instrument = args[1]
start_day = args[2]
start_time = args[2]
start_time = "%s %s" % (start_day, start_time)

account_id = 4093685
token = 'e93bdc312be2c3e0a4a18f5718db237a-32ca3b9b94401fca447d4049ab046fad'
env = 'live'

mysql_connector = MysqlConnector()
now = datetime.now()

start_time = "2018-02-15 08:35:00"
end_time = now
start_time = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")

sql_file = open("w", "%s_record.sql" % instrument)

while start_time < end_time:
    start_ftime = start_time - timedelta(hours=9)
    start_ftime = start_ftime.strftime("%Y-%m-%dT%H:%M:%S")

    oanda = oandapy.API(environment=env, access_token=token)
    response = {}
    try :
        response = oanda.get_history(
            instrument=instrument,
            start=start_ftime,
            granularity="S5",
            candleFormat="midpoint"
        )
    except ValueError as e:
        print e

    if len(response) > 0:
        instrument = response["instrument"]
        candles = response["candles"]
        ask_price = candles[0]["openMid"]
        bid_price = candles[0]["openMid"]
        insert_time = start_time.strftime("%Y-%m-%d %H:%M:%S")
<<<<<<< Updated upstream
        sql = u"insert into %s_TABLE(ask_price, bid_price, insert_time) values(%s, %s, \'%s\')" % (instrument, ask_price, bid_price, insert_time)
        sql_file.write(sql + "\n")
=======
        sql = u"insert into %s_TABLE(ask_price, bid_price, insert_time) values(%s, %s, \'%s\');" % (instrument, ask_price, bid_price, insert_time)
        print sql

#        for candle in candles:
#            ask_price = (candle["openMid"])
#            bid_price = (candle["openMid"])
#            print ask_price
#            print bid_price
#            sql = u"insert into %s_TABLE(ask_price, bid_price, insert_time) values(%s, %s, \'%s\')" % (instrument, ask_price, bid_price, insert_time)
#            print sql
#            try:
#                mysql_connector.insert_sql(sql)
#            except Exception as e:
#                pass
>>>>>>> Stashed changes
    else:
        print "response length <= 0"

    start_time = start_time + timedelta(seconds=5)

sql_file.close()
