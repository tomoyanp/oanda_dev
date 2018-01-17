#coding: utf-8

from test_thread import SetPriceThread
from datetime import datetime
import time

now = datetime.now()
th = SetPriceThread("USD_JPY", now, 30)


th.start()
while True:
    now = datetime.now()
    time.sleep(1)
    th.setBaseTime(now)
