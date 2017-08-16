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
    days_ago = 7

    now = datetime.now()

    for i in range(0, days_ago):
        target_day = now - timedelta(days=i)
        target_day = target_day.strftime("%Y-%m-%d")
        start_time = "%s 00:00:00" % target_day
        end_time = "%s 23:59:59" % target_day

        sql = u"select * from %s_TABLE where insert_time > \'%s\' and insert_time < \'%s\'" % (currency, start_time, end_time)
        print sql
        response = con.select_sql(sql)
        filename = "%s/csv/%s_export_%s.csv" % (current_path, currency, target_day)
        target_file = open(filename, "w")
        target_file.write("time,ask_price,bid_price\n")
        for line in response:
            target_file.write("%s,%s,%s\n" % (line[3], line[2], line[1]))
    
        target_file.close()
    
