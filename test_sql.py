# cofing: utf-8
import sys
import os
import traceback
import json

# 実行スクリプトのパスを取得して、追加
current_path = os.path.abspath(os.path.dirname(__file__))
sys.path.append(current_path)
sys.path.append(current_path + "/trade_algorithm")
sys.path.append(current_path + "/obj")
sys.path.append(current_path + "/lib")

property_path = current_path + "/property"
config_path = current_path + "/config"



from mysql_connector import MysqlConnector 


mysqlConnector = MysqlConnector()


sql = "select insert_price, ask_price from GBP_JPY_TABLE where insert_time > '2017-10-12 00:00:00' and insert_time < '2017-10-12 01:00:00'"
response = mysqlConnector.select_sql(sql)


for res in response:
	print res