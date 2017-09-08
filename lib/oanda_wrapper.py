# coding: utf-8

from oandapy import oandapy
from price_obj import PriceObj
from order_obj import OrderObj
from datetime import datetime, timedelta
import time

class OandaWrapper:
    def __init__(self, env, account_id, token):
        self.oanda = oandapy.API(environment=env, access_token=token)
        self.account_id = account_id

    def get_price(self, currency):
        response = self.oanda.get_prices(instruments=currency)
        prices = response.get("prices")
        price_time = prices[0].get("time")
        instrument = prices[0].get("instrument")
        asking_price = prices[0].get("ask")
        selling_price = prices[0].get("bid")
        price_obj = PriceObj(instrument, price_time, asking_price, selling_price)
        return price_obj


    def order(self, l_side, currency, stop_loss, take_profit):
        try:
            while True:
                response = self.oanda.create_order(self.account_id,
                    instrument=currency,
                    units=50000,
                    side=l_side,
                    stopLoss=stop_loss,
                    takeProfit=take_profit,
                    type='market'
                )
                time.sleep(5)
                print response
                if len(response) > 0:
                    print "ordered"
                    break
            return response
        except Exception as e:
            raise


    # positionがあるかチェック
    def get_trade_response(self, trade_id):
        try:
            response = {}
            response = self.oanda.get_trades(self.account_id)
            for trade in response["trades"]:
                if trade_id == trade["id"]:
                    response = trade
            return response

        except:
            raise
            
    def close_trade(self, trade_id):
        try:
            #response = self.oanda.get_trades(self.account_id)
            #print response
            #trade_id = response["trades"][0]["id"]
            self.oanda.close_trade(self.account_id, trade_id)
            print "closed"
        except:
            raise
