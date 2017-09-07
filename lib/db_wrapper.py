# coding: utf-8


import oandapy
from mysql_connector import MysqlConnector
from datetime import datetime, timedelta

class DBWrapper:

	def __init__(self):
		self.con = MysqlConnector()


	def getPrice(self, instrument, time_width, now):
        time_width = int(time_width)
		#now = datetime.now()
		base_time = now - timedelta(seconds=time_width)
		base_time = base_time.strftime("%Y-%m-%d %H:%M:%S")
        print base_time
		sql = "select ask_price, bid_price, insert_time from %s_TABLE where insert_time > \'%s\'" % (instrument, base_time)
        print sql
		response = self.con.select_sql(sql)
		return response


	def getTimeFormat(self, dtime):
		return dtime.strftime("%Y-%m-%d %H:%M:%S")
