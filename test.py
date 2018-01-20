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

start_time = "2018-01-08 07:00:00"
start_time = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
now = datetime.now()
con = MysqlConnecter()

def ewmaWrapper(sql, wma_length):
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
    
    ewma = getEWMA(ask_price_list, bid_price_list, wma_length, 1)
    return ewma[-1]

while now > start_time:
    now = datetime.now()

    wma_length = 100
    sql = "select ask_price, bid_price, insert_time from GBP_JPY_TABLE where insert_time < \'%s\'   and insert_time like ‘%%59:59’ ORDER BY insert_time DESC limit %s" % (start_time, wma_length)

    ewma_value = ewmaWrapper(sql, wma_length)
    print "time = %s, ewma_value = %s" % (start_time, ewma_value)
    start_time = start_time + timedelta(minutes=10)

