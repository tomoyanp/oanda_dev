# coding: utf-8

from oandapy import oandapy
from price_obj import PriceObj

class OandaWrapper:
    def __init__(self, env, account_id, token):
        self.oanda = oandapy.API(environment=env, access_token=token)

    def get_price(self, currency):
        response = self.oanda.get_prices(instruments=currency)
        prices = response.get("prices")
        price_time = prices[0].get("time")
        instrument = prices[0].get("instrument")
        asking_price = prices[0].get("ask")
        selling_price = prices[0].get("bid")
        price_obj = PriceObj(instrument, price_time, asking_price, selling_price)
        return price_obj
