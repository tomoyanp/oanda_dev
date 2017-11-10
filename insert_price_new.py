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
    polling_time = 0.5
    sleep_time = 3600
    units = 1000
    oanda_wrapper = OandaWrapper(env, account_id, token, units)

    old_today = datetime.now()
    old_today = old_today.strftime("%Y-%m-%d")

    while True:
        try: 
            now = datetime.now()
            week = now.weekday()
            hour = now.hour
            if week == 5 and hour > 4:
                pass
            elif week == 6:
                pass
            elif week == 0 and  hour < 6:
                pass
            else:
                price_obj = oanda_wrapper.get_price(currency)
                ask_price = price_obj.getAskingPrice()
                bid_price = price_obj.getSellingPrice()
    
                sql = u"insert into %s(ask_price, bid_price) values(%s, %s)" % (currency, ask_price, bid_price)
                con.insert_sql(sql)
        
                time.sleep(polling_time)
        
                today = datetime.now()
                today = today.strftime("%Y-%m-%d")
        
                if today != old_today:
        #        if 1 == 1:
                    now = datetime.now()
                    week_ago = now - timedelta(days=64)
                    week_ago = week_ago.strftime("%Y-%m-%d")
                    
                    sql = u"delete from %s where insert_time < \'%s\'" % (currency, week_ago)
                    con.insert_sql(sql)
                    old_today = today
        except Exception as e:
            print e.args


#        sql = u"select * from GBP_JPY_TABLE"
#        response = con.select_sql(sql)
#        for line in response:
#            print type(line)
#            for obj in line:
#                print obj
