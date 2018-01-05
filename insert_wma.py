# coding: utf-8

# 実行スクリプトのパスを取得して、追加
import sys
import os
current_path = os.path.abspath(os.path.dirname(__file__))
sys.path.append(current_path)
sys.path.append(current_path + "/trade_algorithm")
sys.path.append(current_path + "/obj")
sys.path.append(current_path + "/lib")

from mysql_connector import MysqlConnector
from oanda_wrapper import OandaWrapper
from price_obj import PriceObj
from datetime import datetime, timedelta
from common import decideMarket, getWMA
import time


def getInitialRecord(base_time):
    insert_time = base_time.strftime("%Y-%m-%d %H:%M:%S")
    width = 4000 * 200
    sql = u"select ask_price, bid_price, insert_time from %s_TABLE where insert_time <= \'%s\' ORDER BY insert_time DESC limit %s" % (currency, insert_time, width)
    print sql
    response = con.select_sql(sql)

    now = datetime.now()

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
    
    while now != base_time:
        base_time = base_time + timedelta(seconds=1)
        insert_time = base_time.strftime("%Y-%m-%d %H:%M:%S")
        sql = u"select ask_price, bid_price, insert_time from %s_TABLE where insert_time = \'%s\'" % (currency, insert_time)
        print sql
        response = con.select_sql(sql)

        for res in response:
            ask_price_list.append(res[0])
            bid_price_list.append(res[1])
            insert_time_list.append(res[2])
 
        now = datetime.now()

    return ask_price_list, bid_price_list, insert_time_list, base_time

def addRecord():





if __name__ == "__main__":
    args = sys.argv
    currency = args[1].strip()
    con = MysqlConnector()
    now = datetime.now()
    resposne = getInitialRecord(now)

    ask_price_list = []
    bid_price_list = []
    insert_time_list = []


    while True:
        try:
            now = datetime.now()
            flag = decideMarket(now)

            if flag == False:
                pass
            else:
                now = now.strftime("%Y-%m-%d %H:%M:%S")
                sql = u"select ask_price, bid_price, insert_time from %s_TABLE where insert_time <= \'%s\' ORDER BY insert_time DESC limit %s" % (currency, now, width)
                ask_price_list = []
                bid_price_list = []
                for res in response:
                    ask_price_list.append(res[0])
                    bid_price_list.append(res[1])

                ask_price_list.reverse()
                bid_price_list.reverse()

                wma_length = 200
                candle_width = 60
                wma_value = getWMA(ask_price_list, bid_price_list, wma_length, candle_width)
                print wma_value
                candle_width = 300
                wma_value = getWMA(ask_price_list, bid_price_list, wma_length, candle_width)
                print wma_value

                candle_width = 3600
                wma_value = getWMA(ask_price_list, bid_price_list, wma_length, candle_width)

                print wma_value

        except Exception as e:
            print e.args


