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

start_time = "2018-01-05 00:00:00"
start_time = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")

now = datetime.now()

con = MysqlConnector()
while now > start_time:
  now = datetime.now()

  sql = "select ask_price, bid_price, insert_time from GBP_JPY_TABLE where insert_time < \'%s\' ORDER BY insert_time DESC limit 100000" % start_time

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

  ewma50 = getEWMA(ask_price_list, bid_price_list, 50, 300)
  slope_length = 10*300*-1
  slope_list = ewma50[slope_length:]
  slope = getSlope(slope_list)
  print "time = %s, slope = %s" % (start_time, slope)
  start_time = start_time + timedelta(minutes=5)

