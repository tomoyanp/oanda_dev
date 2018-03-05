#coding: utf-8
#############################################
# Parent Class ===> new price_object
# Parent Class ===> new thread
# Parent Class ===> thread.setBaseTime
# Thread Class ===> compute price and price_object.setPrice
# Parent Class ===> price_object.getPrice
#############################################

import threading
from datetime import datetime, timedelta
from price_object import PriceObject

class ComputePriceThread(threading.Thread):
    def __init__(self, price_object, base_time):
        super(ComputePriceThread, self).__init__()
        self.price_object = price_object
        self.old_base_time = base_time
        self.base_time = base_time
        self.setPrice()

    def setBaseTime(self, base_time):
        self.base_time = base_time

    def getBaseTime(self):
        return self.base_time

    def setPrice(self):
        self.price_object.setPriceList([1,2,3,4,5])

    def run(self):
        for i in range(0, 10000):
            base_time = self.getBaseTime()
            if self.old_base_time < base_time:
                self.old_base_time = base_time
                price_list = self.price_object.getPriceList()
                price_list.append(i)
                self.price_object.setPriceList(price_list)



if __name__ == "__main__":
    price_object = PriceObject()
    base_time = datetime.now()
    thread = ComputePriceThread(price_object, base_time)
    thread.start()

    for i in range(0, 10000):
        base_time = base_time + timedelta(seconds=i) 
        thread.setBaseTime(base_time)
        price_list = price_object.getPriceList()
        print price_list
        print "================================"

