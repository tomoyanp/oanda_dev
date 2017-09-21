# coding: utf-8


import oandapy
from mysql_connector import MysqlConnector
from datetime import datetime, timedelta

class DBWrapper:

    def __init__(self):
        self.con = MysqlConnector()

    def getPrice(self, instrument, time_width, now):
        time_width = int(time_width)
        base_time = now - timedelta(seconds=time_width)
        base_time = base_time.strftime("%Y-%m-%d %H:%M:%S")
        end_time = now.strftime("%Y-%m-%d %H:%M:%S")
        sql = "select ask_price, bid_price, insert_time from %s_TABLE where insert_time > \'%s\' and insert_time < \'%s\' order by insert_time" % (instrument, base_time, end_time)
        print sql
        response = self.con.select_sql(sql)
        return response

    def getStartEndPrice(self, instrument, time_width, now):
        time_width = int(time_width)
        base_time = now - timedelta(seconds=time_width)
        base_time = base_time.strftime("%Y-%m-%d %H:%M:00")
        end_time = now.strftime("%Y-%m-%d %H:%M:00")
        sql = "select ask_price, bid_price, insert_time from %s_TABLE where insert_time > \'%s\' and insert_time < \'%s\' order by insert_time" % (instrument, base_time, end_time)
        print sql
        response = self.con.select_sql(sql)
        return response


    def getTimeFormat(self, dtime):
        return dtime.strftime("%Y-%m-%d %H:%M:%S")

    def insertOrderHistory(self):
        sql = u"insert into ORDER_HISTORY_TABLE(trade_id, instrument, order_time, order_price, trade_flag, mode) values(%s, %s, %s, %s, %s, %s)" % (trade_id, instrument, order_time, order_price, trade_flag, mode)
        self.con.insert_sql(sql)

    def updateOrderHistory(self):
        sql = u"update ORDER_HISTORY_TABLE set stl_flag = 0, stl_time = \'%s\', stl_price = %s where trade_id = %s" % (stl_time, stl_price)
        self.con.insert_sql(sql)
