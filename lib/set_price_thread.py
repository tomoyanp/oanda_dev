# coding: utf-8

import sys
import os
from datetime import datetime, timedelta
import threading
import time

current_path = os.path.abspath(os.path.dirname(__file__))
sys.path.append(current_path)
sys.path.append(current_path + "/lib")

from mysql_connector import MysqlConnector

class SetPriceThread(threading.Thread):

    def __init__(self, instruments, base_time, time_width):
        super(SetPriceThread, self).__init__()
        self.ask_price_list = []
        self.bid_price_list = []
        self.insert_time_list = []
  
        self.instruments = instruments
        self.time_width = time_width
        self.start_time = base_time - timedelta(seconds=self.time_width)
        self.end_time = base_time
        self.base_time = base_time
        self.con = MysqlConnector()
        self.setPrice()

    def getDataSet(self):
        return self.ask_price_list, self.bid_price_list, self.insert_time_list


    def getSql(self):
        start_time = self.start_time.strftime("%Y-%m-%d %H:%M:%S")
        end_time = self.end_time.strftime("%Y-%m-%d %H:%M:%S")
        sql = "select ask_price, bid_price, insert_time from %s_TABLE where insert_time >= \'%s\' and insert_time < \'%s\' ORDER BY insert_time ASC" % (self.instruments, start_time, end_time)

        return sql

    def setPrice(self):
        sql = self.getSql()
        print(sql)
        response = self.con.select_sql(sql)
        self.setResponse(response)

    def addPrice(self):
        cmp_end_time = self.end_time.strftime("%Y-%m-%d %H:%M:%S")
        cmp_base_time = self.base_time.strftime("%Y-%m-%d %H:%M:%S")
        if cmp_end_time == cmp_base_time:
            pass
            #print("pass")
        else:
            self.start_time = self.end_time
            self.end_time = self.base_time
            sql = self.getSql()
            print(sql)
            response = self.con.select_sql(sql)
            self.addResponse(response)

    def setResponse(self, response):
        for res in response:
            self.ask_price_list.append(res[0])
            self.bid_price_list.append(res[1])
            self.insert_time_list.append(res[2])

    def addResponse(self, response):
        response_length = len(response)
        if response_length < 0:
            pass
        else:
            for i in range(0, response_length):
                self.ask_price_list.pop(0)
                self.bid_price_list.pop(0)
                self.insert_time_list.pop(0)

            for res in response:
                self.ask_price_list.append(res[0])
                self.bid_price_list.append(res[1])
                self.insert_time_list.append(res[2])

            for elm in self.insert_time_list:
                print(elm)
            print("=========================================")
            
    def setBaseTime(self, base_time):
        self.base_time = base_time

    def printBaseTime(self):
        print(self.base_time)

    def run(self):
        while True:
            self.addPrice() 
            time.sleep(0.1)
      
