# coding: utf-8

##########################################################
#
# いちいちSQL叩いているとすげー遅いのでマルチスレッドにして変数にキャッシュしとく
#
##########################################################

import threading
import time
import datetime
from mysql_connector import MysqlConnector
from common import instrument_init

class DbCache(threading.Thread):

    """docstring for TestThread"""

    def __init__(self, base_time):
        super(TestThread, self).__init__()
        self.config_data = instrument_init(self.instrument, self.base_path)
        self.base_time = base_time
        self.ask_price_list = []
        self.bid_price_list = []
        self.insert_time_list = []
        self.mysqlConnector = MysqlConnector()
        sql = self.getInitialSql(self.base_time)
        response = self.mysqlConnector.select_sql(sql)
        self.setResponse(response)

    def run(self):


   def setResponse(self, response):
        if len(response) < 1:
            pass
        else:
            self.ask_price_list = []
            self.bid_price_list = []
            self.insert_time_list = []
            for line in response:
                self.ask_price_list.append(line[0])
                self.bid_price_list.append(line[1])
                self.insert_time_list.append(line[2])


    def getInitialSql(self, base_time):
        time_width = self.config_data["time_width"]
        start_time = base_time - timedelta(seconds=time_width)
        start_time = start_time.strftime("%Y-%m-%d %H:%M:%S")
        end_time = base_time.strftime("%Y-%m-%d %H:%M:%S")
        sql = "select ask_price, bid_price, insert_time from %s_TABLE group by insert_time having insert_time > \'%s\' and insert_time < \'%s\' order by insert_time" % (self.instrument, start_time, end_time)
        print sql
        return sql

    def getAddSql(self, base_time):
        base_time = base_time.strftime("%Y-%m-%d %H:%M:%S")
        sql = "select distinct ask_price, bid_price, insert_time from %s_TABLE where insert_time = \'%s\' limit 1" % (self.instrument, base_time)
        return sql

    def addResponse(self, response):
        if len(response) < 1:
            pass
        else:
            self.ask_price_list.pop(0)
            self.bid_price_list.pop(0)
            self.insert_time_list.pop(0)

        for line in response:
            self.ask_price_list.append(line[0])
            self.bid_price_list.append(line[1])
            self.insert_time_list.append(line[2])

    def setPriceTable(self, base_time):

        if len(self.ask_price_list) < 1:
            sql = self.getInitialSql(base_time)
            print sql
            response = self.mysqlConnector.select_sql(sql)
            self.setResponse(response)
        else:
            cmp_time = self.insert_time_list[len(self.insert_time_list)-1]
            print cmp_time
            print type(cmp_time)
            #cmp_time = datetime.strptime(cmp_time, "%Y-%m-%d %H:%M:%S")
            cmp_time = cmp_time + timedelta(seconds=5)
            if cmp_time < base_time:
                sql = self.getInitialSql(base_time)
                print sql
                response = self.mysqlConnector.select_sql(sql)
                self.setResponse(response)
            else:
                sql = self.getAddSql(base_time)
                print sql
                response = self.mysqlConnector.select_sql(sql)
                self.addResponse(response)
        logging.info(sql)