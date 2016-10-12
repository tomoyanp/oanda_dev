# coding: utf-8
from datetime import datetime, timedelta
from order_info import orderInfo
import oandapy
import time

account_id = 2542764
token = '85abe6d9c2646b9c56fbf01f0478a511-fe9cb897da06cd6219fde9b4c2052055'
oanda = oandapy.API(environment="practice", access_token=token)
price_list = []
day_lower_threshold = 0.1
day_upper_threshold = 0.02
night_threshold = 0.2
default_units = 10000
default_instrument = "USD_JPY"
default_type = "market"
lower_threshold_time = 7
upper_threshold_time = 17
mode = "buy"
settlement_mode = "bid"
 
# 引数に買いか売りか指定出来る(ask or bid)
def get_price(l_side):
    response = oanda.get_prices(instruments=default_instrument)
    prices = response.get("prices")
    price_time = response.get("time")
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


def settlement(orderInstance):
    if mode == 'buy':
        settlement_mode = 'bid'
    else:
        settlement_mode = 'ask'

    while True:
        # デフォルトの損切り、利確の閾値は20pips
        lower_threshold = night_threshold
        upper_threshold = night_threshold
        now = datetime.now().hour
        print "current time = %s" % now
        if lower_threshold_time < now and now < upper_threshold_time:
            lower_threshold = day_lower_threshold
            upper_threshold = day_upper_threshold
        else:
            lower_threshold = night_threshold
            upper_threshold = night_threshold
        print "lower_threshold = %s" % lower_threshold
        print "upper_threshold = %s" % upper_threshold

        time.sleep(30)
        price = get_price(settlement_mode)
        print "current price = %s" % price
        buy_price = orderInstance.getPrice()
        print "yakujou price = %s" % buy_price
# 損切り
        if (buy_price - price) > lower_threshold:
            oanda.close_trade(account_id, orderInstance.getId())
            print "#########################"
            print "DO CLOSE TRADE BY SONGIRI"
            print "#########################"
            break
# 利確
        elif (price - buy_price) > upper_threshold:
            oanda.close_trade(account_id, orderInstance.getId())
            print "#########################"
            print "DO CLOSE TRADE BY RIKAKU"
            print "#########################"
            break
# 継続
        else:
            print "DO NOT CLOSE TRADE ... PASS"
            pass

            

if __name__ == '__main__':
    while True:
        price_list = []
        while True:
            price = get_price("ask")
            price_list.append(price)
            if len(price_list) > 5:
                price_list.pop(0)
        
            print price_list
            if len(price_list) < 5:
                pass
            elif price_list[0] - price < 0:
                print "DO ORDER!!!"
                print "initial price = %s" % price_list[0] 
                print "asking price = %s" % price 
                orderInstance = order(mode)
                break
            else:
                print "DO NOT ORDER!! "
            time.sleep(60)
        settlement(orderInstance)
