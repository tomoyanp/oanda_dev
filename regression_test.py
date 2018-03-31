#coding: utf-8

import sys, os
import numpy as np
from datetime import datetime, timedelta
import time

# 実行スクリプトのパスを取得して、追加
current_path = os.path.abspath(os.path.dirname(__file__))
#current_path = "/.."
sys.path.append(current_path)
sys.path.append(current_path + "/trade_algorithm")
sys.path.append(current_path + "/obj")
sys.path.append(current_path + "/lib")

from mysql_connector import MysqlConnector
from common import decideMarket
from common import getSlope

target_time = "2017-09-01 00:00:00"
target_time = datetime.strptime(target_time, "%Y-%m-%d %H:%M:%S")
mysqlConnector = MysqlConnector()
output_file = open("regression_test.txt", "w")

while True:
    if decideMarket(target_time):
        trend_time_width = 5
        instrument = "GBP_JPY"
        #sql = "select base_line from INDICATOR_TABLE where instrument = \'%s\' and type = \'bollinger1h3\' and insert_time <= \'%s\' order by insert_time desc limit 5" % (instrument, target_time)
        sql = "select ask_price from %s_TABLE where insert_time <= \'%s\' and insert_time like \'%%59:59\' order by insert_time desc limit 10" % (instrument, target_time)
        print sql
        
        response = mysqlConnector.select_sql(sql)
        base_line_list = []
        for res in response:
            print res
            base_line_list.append(res[0])

        base_line_list.reverse()
        slope = getSlope(base_line_list)
            
        output_file.write("time = %s, slope = %s\n" % (target_time, slope))
      
    else:
        pass

    now = datetime.now()
    if target_time > now:
        break
    
    target_time = target_time + timedelta(minutes=60)
  
output_file.close()
