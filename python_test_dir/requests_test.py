# coding: utf-8
import requests

instruments = 'GBP_JPY'
account_id = 4093685
token = 'e93bdc312be2c3e0a4a18f5718db237a-32ca3b9b94401fca447d4049ab046fad'
url = "https://api-fxtrade.oanda.com/v3/accounts/%s/instruments" % account_id
headers = {'Content-Type': 'application/json',
           'Authorization': 'Bearer %s' % token}
params = {'instruments': instruments}

response = requests.get(url, params=params, headers, headers)
print response
