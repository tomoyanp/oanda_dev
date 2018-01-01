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
    base_time = "2017-12-01 00:00:00"
    #base_time = "2017-12-31 00:00:00"
    base_time = datetime.strptime(base_time, "%Y-%m-%d %H:%M:%S")

    try:
        while True:
            now = datetime.now()
            flag = decideMarket(now)

            if flag == False:
                pass
            else:

                sql = u"select insert_time from %s_TABLE where insert_time = \'%s\'" % (currency, base_time)
                response = con.select_sql(sql)

                if len(response) < 1:
                    print base_time.strftime("%Y-%m-%d %H:%M:%S")
                else:
                    pass

            base_time = base_time + timedelta(seconds=1)
    except Exception as e:
        print e.args
