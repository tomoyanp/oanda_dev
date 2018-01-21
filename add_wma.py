# coding:utf-8
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

from common import getSlope
from mysql_connector import MysqlConnector
from datetime import datetime, timedelta
from common import getEWMA, getSlope

start_time = "2018-01-19 05:00:00"
start_time = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
now = datetime.now()
con = MysqlConnector()

args = sys.argv
instruments = args[1].strip()

def ewmaWrapper(start_time, wma_length):
    sql = "select ask_price, bid_price, insert_time from %s_TABLE where insert_time < \'%s\' ORDER BY insert_time DESC limit %s" % (instruments, start_time, wma_length)
    response = con.select_sql(sql)
    ask_price_list = []
    bid_price_list = []
    insert_time_list = []
    for res in response:
      ask_price_list.append(res[0])
      bid_price_list.append(res[1])
      insert_time_list.append(res[2])
 
    ask_price_list.reverse()
    bid_price_list.reverse()
    insert_time_list.reverse()

    wma_length = len(ask_price_list)
#    ewma = getEWMA(ask_price_list, bid_price_list, wma_length, 1)
    ewma = getEWMA(bid_price_list, bid_price_list, wma_length, 1)
    return ewma[-1]

while now > start_time:
    now = datetime.now()

    # 1h 21
    ewma_length = 21
    candle_width = 3600
    wma_length = ewma_length * candle_width
    ewma_value = ewmaWrapper(start_time, wma_length)
#    print "time = %s, ewma_value = %s" % (start_time, ewma_value)
    sql = "insert into %s_EWMA_TABLE(ewma_value, ewma_length, candle_width, insert_time) values(%s, %s, %s, \'%s\')" % (instruments, ewma_value, ewma_length, candle_width, start_time)
    con.insert_sql(sql)

    # 1h 50
    ewma_length = 50
    candle_width = 3600
    wma_length = ewma_length * candle_width
    ewma_value = ewmaWrapper(start_time, wma_length)
#    print "time = %s, ewma_value = %s" % (start_time, ewma_value)
    sql = "insert into %s_EWMA_TABLE(ewma_value, ewma_length, candle_width, insert_time) values(%s, %s, %s, \'%s\')" % (instruments, ewma_value, ewma_length, candle_width, start_time)
    con.insert_sql(sql)

    # 1h 100
    ewma_length = 100
    candle_width = 3600
    wma_length = ewma_length * candle_width
    ewma_value = ewmaWrapper(start_time, wma_length)
#    print "time = %s, ewma_value = %s" % (start_time, ewma_value)
    sql = "insert into %s_EWMA_TABLE(ewma_value, ewma_length, candle_width, insert_time) values(%s, %s, %s, \'%s\')" % (instruments, ewma_value, ewma_length, candle_width, start_time)
    con.insert_sql(sql)

    # 5m 21
    ewma_length = 21
    candle_width = 300
    wma_length = ewma_length * candle_width
    ewma_value = ewmaWrapper(start_time, wma_length)
#    print "time = %s, ewma_value = %s" % (start_time, ewma_value)
    sql = "insert into %s_EWMA_TABLE(ewma_value, ewma_length, candle_width, insert_time) values(%s, %s, %s, \'%s\')" % (instruments, ewma_value, ewma_length, candle_width, start_time)
    con.insert_sql(sql)

    # 5m 50
    ewma_length = 50
    candle_width = 300
    wma_length = ewma_length * candle_width
    ewma_value = ewmaWrapper(start_time, wma_length)
#    print "time = %s, ewma_value = %s" % (start_time, ewma_value)
    sql = "insert into %s_EWMA_TABLE(ewma_value, ewma_length, candle_width, insert_time) values(%s, %s, %s, \'%s\')" % (instruments, ewma_value, ewma_length, candle_width, start_time)
    con.insert_sql(sql)

    # 5m 200
    ewma_length = 200
    candle_width = 300
    wma_length = ewma_length * candle_width
    ewma_value = ewmaWrapper(start_time, wma_length)
#    print "time = %s, ewma_value = %s" % (start_time, ewma_value)
    sql = "insert into %s_EWMA_TABLE(ewma_value, ewma_length, candle_width, insert_time) values(%s, %s, %s, \'%s\')" % (instruments, ewma_value, ewma_length, candle_width, start_time)
    con.insert_sql(sql)

    start_time = start_time + timedelta(minutes=1)

