#coding: utf-8

import sys
import numpy as np
from datetime import datetime, timedelta

import time
sys.path.append("lib/")
from mysql_connector import MysqlConnector
from common import decideMarket

target_time = "2017-12-10 00:00:00"
target_time = datetime.strptime(target_time, "%Y-%m-%d %H:%M:%S")
mysqlConnector = MysqlConnector()
output_file = open("regression_test.txt", "w")

while True:
    if decideMarket(target_time):
        trend_time_width = 5
        instrument = "USD_JPY"
        trend_time_width = int(trend_time_width)
        before_time = target_time - timedelta(hours=trend_time_width)
        sql = "select ask_price from %s_TABLE where insert_time > \'%s\' and insert_time < \'%s\'" % (instrument, before_time, target_time)
        print sql
        
        response = mysqlConnector.select_sql(sql)
        if len(response) > 1:
            price_list = []
            index_list = []
            index = 1 
            for price in response:
                price_list.append(price[0])
                index_list.append(index)
                index = index + 1
            
            price_list = np.array(price_list)
            index_list = np.array(index_list)
            print price_list
            z = np.polyfit(index_list, price_list, 3)
            a, b, c, d = np.poly1d(z)
            
            tmp_time = target_time.strftime("%Y-%m-%d %H:%M:%S")
            output_file.write("time = %s, a = %s, b = %s, c = %s, d = %s\n" % (tmp_time, a, b, c, d))
      
        now = datetime.now()
        if target_time > now:
            break
    else:
        pass
    
    target_time = target_time + timedelta(minutes=10)
  
output_file.close()
