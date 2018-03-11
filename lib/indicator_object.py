#coding: utf-8
#####################################################################
#
# 価格とインジケータはこのオブジェクトで格納
# 親スレッドと子スレッドはこのオブジェクトを通してデータにアクセスする
#
#####################################################################

import logging
class IndicatorObject:
    def __init__(self):
        self.ask_price_list = []
        self.bid_price_list = []
        self.insert_time_list = []
        self.high_low_price_dataset = {}
        self.ewma200_1h_dataset = {}
        self.bollinger_2p5sigma_dataset = {}
        self.ewma50_5m_dataset = {}

    def setPriceList(self, response):
        if len(response) < 1:
            pass
        else:
            self.ask_price_list = []
            self.bid_price_list = []
            self.insert_time_list = []
            for line in response:
                self.ask_price_list.append(line[0])
                self.bid_price_list.append(line[1])
                self.insert_time_list.append(line[2])

            self.ask_price_list.reverse()
            self.bid_price_list.reverse()
            self.insert_time_list.reverse()

    def addPriceList(self, response):
        response_length = len(response)
        if response_length < 1:
            pass
        else:
            logging.info("Remove Price List Start")
            del self.ask_price_list[0:response_length]
            del self.bid_price_list[0:response_length]
            del self.insert_time_list[0:response_length]
#            self.ask_price_list = self.ask_price_list[response_length:]
#            self.bid_price_list = self.bid_price_list[response_length:]
#            self.insert_time_list = self.insert_time_list[response_length:]
            logging.info("Remove Price List End")

            logging.info("Add Price List Start")
            for res in response:
                self.ask_price_list.append(res[0])
                self.bid_price_list.append(res[1])
                self.insert_time_list.append(res[2])
            logging.info("Add Price List End")
        logging.info("PRICE_LIST LENGTH: ask_price_list = %s, bid_price_list = %s" % (len(self.ask_price_list), len(self.bid_price_list)))

    def getPriceList(self):
        return self.ask_price_list, self.bid_price_list, self.insert_time_list

    def getAskPriceList(self):
        return self.ask_price_list

    def getBidPriceList(self):
        return self.bid_price_list

    def getInsertTimeList(self):
        return self.insert_time_list

    def setHighLowPriceDataset(self, high_price, low_price, base_time):
        self.high_low_price_dataset = {"high_price": high_price,
                                     "low_price": low_price,
                                     "get_time": base_time}

    def getHighLowPriceDataset(self):
        return self.high_low_price_dataset


    def setEwma200_1hDataset(self, ewma200_1h, base_time):
        self.ewma200_1h_dataset = {"ewma_value": ewma200_1h[-1],
                               "get_time": base_time}

    def getEwma200_1hDataset(self):
        return self.ewma200_1h_dataset


    def setBollinger2p5sigmaDataset(self, data_set, base_time):
        self.bollinger_2p5sigma_dataset = {"upper_sigma": data_set["upper_sigmas"][-1],
                                           "lower_sigma": data_set["lower_sigmas"][-1],
                                           "base_line": data_set["base_lines"][-1],
                                           "get_time": base_time}

    def getBollinger2p5sigmaDataset(self):
        return self.bollinger_2p5sigma_dataset


    def setEwma50_5mDataset(self, ewma50, slope, base_time):
        self.ewma50_5m_dataset = {"ewma_value": ewma50[-1],
                               "slope": slope,
                               "get_time": base_time}

    def getEwma50_5mDataset(self):
        return self.ewma50_5m_dataset


    def setEwma200_5mDataset(self, ewma200, base_time):
        self.ewma200_5m_dataset = {"ewma_value": ewma200[-1],
                                "get_time": base_time}

    def getEwma200_5mDataset(self):
        return self.ewma200_5m_dataset
