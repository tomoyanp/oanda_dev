# coding: utf-8
from datetime import datetime, timedelta
import oandapy
import time

account_id = 2542764
token = '85abe6d9c2646b9c56fbf01f0478a511-fe9cb897da06cd6219fde9b4c2052055'
oanda = oandapy.API(environment="practice", access_token=token)
price_list = []

class PriceObj:
    def __init__(self, price_time, asking_price, selling_price):
        self.price_time = price_time
        self.asking_price = asking_price
        self.selling_price = selling_price

    def getPriceTime(self):
        return self.price_time

    def getAskingPrice(self):
        return self.asking_price

    def getSellingPrice(self):
        return self.selling_price

def get_price(currency):
    response = oanda.get_prices(instruments=currency)
    prices = response.get("prices")
    price_time = response.get("time")
    asking_price = prices[0].get("ask")
    selling_price = prices[0].get("bid")
    price_obj = PriceObj(price_time, asking_price, selling_price)
    return price_obj


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

def update_price():
    price = get_price()

if __name__ == '__main__':
    currency = "USD_JPY"
    price_obj = get_price(currency)

    print price_obj.getPriceTime()
    print price_obj.getAskingPrice()
    print price_obj.getSellingPrice()
