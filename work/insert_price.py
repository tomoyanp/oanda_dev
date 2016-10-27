# coding: utf-8
from mysql_connector import mysqlConnector
import oandapy
import time
import datetime
import jholiday

account_id = 2542764
token = '85abe6d9c2646b9c56fbf01f0478a511-fe9cb897da06cd6219fde9b4c2052055'
oanda = oandapy.API(environment="practice", access_token=token)
default_instrument = "USD_JPY"
db_connector = mysqlConnector()
buffer_time = 10


def decide_holiday():
	flag = False
	today = datime.datetime.today()
	year = today.year
	month = today.month
	day = today.day
	target_date = datetime.date(year, month, day)
	weekday = target_date.weekday
	time = today.time()
	hour = time.hour
    holiday = jholiday.holiday_name(date=target_date)
    # 祝日だったら
    if holiday_name is not None:
    	# 月曜祝日だったらパス
    	if weekday == 0:
    	    pass
   	    # その他の祝日だったら朝5時まで更新
    	else:
    	    if hour < 5:
    	        flag = True
 	        else:
 	            pass    
    # 火曜日～金曜日だったら更新
	elif 0 < weekday or weekday < 5:
		flag = True

	# 日曜日だったらパス	
	elif weekday == 6:
	    pass

    # 月曜の朝5時以降だったら更新
	elif weekday == 0:
	    if hour < 5:
	        pass
	    else:
	    	flag = True
    #土曜の朝5時までだったら更新
	elif weekday == 5
	    if hour < 5:
	    	flag = True
        else:
	        pass    	

    return flag


def get_insert_price():
    while True:
    	# 休みじゃなければ
    	if decide_holiday():
            response = oanda.get_prices(instruments=default_instrument)
            prices = response.get("prices")
            ask_price = prices[0].get("ask")
            bid_price = prices[0].get("bid")
            db_connector.insert_price(default_instrument, ask_price, bid_price)
            time.sleep(buffer_time)
        else:
            pass    

get_insert_price()