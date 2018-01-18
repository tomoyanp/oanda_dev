# coding: utf-8

import sys
import os
from datetime import datetime, timedelta
import threading
import time


class SetPriceThread(threading.Thread):

    def __init__(self, price_object):
        super(SetPriceThread, self).__init__()
        self.price_object = price_object
        self.base_time = self.price_object.getBaseTime()

    def run(self):
        index = 0
        while True:
            index = index + 1 
            self.base_time = self.price_object.getBaseTime()
            print self.base_time
            self.price_object.setData(index) 
            time.sleep(0.1)
      
