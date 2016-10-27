# coding: utf-8
from datetime import datetime, timedelta
from order_info import orderInfo
from mysql_connector import mysqlConnector
import oandapy
import time

account_id = 2542764
token = '85abe6d9c2646b9c56fbf01f0478a511-fe9cb897da06cd6219fde9b4c2052055'
oanda = oandapy.API(environment="practice", access_token=token)
threshold = 0.02
default_units = 50000
default_instrument = "USD_JPY"
default_type = "market"
mode = "buy"
settlement_mode = "sell"

get_price_mode = "ask"
settle_price_mode = "bid"

db_connector = mysqlConnector()
 
def get_price(l_side):
    response = oanda.get_prices(instruments=default_instrument)
    prices = response.get("prices")
    price = prices[0].get(l_side)
    return price

# 引数に買いか売りか指定出来る(buy or sell)
def order(l_side):    
    response = oanda.create_order(account_id,
        instrument=default_instrument,
        units=default_units,
        side=l_side,
        type=default_type
    )
    trade_info = response.get("tradeOpened")
    id = trade_info.get("id")
    price = response.get("price")
    orderInstance = orderInfo(id, price)
    print "orderInstance.id = %s" % orderInstance.getId()
    print "orderInstance.price = %s" % orderInstance.getPrice()
    print "yakujou price = %s" % price
    return orderInstance
    
def get_tradeid():
    response = oanda.get_trades(account_id)
    for trade in response.get("trades"):
        print trade.get("id")

if __name__ == '__main__':
    while True:
        flag = False
        while flag == False:    
            time.sleep(30)
            # 現在の価格をGET
            current_price_ask = get_price("ask")
            current_price_bid = get_price("bid")
            algorithm = tradeAlgolithm()
            # 過去6時間の最大値、最小値をSET
            algorithm.set_range_limit()

            order_flag = algorithm.trade_decision_at_day(current_price_ask, current_price_bid)
            if order_flag is not None:
                if order_flag == 'sell':
                    mode = 'sell'
                    settlement_mode = 'buy'
                elif order_flag == 'buy':
                    mode = 'buy'    
                    settlement_mode = 'sell'    
                else:
                    print "--- MODE CHECK ERROR ---"    

                orderInstance = order(mode)
                flag = True
                break
            else:
                pass    
        flag = False:        
        while flag == False:
            time.sleep(15)
            # 現在の価格をGET
            current_price = get_price("bid")
            yakujou_price = orderInstance.getPrice()
            print "--- current price ---"
            print current_price
            print "--- yakujou price ---"
            print yakujou_price
            print "---------------------"
            settle_flag = algorithm.settlement_decision_at_day(yakujou_price, current_price, threshold)
            if settle_flag:
                oanda.close_trade(account_id, orderInstance.getId())
                flag = True
                print "--- DO CLOSE ORDER ---"
                print "--- current_price = %s" % current_price
                print "--- yakujou_price = %s" % yakujou_price
                print "----------------------"
            else:
                pass
