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
from common import decideMarket
import time

if __name__ == "__main__":
    args = sys.argv
    currency = args[1].strip()
    con = MysqlConnector()
    polling_time = 60

    try:
        while True:
            now = datetime.now()
            flag = decideMarket(now)

            if flag == False:
                pass
            else:
                start_time = now - timedelta(minutes=1)
                start_time = start_time.strftime("%Y-%m-%d %H:%M:%S")
                end_time   = now.strftime("%Y-%m-%d %H:%M:%S")

                sql = u"select insert_time from %s_TABLE where insert_time > \'%s\' and insert_time < \'%s\'" % (currency, start_time, end_time)
                print sql
                response = con.select_sql(sql)
                print response
                print "==============================================="
                for res in response:
                    tm = res[0].strftime("%Y-%m-%d %H:%M:%S")
                    print tm

                if len(response) < 50:
                    raise ValueError("%s_TABLE CHECK FAIL. LIST LENGTH=%s" %(currency, len(response)))
                else:
                    pass

                time.sleep(polling_time)

    except Exception as e:
        print e.args
