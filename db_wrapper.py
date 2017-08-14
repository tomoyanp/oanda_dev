# coding: utf-8


import oandapy
from mysql_connector import MysqlConnector
from datetime import datetime, timedelta

class DBWrapper:

	def __init__(self):
		self.con = MysqlConnector()


	def getPrice(self, base_seconds, instrument):
		sql = "select ask_price, bid_price from %s_TABLE where insert_time > " % instrument
		now = datetime.now()
		base_time = now - timedelta(seconds=base_seconds)
		base_time = base_time.strftime("%Y-%m-%d %H:%M:%S")
		sql = sql + "%s" % base_time
		response = self.con.select_sql(sql)
		return response




