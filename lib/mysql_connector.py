import MySQLdb
from datetime import datetime, timedelta
from price_table_wrapper import PriceTableWrapper

class MysqlConnector:

    def __init__(self):
        self.hostname = 'localhost'
        self.dbname = 'oanda_db'
        self.username = 'tomoyan'
        self.password = 'tomoyan180'
        self.character = 'utf8'
        self.connector = MySQLdb.connect(host=self.hostname, db=self.dbname, user=self.username, passwd=self.password, charset=self.character)
        self.cursor = self.connector.cursor()

    def insert_sql(self, sql):
        self.cursor.execute(sql)
        self.connector.commit()

    def select_sql(self, sql):
        self.cursor.execute(sql)
        response = self.cursor.fetchall()
        return response

    def get_price(self, instruments, target_time):
        now = datetime.now()
        target_time = now - timedelta(seconds=target_time)
        sql = u"select insert_time, ask_price, bid_price from %s_TABLE where insert_time > %s" % (instruments, target_time)
        self.cursor.execute(sql)
        response = self.cursor.fetchall()
        priceTableWrapper = PriceTableWrapper()
        priceTableWrapper.setResponse(response)
        return priceTableWrapper

#     def get_newest_price(self, instruments):
#        now = datetime.now()
#        before_seconds = 2
#        target_time = now - timedelta(seconds=before_seconds)
#        sql = u"select insert_time, ask_price, bid_price from %s_TABLE where insert_time > %s" % (instruments, target_time)
#        self.cursor.execute(sql)
#        response = self.cursor.fetchall()
#        priceTableWrapper = PriceTableWrapper()
#        priceTableWrapper.setResponse(response)
#        length = len(priceTableWrapper.getAskPriceList()-1)
#        price_list = {}
#        price_list["ask"] = priceTableWrapper.getAskPriceList(length)
#        price_list["bid"] = priceTableWrapper.getBidPriceList(length)
#        return price_list  
