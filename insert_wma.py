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

start_time = "2018-01-06 07:00:00"
start_time = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")

now = datetime.now()
mysqlConnector = MysqlConnector()

args = sys.argv
instruments = args[1].strip()

ask_price_list = []
bid_price_list = []
insert_time_list = []

def addPrice(self, instrument, base_time, end_time):
    cmp_end_time  = end_time.strftime("%Y-%m-%d %H:%M:%S")
    cmp_base_time = base_time.strftime("%Y-%m-%d %H:%M:%S")
    if cmp_end_time == cmp_base_time:
        pass
    else:
        start_time = end_time
        end_time = base_time
        start_time = start_time.strftime("%Y-%m-%d %H:%M:%S")
        end_time = end_time.strftime("%Y-%m-%d %H:%M:%S")
        sql = "select ask_price, bid_price, insert_time from %s_TABLE where insert_time >= \'%s\' and insert_time < \'%s\' ORDER BY insert_time ASC" % (instrument, start_time, end_time)
        print(sql)
        response = mysqlConnector.select_sql(sql)
        response_length = len(response)
        if response_length < 0:
            pass
        else:
            for i in range(0, response_length):
                ask_price_list.pop(0)
                bid_price_list.pop(0)
                insert_time_list.pop(0)

            for res in response:
                ask_price_list.append(res[0])
                bid_price_list.append(res[1])
                insert_time_list.append(res[2])

    end_time = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
    return end_time

def setInitialPrice(self, instrument, base_time, time_width):
    end_time = base_time.strftime("%Y-%m-%d %H:%M:%S")
    sql = "select ask_price, bid_price, insert_time from %s_TABLE where insert_time < \'%s\' ORDER BY insert_time DESC limit %s" % (instrument, end_time, time_width)
    print sql
    response = mysqlConnector.select_sql(sql)
    setResponse(response)

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

    end_time = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
    return end_time



def ewmaWrapper(wma_length):
    wma_length = wma_length * -1
    tmp_ask_price_list = ask_price_list[wma_length:]
    tmp_bid_price_list = bid_price_list[wma_length:]

    wma_length = len(ask_price_list)
    ewma = getEWMA(tmp_bid_price_list, tmp_bid_price_list, wma_length, 1)
    return ewma[-1]

while True:
    setInitialPrice(start_time)
    try:
        flag = decideMarket(start_time)
        if flag == False:
            pass

        else:
            if now < start_time:
                time.sleep(60)
            else:
                now = datetime.now()

                # 1h 21
                ewma_length = 21
                candle_width = 3600
                wma_length = ewma_length * candle_width
                ewma_value = ewmaWrapper(start_time, wma_length)
            #    print "time = %s, ewma_value = %s" % (start_time, ewma_value)
                sql = "insert into %s_EWMA_TABLE(ewma_value, ewma_length, candle_width, insert_time) values(%s, %s, %s, \'%s\')" % (instruments, ewma_value, ewma_length, candle_width, start_time)
#                con.insert_sql(sql)

                # 1h 50
                ewma_length = 50
                candle_width = 3600
                wma_length = ewma_length * candle_width
                ewma_value = ewmaWrapper(start_time, wma_length)
            #    print "time = %s, ewma_value = %s" % (start_time, ewma_value)
                sql = "insert into %s_EWMA_TABLE(ewma_value, ewma_length, candle_width, insert_time) values(%s, %s, %s, \'%s\')" % (instruments, ewma_value, ewma_length, candle_width, start_time)
#                con.insert_sql(sql)

                # 1h 100
                ewma_length = 100
                candle_width = 3600
                wma_length = ewma_length * candle_width
                ewma_value = ewmaWrapper(start_time, wma_length)
            #    print "time = %s, ewma_value = %s" % (start_time, ewma_value)
                sql = "insert into %s_EWMA_TABLE(ewma_value, ewma_length, candle_width, insert_time) values(%s, %s, %s, \'%s\')" % (instruments, ewma_value, ewma_length, candle_width, start_time)
#                con.insert_sql(sql)
                print ewma_value

                # 5m 21
                ewma_length = 21
                candle_width = 300
                wma_length = ewma_length * candle_width
                ewma_value = ewmaWrapper(start_time, wma_length)
            #    print "time = %s, ewma_value = %s" % (start_time, ewma_value)
                sql = "insert into %s_EWMA_TABLE(ewma_value, ewma_length, candle_width, insert_time) values(%s, %s, %s, \'%s\')" % (instruments, ewma_value, ewma_length, candle_width, start_time)
#                con.insert_sql(sql)

                # 5m 50
                ewma_length = 50
                candle_width = 300
                wma_length = ewma_length * candle_width
                ewma_value = ewmaWrapper(start_time, wma_length)
            #    print "time = %s, ewma_value = %s" % (start_time, ewma_value)
                sql = "insert into %s_EWMA_TABLE(ewma_value, ewma_length, candle_width, insert_time) values(%s, %s, %s, \'%s\')" % (instruments, ewma_value, ewma_length, candle_width, start_time)
#                con.insert_sql(sql)

                # 5m 200
                ewma_length = 200
                candle_width = 300
                wma_length = ewma_length * candle_width
                ewma_value = ewmaWrapper(start_time, wma_length)
            #    print "time = %s, ewma_value = %s" % (start_time, ewma_value)
                sql = "insert into %s_EWMA_TABLE(ewma_value, ewma_length, candle_width, insert_time) values(%s, %s, %s, \'%s\')" % (instruments, ewma_value, ewma_length, candle_width, start_time)
#                con.insert_sql(sql)

        start_time = start_time + timedelta(minutes=1)
        addPrice(start_time)

    except:
        pass
