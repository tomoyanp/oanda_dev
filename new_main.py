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
from datetime import datetime, timedelta
import time

account_id = 2542764
token = '85abe6d9c2646b9c56fbf01f0478a511-fe9cb897da06cd6219fde9b4c2052055'
env = "practice"

if __name__ == "__main__":
    con = MysqlConnector()
    currency = "GBP_JPY"
    seconds_ago = 300
    threshold = 0.1

    now = datetime.now()

    # 前日が陽線引けかどうかでbuy or sellを決める
    before_day = now - timedelta(days=1)
    before_day = before_day.strftime("%Y-%m-%d")
    sql = u"select ask_price from %s_TABLE where insert_time = \'%s 00:00:00\'" % (currency, before_day)
    print sql
    response = con.select_sql(sql)
    before_start_price = tmp_list[0][0]

    sql = u"select ask_price from %s_TABLE where insert_time = \'%s 00:00:00\'" % (currency, before_day)
    print sql

    response = con.select_sql(sql)
    tmp_list = []
    for line in response:
        tmp_list.append(line)
    before_end_price = tmp_list[0][0]

    if before_end_price - before_start_price > 0:
        flag = "buy"
    else:
        flag = "bid"

    while True:
        now = datetime.now()
        target_time = now - timedelta(seconds=seconds_ago)
        start_time = target_time.strftime("%Y-%m-%d %H:%M:%S")
        end_time = target_time.strftime("%Y-%m-%d %H:%M:%S")

        sql = u"select %s_price from %s_TABLE where insert_time = \'%s\'" % (flag, currency, start_time)
        response = con.select_sql(sql)
        start_price = float(response[0][0])
    
    
        sql = u"select %s_price from %s_TABLE where insert_time = \'%s\'" % (flag, currency, end_time)
        response = con.select_sql(sql)
        end_price = float(response[0][0])
    
        diff_price = end_price - start_price
        print diff_price 

        if end_price - start_price > 0.1 and flag == "buy":

        elif end_price - start_price < -0.1 and flag == "bid":
