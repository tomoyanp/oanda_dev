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
from common import getEWMA, getSlope, decideMarket

start_time = "2018-01-25 07:00:00"
start_time = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")

now = datetime.now()
mysqlConnector = MysqlConnector()

args = sys.argv
instruments = args[1].strip()

def getPrice(base_time, time_width):
    base_time = base_time.strftime("%Y-%m-%d %H:%M:%S")
    sql = "select ask_price, bid_price, insert_time from %s_TABLE where insert_time < \'%s\' ORDER BY insert_time DESC limit %s" % (instruments, base_time, time_width)
    print sql
    response = mysqlConnector.select_sql(sql)
    if len(response) < 1:
        pass
    else:
        for line in response:
            ask_price_list.append(line[0])
            bid_price_list.append(line[1])
            insert_time_list.append(line[2])

        ask_price_list.reverse()
        bid_price_list.reverse()
        insert_time_list.reverse()

    return ask_price_list, bid_price_list, insert_time_list

def ewmaWrapper(ask_price_list, bid_price_list, wma_length):
    wma_length = wma_length * -1
    tmp_ask_price_list = ask_price_list[wma_length:]
    tmp_bid_price_list = bid_price_list[wma_length:]

    wma_length = len(ask_price_list)
    ewma = getEWMA(tmp_ask_price_list, tmp_bid_price_list, wma_length, 1)
    return ewma[-1]

ask_price_list = []
bid_price_list = []
insert_time_list = []

while True:
    try:
        flag = decideMarket(start_time)
        if flag == False:
            pass
        else:
            if now < start_time:
                time.sleep(60)
            else:
                now = datetime.now()
                time_width = 3600 * 200
                ask_price_list, bid_price_list, insert_time_list = getPrice(start_time, time_width)

                # 1h 21
                ewma_length = 21
                candle_width = 3600
                wma_length = ewma_length * candle_width
                ewma_value = ewmaWrapper(ask_price_list, bid_price_list, wma_length)
                print "time = %s, ewma_value = %s" % (start_time, ewma_value)
                sql = "insert into %s_EWMA_TABLE(ewma_value, ewma_length, candle_width, insert_time) values(%s, %s, %s, \'%s\')" % (instruments, ewma_value, ewma_length, candle_width, start_time)
                con.insert_sql(sql)

                # 1h 50
                ewma_length = 50
                candle_width = 3600
                wma_length = ewma_length * candle_width
                ewma_value = ewmaWrapper(ask_price_list, bid_price_list, wma_length)
                print "time = %s, ewma_value = %s" % (start_time, ewma_value)
                sql = "insert into %s_EWMA_TABLE(ewma_value, ewma_length, candle_width, insert_time) values(%s, %s, %s, \'%s\')" % (instruments, ewma_value, ewma_length, candle_width, start_time)
                con.insert_sql(sql)

                # 1h 100
                ewma_length = 200
                candle_width = 3600
                wma_length = ewma_length * candle_width
                ewma_value = ewmaWrapper(ask_price_list, bid_price_list, wma_length)
                print "time = %s, ewma_value = %s" % (start_time, ewma_value)
                sql = "insert into %s_EWMA_TABLE(ewma_value, ewma_length, candle_width, insert_time) values(%s, %s, %s, \'%s\')" % (instruments, ewma_value, ewma_length, candle_width, start_time)
                con.insert_sql(sql)

                # 5m 21
                ewma_length = 21
                candle_width = 300
                wma_length = ewma_length * candle_width
                ewma_value = ewmaWrapper(ask_price_list, bid_price_list, wma_length)
                print "time = %s, ewma_value = %s" % (start_time, ewma_value)
                sql = "insert into %s_EWMA_TABLE(ewma_value, ewma_length, candle_width, insert_time) values(%s, %s, %s, \'%s\')" % (instruments, ewma_value, ewma_length, candle_width, start_time)
                con.insert_sql(sql)


                # 5m 50
                ewma_length = 50
                candle_width = 300
                wma_length = ewma_length * candle_width
                ewma_value = ewmaWrapper(ask_price_list, bid_price_list, wma_length)
                print "time = %s, ewma_value = %s" % (start_time, ewma_value)
                sql = "insert into %s_EWMA_TABLE(ewma_value, ewma_length, candle_width, insert_time) values(%s, %s, %s, \'%s\')" % (instruments, ewma_value, ewma_length, candle_width, start_time)
                con.insert_sql(sql)


                # 5m 200
                ewma_length = 200
                candle_width = 300
                wma_length = ewma_length * candle_width
                ewma_value = ewmaWrapper(ask_price_list, bid_price_list, wma_length)
                print "time = %s, ewma_value = %s" % (start_time, ewma_value)
                sql = "insert into %s_EWMA_TABLE(ewma_value, ewma_length, candle_width, insert_time) values(%s, %s, %s, \'%s\')" % (instruments, ewma_value, ewma_length, candle_width, start_time)
                con.insert_sql(sql)

                start_time = start_time + timedelta(minutes=1)

    except:
        pass
