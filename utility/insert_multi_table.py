# coding: utf-8

# 実行スクリプトのパスを取得して、追加
import sys
import os
current_path = os.path.abspath(os.path.dirname(__file__))
current_path = current_path + "/.."
sys.path.append(current_path)
sys.path.append(current_path + "/trade_algorithm")
sys.path.append(current_path + "/obj")
sys.path.append(current_path + "/lib")

from mysql_connector import MysqlConnector
from oanda_wrapper import OandaWrapper
from price_obj import PriceObj
from datetime import datetime, timedelta
from common import decideMarket
import time



def insertTable(base_time, currency, connector, table_type, span):
    sql = u"select ask_price, bid_price from %s_TABLE where insert_time < \'%s\' order by insert_time desc limit %s" % (currency, base_time, span)
    response = connector.select_sql(sql)

    ask_price_list = []
    bid_price_list = []
    for res in response:
        ask_price_list.append(res[0])
        bid_price_list.append(res[1])

    ask_price_list.reverse()
    bid_price_list.reverse()

    start_price = (ask_price_list[0] + bid_price_list[0]) / 2
    end_price = (ask_price_list[-1] + bid_price_list[-1]) / 2
    max_price = (max(ask_price_list) + max(bid_price_list)) / 2
    min_price = (min(ask_price_list) + min(bid_price_list)) / 2
    target_time = base_time - timedelta(seconds=span)


    print "==================="
    print "table_type=%s" % table_type
    print "base_time=%s" % base_time
    print "target_time=%s" % target_time
    print "start_price=%s" % start_price
    print "end_price=%s" % end_price
    print "max_price=%s" % max_price
    print "min_price=%s" % min_price


    sql = u"insert into %s_%s_TABLE(start_price, end_price, max_price, min_price, insert_time) values(%s, %s, %s, %s, \'%s\')" % (currency, table_type, start_price, end_price, max_price, min_price, target_time)
    connector.insert_sql(sql)

if __name__ == "__main__":
    args = sys.argv
    currency = args[1].strip()
    mode = args[2].strip()
    con = MysqlConnector()
    polling_time = 0.5
    sleep_time = 3600

    if mode == "test":
        base_time = "2017-02-01 00:00:00"
        base_time = datetime.strptime(base_time, "%Y-%m-%d %H:%M:%S")
        end_time = "2018-05-19 07:01:00"
        end_time = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
    else:
        base_time = datetime.now()
        end_time = datetime.now()

    while True:
        try:
            now = datetime.now()
            flag = decideMarket(base_time)

            if flag == False:
                pass
            else:
                hour = base_time.hour
                minutes = base_time.minute
                seconds = base_time.second

                if base_time > now:
                    if mode == "test":
                        break
                    else:
                        time.sleep(1)
                        base_time = base_time - timedelta(seconds=1)

                else:
                    if seconds == 59:
                        insertTable(base_time, currency, con, table_type="1m", span=60)
                    if seconds == 59 and minutes % 5 == 4:
                        insertTable(base_time, currency, con, table_type="5m", span=300)
                    if seconds == 59 and minutes == 59:
                        insertTable(base_time, currency, con, table_type="1h", span=3600)
                    if seconds == 59 and minutes == 59 and hour == 5:
                        insertTable(base_time, currency, con, table_type="day", span=(3600*24))

            base_time = base_time + timedelta(seconds=1)

            if mode == "test" and base_time > end_time:
                break

        except Exception as e:
            print e.args
