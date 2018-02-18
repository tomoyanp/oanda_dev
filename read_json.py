# coding: utf-8

import json


file = open("get_trades_result")

response = json.load(file)
print len(response)
trade_data = response["trades"][0]
order_price = trade_data["price"]
order_kind  = trade_data["side"]
trade_id = trade_data["id"]

print order_price
print order_kind
print trade_id
