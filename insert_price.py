# coding: utf-8
from mysql_connector import MysqlConnector

# 実行スクリプトのパスを取得して、追加
import sys
import os
current_path = os.path.abspath(os.path.dirname(__file__))
sys.path.append(current_path)
sys.path.append(current_path + "/trade_algorithm")
sys.path.append(current_path + "/obj")

from price_obj import PriceObj
import time

account_id = 2542764
token = '85abe6d9c2646b9c56fbf01f0478a511-fe9cb897da06cd6219fde9b4c2052055'
oanda = oandapy.API(environment="practice", access_token=token)

if __name__ == "__main__":
    con = MysqlConnector()
    currency = "GBP_JPY"
    polling_time = 1
    sleep_time = 3600

    price_obj = get_price(currency)
    older_ask_price = price_obj.getAskingPrice()

    while True:
        price_obj = get_price(currency)
        ask_price = price_obj.getAskingPrice()
        bid_price = price_obj.getSellingPrice()

        # 前回値と同じだった場合、休日のためスリープする
        if ask_price == older_ask_price:
            time.sleep(sleep_time)

        else:
            sql = u"insert into %s_TABLE(ask_price, bid_price) values(%s, %s)" % (currency, ask_price, bid_price)
            con.insert_sql(sql)

        older_ask_price = ask_price
        time.sleep(polling_time)

#    sql = u"select * from GBP_JPY_TABLE"
#    response = con.select_sql(sql)
#    for line in response:
#        print type(line)
#        for obj in line:
#            print obj
