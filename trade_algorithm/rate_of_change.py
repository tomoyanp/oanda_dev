# coding: utf-8

import oandapy
from mysql_connector import MysqlConnector
from db_wrapper import DBWrapper

class RateOfChange:
	def __init__(self, base_seconds, instrument):
		self.db_wrapper = DBWrapper()
		self.base_seconds = base_seconds
		self.instrument = instrument
		# 一分足の動きをベースに閾値を計算する
		self.threshold_time = 60
		self.base_rate_of_change_list = []

	def set_base_threshold(self):
		response = self.db_wrapper.getPrice(self.base_seconds, self.instrument)
		# ask_price = [] こういう想定
		# bid_pricd = []

        ask_threshold_price = []

        # 一分ごとの始め値と終わり値を抽出
		for i in range(0, len(ask_price)):
			if i % self.threshold_time == 0:
				ask_threshold_price.append(ask_price[i])

        ask_rate_of_change_list = []

        # listの偶数か奇数かで始め値 or 終わり値
        # 終わり値 - 始め値を計算
        for i in range(0, len(ask_threshold_price)):
        	if i % 2 != 0:
        		result = ask_threshold_price[i] - ask_threshold_price[i-1]
        		# 結果がマイナスの場合、プラスに反転させる
        		if result < 0:
        			result = result * -1
        		ask_rate_of_change_list.append(result)

         self.base_rate_of_change_list = ask_rate_of_change_list
#        rate_of_change = sum(ask_rate_of_change_list)/len(ask_rate_of_change_list) 
#        return rate_of_change


	def decide_trade(self, threshold):



