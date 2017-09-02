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
import time

account_id = 2542764
token = '85abe6d9c2646b9c56fbf01f0478a511-fe9cb897da06cd6219fde9b4c2052055'
env = "practice"


if __name__ == "__main__":
    con = MysqlConnector()
    currency = "USD_JPY"
    polling_time = 1
    sleep_time = 3600
    oanda_wrapper = OandaWrapper(env, account_id, token)

    old_today = datetime.now()
    old_today = old_today.strftime("%Y-%m-%d")

    while True:
        try: 
            price_obj = oanda_wrapper.get_price(currency)
            ask_price = price_obj.getAskingPrice()
            bid_price = price_obj.getSellingPrice()

            sql = u"insert into %s_TABLE(ask_price, bid_price) values(%s, %s)" % (currency, ask_price, bid_price)
            con.insert_sql(sql)
    
            time.sleep(polling_time)
    
            today = datetime.now()
            today = today.strftime("%Y-%m-%d")
    
            if today != old_today:
    #        if 1 == 1:
                print "OK"
                now = datetime.now()
                week_ago = now - timedelta(days=14)
                week_ago = week_ago.strftime("%Y-%m-%d")
                
                sql = u"delete from USD_JPY_TABLE where insert_time < \'%s\'" % week_ago
                con.insert_sql(sql)
                old_today = today
        except Exception as e:
            print e.args

