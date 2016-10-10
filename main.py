# coding: utf-8
from datetime import datetime, timedelta
import oandapy
import time

account_id = 2542764
token = '85abe6d9c2646b9c56fbf01f0478a511-fe9cb897da06cd6219fde9b4c2052055'
oanda = oandapy.API(environment="practice", access_token=token)
def get_price():
    oanda = oandapy.API(environment="practice", access_token=token)
    response = oanda.get_prices(instruments="USD_JPY")
    prices = response.get("prices")
    time = response.get("time")
    asking_price = prices[0].get("ask")
    selling_price = prices[0].get("bid")
    time.sleep(60)


#trade_expire = datetime.utcnow() + timedelta(days=1)
#trade_expire = trade_expire.isoformat("T") + "Z"

def order(oanda, l_side):    
    response = oanda.create_order(account_id,
        instrument="USD_JPY",
        units=1000,
        side=l_side,
        type='market'
    )
    print response
    
    
order(oanda, "buy")

#response = oanda.get_orders(account_id)
#約定していないものしか表示されない

#print response

#response = oanda.close_order(account_id, 10463873762)
#response = oanda.close_order(account_id, 10463873762)
#response = oanda.get_positions(account_id)
#response = oanda.get_trades(account_id)
#response = oanda.close_trade(account_id, 10463873762)
#print response    
