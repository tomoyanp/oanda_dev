import MySQLdb

class mysqlConnector:

	def __init__(self):
        self.hostname = 'localhost'
        self.dbname = 'oanda_db'
        self.username = 'trade_user'
        self.password = 'trade_user'
        self.character = 'utf8'
        self.connector = MySQLdb.connect(host=hostname, db=dbname, user=username, passwd=password, charset=character)
        self.cursor = connector.cursor()

    def insert_price(instrument, ask_price, bid_price):
        sql = u"insert into price_table(instrument, ask_price, bid_price) values(%s, %s, %s)" % (instrument, ask_price, bid_price)
        cursor.execute(sql)
        connector.commit()

    def select_price():
	    results = []
	    sql = u"select instrument, ask_price, bid_price from price_table order by id desc limit 60;"
	    cursor.execute(sql)
	    responses = cursor.fetchall()
	    for response in responses:
	        results.append(response) 
	        
    	return response    

