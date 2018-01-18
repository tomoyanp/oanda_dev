#coding: utf-8

from test_thread import SetPriceThread
from datetime import datetime
from price_object import PriceObject
import time

now = datetime.now()
price_object = PriceObject(now)
th = SetPriceThread(price_object)


th.start()
while True:
    now = datetime.now()
    time.sleep(1)
    price_object.setBaseTime(now)
    data = price_object.getData()
    print data
