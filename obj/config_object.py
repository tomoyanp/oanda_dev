#coding: utf-8

from common import instrument_init

class ConfigObject:
	def __init__(self, instrument, base_path):
        config_data        = instrument_init(instrument, base_path)
        self.instrument = instrument
        self.trade_threshold    = config_data["trade_threshold"]
        self.optional_threshold = config_data["optional_threshold"]
        self.stop_loss          = config_data["stop_loss"]
        self.take_profit        = config_data["take_profit"]
        self.time_width         = config_data["time_width"]
        self.stl_time_width     = config_data["stl_time_width"]
        self.stl_sleeptime      = config_data["stl_sleeptime"]
        self.units              = config_data["units"]	
        self.trend_time_width   = config_data["trend_time_width"]


    def getInstrument(self):
    	return self.instrument

    def getTradeThreshold(self):
    	return self.trade_threshold
    	
    def getOptionalThreshold(self):
    	return self.optional_threshold
    	
    def getStopLoss(self):
    	return self.stop_loss
    	
    def getTakeProfit(self):
    	return self.take_profit
    	
    def getTimeWidth(self):
    	return self.time_width
    	
    def getStlTimeWidth(self):
    	return self.stl_time_width

    def getStlSleepTime(self):
    	return self.stl_sleeptime

    def getUnits(self):
    	return self.units

    def getTrendTimeWidth(self):
    	return self.trend_time_width