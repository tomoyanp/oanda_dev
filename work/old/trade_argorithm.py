# coding: utr-8

from mysql_connector import mysqlConnector
class tradeAlgorithm:

	def __init__(self):
		self.upper_ask = 0
		self.lower_ask = 0
        self.upper_bid = 0
        self.lower_bid = 0
		self.db_connector = mysqlConnector()

    def set_range_limit(self):
    	sql = ""
        # 過去6時間
        time = 360
        limit = time * 6
        # 過去6時間の最大
        sql = u"select instrument, MAX(ask_price), MAX(bid_price) from price_table order by id desc limit %s;" % limit 
        upper_price = self.db_connector.select_price(sql)
        # 過去6時間の最小
        sql = u"select instrument, MIN(ask_price), MIN(bid_price) from price_table order by id desc limit %s;" % limit 
        lower_price = self.db_connector.select_price(sql)
    	self.upper_ask = upper_price[0][1]
    	self.lower_ask = lower_price[0][1]
        self.upper_bid = upper_price[0][2]
        self.lower_bid = lower_price[0][2]
        print "--- upper price ---"
        print "--- upper_ask = %s" % self.upper_ask
        print "--- upper_bid = %s" % self.upper_bid
        print "--- lower price ---"
        print "--- lower_ask = %s" % self.lower_ask
        print "--- upper_bid = %s" % self.lower_bid
        print "-------------------"

#### ここが微妙、セットしたレンジ幅を使っていない。トレンドもなんか微妙
    def trade_decision_at_day(self, current_price):
        # 過去15分
    	time = 15 
    	limit = time * 6
        sql = u"select instrument, ask_price, bid_price from price_table order by id desc limit %s;" % limit 
        price_list = self.db_connector.select_price(sql)
        initial_price = price_list[0][1]
        print " --- initial price ---"
        print initial_price
        print "----------------------" 
        trand_low_flag = 0
        trand_high_flag = 0
        for i in range(1,limit):
            print "--- price_list %s ---" % i
            print price_list[i][1]
            print "---------------------"
            if initial_price > price_list[i][1]:
                trand_low_flag = trand_low_flag + 1
            else:
                trand_high_flag = trand_high_flag + 1
                    
        # 初期値を2/3以上上回っていたら            
        if trand_high_flag > ((limit/3) * 2):
            order_flag =  "buy"           
        elif trand_low_flag > ((limit/3) * 2):
            order_flag = "sell"    
        else:
            order_flag = False    

        print "--- order flas buy or sell oy False ---"
        print order_flag
        print "---------------------------------------"

        return order_flag

    def settlement_decision_at_day(yakujou_price, current_price, threshold):	
        flag = False
        # 約定価格と現在価格の差が閾値超えたら決済する
        if (yakujou_price - current_price) > threshold:
            print "--- SONGIRI ---"
            flag = True 
        elif(current_price - yakujou_price) > threshold:    
            print "--- RIKAKU ---"
            flag = True
        else:
            print "--- DO NOT ORDER ---"
            flag = False    

    	return flag 



