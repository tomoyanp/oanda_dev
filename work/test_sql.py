# cofing: utf-8
import sys
import os
import traceback
import json

current_path = os.path.abspath(os.path.dirname(__file__))
sys.path.append(current_path)
sys.path.append(current_path + "/trade_algorithm")
sys.path.append(current_path + "/obj")
sys.path.append(current_path + "/lib")

property_path = current_path + "/property"
config_path = current_path + "/config"



from mysql_connector import MysqlConnector 


mysqlConnector = MysqlConnector()


sql = "select insert_time, ask_price from GBP_JPY_TABLE where insert_time > '2017-10-12 00:00:00' and insert_time < '2017-10-12 01:00:00'"
response = mysqlConnector.select_sql(sql)


price_list = []
time_list = []

for res in response:
  time_list.append(res[0])
  price_list.append(res[1])


length = len(time_list)
for i in range(0, length):
  print str(time_list[i]) + "      " + str(price_list[i])
