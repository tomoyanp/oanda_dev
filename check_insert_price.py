# coding: utf-8

# 実行スクリプトのパスを取得して、追加
import sys
import os
current_path = os.path.abspath(os.path.dirname(__file__))
sys.path.append(current_path)
sys.path.append(current_path + "/trade_algorithm")
sys.path.append(current_path + "/obj")
sys.path.append(current_path + "/lib")

from mysql_connector import MysqlConnector
from oanda_wrapper import OandaWrapper
from price_obj import PriceObj
from datetime import datetime, timedelta
from common import decideMarket
from send_mail import SendMail
import time



# if check value is empty, insert record before 1 seconds 
def follow_record(con, base_time, currency):
    #print "value is empty, base_time = %s" % base_time
    print("value is empty, base_time = %s" % base_time)
    base_time_bef = base_time - timedelta(seconds=1)
    sql = "select ask_price, bid_price from %s_TABLE where insert_time = \'%s\'" % (currency, base_time_bef)
    #print sql
    print(sql)
    response = con.select_sql(sql)

    ask_price = response[0][0]
    bid_price = response[0][1]

    sql = "insert into %s_TABLE (ask_price, bid_price, insert_time) values (%s, %s, \'%s\')" % (currency, ask_price, bid_price, base_time)
    #print sql
    print(sql)
    con.insert_sql(sql)

if __name__ == "__main__":
    args = sys.argv
    currency = args[1].strip()
    con = MysqlConnector()

    now = datetime.now()
    base_time = now

    # for TEST
    base_time = datetime.strptime("2018-01-11 11:00:00", "%Y-%m-%d %H:%M:%S")

    try:
        while True:
            flag = decideMarket(now)

            now = datetime.now()
            tmp_time = now - timedelta(seconds=10)
            if tmp_time < base_time:
                flag = False
                #print "base_time > now, base_time = %s, now = %s" % (base_time, now)
                print("base_time > now, base_time = %s, now = %s" % (base_time, now))
            else:
                base_time = base_time + timedelta(seconds=1)
                #print "base_time = %s" % base_time
                print("base_time = %s" % base_time)

            if flag == False:
                pass
            else:
                sql = u"select insert_time from %s_TABLE where insert_time = \'%s\'" % (currency, base_time)
                #print sql
                print(sql)
                response = con.select_sql(sql)
                if len(response) == 0:
                    follow_record(con, base_time, currency)
                else:
                    pass

    except Exception as e:
        messege = "*** insert_check.py %s is Failed ***\n" % currency
        message = message + traceback.format_exc()
#        sendmail = SendMail("tomoyanpy@gmail.com", "tomoyanpy@softbank.ne.jp", property_path)
#        sendmail.set_msg(message)
#        sendmail.send_mail()
        #print message
        print(message)
