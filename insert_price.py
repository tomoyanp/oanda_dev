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

account_id = 2542764
token = '85abe6d9c2646b9c56fbf01f0478a511-fe9cb897da06cd6219fde9b4c2052055'
env = "practice"


if __name__ == "__main__":
    args = sys.argv
    currency = args[1].strip()
    con = MysqlConnector()
    polling_time = 0.5
    sleep_time = 3600
    units = 1000
    oanda_wrapper = OandaWrapper(env, account_id, token, units)

    while True:
        try:
            now = datetime.now()
            flag = decideMarket(now)

            if flag == False:
                pass
            else:
                price_obj = oanda_wrapper.get_price(currency)
                ask_price = price_obj.getAskingPrice()
                bid_price = price_obj.getSellingPrice()

                sql = u"insert into %s_TABLE(ask_price, bid_price) values(%s, %s)" % (currency, ask_price, bid_price)
                con.insert_sql(sql)

                time.sleep(polling_time)

        except Exception as e:
            print e.args


#        sql = u"select * from GBP_JPY_TABLE"
#        response = con.select_sql(sql)
#        for line in response:
#            print type(line)
#            for obj in line:
#                print obj
