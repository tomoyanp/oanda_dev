import MySQLdb

class mysqlConnector:

    def __init__(self):
        self.hostname = 'localhost'
        self.dbname = 'oanda_db'
        self.username = 'trade_user'
        self.password = 'trade_user'
        self.character = 'utf8'
        self.connector = MySQLdb.connect(host=self.hostname, db=self.dbname, user=self.username, passwd=self.password, charset=self.character)
        self.cursor = self.connector.cursor()

    def insert_price(self, instrument, ask_price, bid_price):
        sql = u"insert into price_table(instrument, ask_price, bid_price) values('%s', %s, %s)" % (instrument, ask_price, bid_price)
        self.cursor.execute(sql)
        self.connector.commit()

    def select_price(self, sql):
        limit = time * 6
        results = []
        self.cursor.execute(sql)
        responses = self.cursor.fetchall()
        for response in responses:
            results.append(response) 
    	return results  

