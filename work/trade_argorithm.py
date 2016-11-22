# coding: utf-8

from mysql_connector import mysqlConnector
import datetime
import numpy

class tradeAlgorithm:

    def __init__(self):
        self.upper_ask = 0
    self.lower_ask = 0
        self.upper_bid = 0
        self.lower_bid = 0
    self.db_connector = mysqlConnector()

    def trade_decision(self):
        sql = ""
        now = datetime.datetime.now()
        year = now.year
        month = now.month
        day = now.day
        hour = now.hour
        minute = now.minute
        second = now.second

        original_time = "%s-%s-%s %s:%s:%s" % (year, month, day, hour, minute-5, second)
        sql = "select instrument, ask_price, bid_price, date_time from price_table where date_time > \'%s\';" % original_time
        price_set = self.db_connector.select_price(sql)
        y_list = []
        x_list = []
        tmp = 0
        for price in price_set:
            y_list.append(price[1])
            x_list.append(tmp)
            tmp = tmp + 1

        logging.info(price_set)
        logging.info(y_list)

        x = numpy.array(x_list)
        y = numpy.array(y_list)
        z = numpy.polyfit(x, y, 1)
        p = numpy.poly1d(z)
        logging.info(p[0])
        logging.info(p[1])
        logging.info(p[2])

        flag = None
        if p[1] > 0:
            flag = "buy"
        elif p[1] < 0:
            flag = "sell"
        else:
            flag = None

        return flag

    def settlement_decision(self, yakujou_price, current_price, songiri_threshold, rikaku_threshold, settlement_mode):  
        flag = False
        if settlement_mode == "buy":
            if (current_price - yakujou_price) > songiri_threshold:
                logging.info("--- SONGIRI ---")
                flag = True 
            elif(yakujou_price - current_price) > rikaku_threshold:    
                logging.info("--- RIKAKU ---")
                flag = True
            else:
                logging.info("--- SETTLEMENT MODE IS BUY DO NOT ORDER ---")
                flag = False    

        # 約定価格と現在価格の差が閾値超えたら決済する
        else:
            if (yakujou_price - current_price) > songiri_threshold:
                logging.info("--- SONGIRI ---")
                flag = True 
            elif(current_price - yakujou_price) > rikaku_threshold:    
                logging.info("--- RIKAKU ---")
                flag = True
            else:
                logging.info("--- SETTLEMENT MODE IS SELL DO NOT ORDER ---")
                flag = False    
    
        return flag 



