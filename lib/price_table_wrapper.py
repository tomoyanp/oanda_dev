# coding: utf-8

# いちいちテーブルから取得したものをパースするのが面倒なため、このラッパーをかます

class PriceTableWrapper:


    def __init__(self):
    	self.ask_price_list = []
    	self.bid_price_list = []
    	self.time_list = []


    def setResponse(self, response):
    	for line in reponse:
    		self.time_list.appned(line[0])
    		self.ask_price_list.appned(line[1])
    		self.bid_price_list.appned(line[2])

	def getTimeList(self):
		return self.time_list

	def getAskPriceList(self):
		return self.ask_price_list

	def getBidPriceList(self):
		return self.bid_price_list