# coding: utf-8

import sys
import os
import traceback
import json

# 実行スクリプトのパスを取得して、追加
current_path = os.path.abspath(os.path.dirname(__file__))
current_path = current_path + "/.."
sys.path.append(current_path)
sys.path.append(current_path + "/trade_algorithm")
sys.path.append(current_path + "/obj")
sys.path.append(current_path + "/lib")

from common import decideMarket, account_init
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

account_data = account_init("production", current_path)
account_id = account_data["account_id"]
token = account_data["token"]
env = account_data["env"]
 
mysql_connector = MysqlConnector()
now = datetime.now()

start_time = "2018-01-10 00:00:00"
end_time = "2018-07-15 00:00:00"

end_time = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
start_time = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")

sql_file = open("%s_record.sql" % instrument, "w")

while start_time < end_time:
    if decideMarket(start_time):
        start_ftime = start_time - timedelta(hours=9)
        start_ftime = start_ftime.strftime("%Y-%m-%dT%H:%M:%S")
    
        oanda = oandapy.API(environment=env, access_token=token)
        response = {}
        try :
            response = oanda.get_history(
                instrument=instrument,
                start=start_ftime,
                granularity="S5"
            )
        except ValueError as e:
            print e
    
        if len(response) > 0:
            instrument = response["instrument"]
            candles = response["candles"]
            for candle in candles:
                time = candle["time"]
                time = time.split(".")[0]
                insert_time = datetime.strptime(time, "%Y-%m-%dT%H:%M:%S")
                insert_time = insert_time + timedelta(hours=9)
                ask_price = candle["openAsk"]
                if instrument == "USD_JPY":
                    bid_price = ask_price - 0.008
                else:
                    bid_price = candle["openBid"]
                sql = u"insert into %s_TABLE(ask_price, bid_price, insert_time) values(%s, %s, \'%s\')" % (instrument, ask_price, bid_price, insert_time)
                mysql_connector.insert_sql(sql)
                sql_file.write("%s\n" % sql)
                print sql
            print "============================================================="
            start_time = insert_time
    
        else:
            print "response length <= 0"

    else:
        print "Market closed %s" % start_time

    start_time = start_time + timedelta(seconds=5)

sql_file.close()
