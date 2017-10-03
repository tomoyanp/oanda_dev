# coding: utf-8
# 傾向分析のために使う
# 約定時間から、直近のトレンドをさぐりたい
# 

from datetime import datetime, timedelta
from mysql_connector import MysqlConnector
from datetime import datetime, timedelta
import os, sys

current_path = os.path.abspath(os.path.dirname(__file__))
sys.path.append(current_path)
sys.path.append(current_path + "/lib")

con = MysqlConnector()
trace_time = 3
list_file = open("result_time.lst")
instrument = "GBP_JPY"

for tm in list_file:
    tm = tm.strip()
    base_time = tm
    base_time = datetime.strptime(base_time, "%Y-%m-%d %H:%M:%S")
    end_time = base_time
    start_time = base_time - timedelta(hours=trace_time)

    sql = "select ask_price, insert_time from %s_TABLE where insert_time > \'%s\' and insert_time < \'%s\' order by insert_time" % (instrument, start_time, end_time)
    print sql
    response = con.select_sql(sql)
    print response
    break