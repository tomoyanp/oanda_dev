#coding: utf-8


class PriceObject():
    def __init__(self, base_time):
        self.base_time = base_time
        self.data = 0

    def setBaseTime(self, base_time):
        self.base_time = base_time

    def getBaseTime(self):
        return self.base_time

    def setData(self, data):
        self.data = data

    def getData(self):
        return self.data
        
