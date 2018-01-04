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

if __name__ == "__main__":
    args = sys.argv
    currency = args[1].strip()
    con = MysqlConnector()

    while True:
        try:
            now = datetime.now()
            flag = decideMarket(now)

            if flag == False:
                pass
            else:
                now = now.strftime("%Y-%m-%d %H:%M:%S")
                width = 4000 * 200
                sql = u"select ask_price, bid_price, insert_time from %s_TABLE where insert_time <= \'%s\' ORDER BY insert_time DESC limit %s" % (currency, now, width)
                response = con.select_sql(sql)
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


