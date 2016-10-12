# coding: utf-8
from datetime import datetime, timedelta
import oandapy
import time

account_id = 2542764
token = '85abe6d9c2646b9c56fbf01f0478a511-fe9cb897da06cd6219fde9b4c2052055'
oanda = oandapy.API(environment="practice", access_token=token)
price_list = []

class orderObj():
    def __init__(self, id, price):
        self.id = id
        self.price = price

    def getId(self):
        return self.id

    def getPrice(self):
        return self.price        
   
def get_price(oanda):
    response = oanda.get_prices(instruments="USD_JPY")
    prices = response.get("prices")
    price_time = response.get("time")
    asking_price = prices[0].get("ask")
    selling_price = prices[0].get("bid")
    return asking_price


#trade_expire = datetime.utcnow() + timedelta(days=1)
#trade_expire = trade_expire.isoformat("T") + "Z"

def order(oanda, l_side):    
    response = oanda.create_order(account_id,
        instrument="USD_JPY",
        units=1000,
        side=l_side,
        type='market'
    )
    id = response.get("id")
    price = response.get("price")
    orderInstance = orderObj(id, price)
    return orderInstance
    
    
def get_tradeid(oanda):
    response = oanda.get_trades(account_id)
    for trade in response.get("trades"):
        print trade.get("id")


def settlement(oanda, orderInstance):
    while True:
        price = get_price(oanda)
        buy_price = orderInstance.getPrice()
# 損切り
        if price - buy_price < -0.2:
            oanda.close_trade(account, orderInstance.getId())
# 利確
        elif price - buy_price > 0.2:
            oanda.close_trade(account, orderInstance.getId())
# 継続
        else:
            pass


#response = oanda.get_orders(account_id)
#約定していないものしか表示されない

#print response

#response = oanda.close_order(account_id, 10463873762)
#response = oanda.close_order(account_id, 10463873762)
#response = oanda.get_positions(account_id)
#response = oanda.get_trades(account_id)
#response = oanda.close_trade(account_id, 10463873762)
#print response    


if __name__ == '__main__':
    while True:
        price_list = []
        while True:
            price = get_price(oanda)
            price_list.append(price)
            if len(price_list) > 5:
                price_list.pop(0)
        
            print price_list
            if len(price_list) < 5:
                pass
            elif price_list[0] - price < 0:
                print "DO ORDER!!!"
                orderInstance = order(oanda, "buy")
                break
            else:
                print "DO NOT ORDER!! "
     
            time.sleep(60)
        settlement(oanda, orderInstance)
