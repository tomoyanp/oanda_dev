#coding: utf-8

import sys

sys.path.append("lib/")
from mysql_connector import MysqlConnector

target_time = "2017-12-01 00:00:00"
target_time = datetime.strptime(target_time, "%Y-%m-%d %H:%M:%S")
mysql_connector = MysqlConnector

while True:
    output_file = open("regression_test.txt", "w")
    trend_time_width = 5
    instrument = "USD_JPY"
    trend_time_width = int(trend_time_width)
    before_time = target_time - timedelta(hours=trend_time_width)
    sql = "select ask_price from %s_TABLE where insert_time > \'%s\' and insert_time < \'%s\'" % (instrument, before_time, target_time)
    
    response = mysqlConnector.select_sql(sql)
    
    price_list = []
    index_list = []
    index = 1 
    for price in response:
        tmp_price = (price_list[0] + price_list[1]) / 2
        price_list.append(tmp_price)
        index_list.append(index)
        index = index + 1
    
    price_list = np.array(price_list)
    index_list = np.array(index_list)
    z = np.polyfit(index_list, price_list, 3)
    a, b, c, d = np.poly1d(z)
    
    tmp_time = target_time.strftime("%Y-%m-%d %H:%M:%S")
    output_file.write("time = %s, a = %s, b = %s, c = %s, d = %s\n" % (tmp_time, a, b, c, d))
  
    now = datetime.now()
    if target_time > now:
        break
  
output_file.close()
