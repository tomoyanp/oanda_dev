import httplib
import urllib
import json
import datetime

# side is sell or buy
def trade(side):
    conn = httplib.HTTPSConnection("api-sandbox.oanda.com")
    headers = {"Content-Type" : "application/x-www-form-urlencoded"}
    params = urllib.urlencode({"instrument" : "USD_CAD",
                               "units" : 50,
                               "type" : 'market',
                               "side" : side})
    conn.request("POST", "/v1/accounts/8026346/orders", params, headers)
    print conn.getresponse().read()

def checkAskPrice():
#    conn = httplib.HTTPSConnection("api-sandbox.oanda.com")
    conn = httplib.HTTPSConnection("api-fxpractice.oanda.com")
    conn.request("GET", "/v1/prices?instruments=USD_CAD")
    response = conn.getresponse()
    resptext = response.read()
    print response.status
    if response.status == 200:
        data = json.loads(resptext)
        print data['prices'][0]['ask']

def checkBidPrice():
   conn = httplib.HTTPSConnection("api-sandbox.oanda.com")
   conn.request("GET", "/v1/prices?instruments=USD_CAD")
   response = conn.getresponse()
   resptext = response.read()
   if response.status == 200:
       data = json.loads(resptext)
       print data['prices'][0]['bid']       
