# coding: utf-8
import json
import time
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import logging

def instrument_init(instrument, base_path, config_name):
    config_path = "%s/config" % base_path
    config_file = open("%s/instruments.config_%s" % (config_path, config_name), "r")
    jsonData = json.load(config_file)
    config_data = jsonData[instrument]
    return config_data

def account_init(mode, base_path):
    property_path = "%s/property" % base_path
    property_file = open("%s/account.properties" % property_path, "r")
    jsonData = json.load(property_file)
    account_data = jsonData[mode]
    return account_data

# マーケットが休みであればfalseを返す
def decideMarket(base_time):
    flag = True
    month = base_time.month
    week = base_time.weekday()
    hour = base_time.hour

    # 冬時間の場合
    if month == 11 or month == 12 or month == 1 or month == 2 or month == 3:
        if week == 5 and hour > 6:
            flag = False

        elif week == 0 and  hour < 7:
            flag = False

    # 夏時間の場合
    else:
        if week == 5 and hour > 5:
            flag = False

        elif week == 0 and  hour < 6:
            flag = False

    # 日曜日の場合
    if week == 6:
        flag = False

    return flag

def getBollingerDataSet(ask_price_list, bid_price_list, window_size, sigma_valiable, candle_width):
    # pandasの形式に変換
    ask_lst = pd.Series(ask_price_list)
    bid_lst = pd.Series(bid_price_list)

    # 売値と買値の平均算出
    lst = (ask_lst+bid_lst) / 2

    # window_size × ローソク足
    window_size = window_size * candle_width

    # シグマと移動平均の計算
    sigma = lst.rolling(window=window_size).std(ddof=0)
    base = lst.rolling(window=window_size).mean()

    # ボリンジャーバンドの計算
    upper_sigmas = base + (sigma*sigma_valiable)
    lower_sigmas = base - (sigma*sigma_valiable)

    # 普通の配列型にキャストして返す
    upper_sigmas = upper_sigmas.values.tolist()
    lower_sigmas = lower_sigmas.values.tolist()
    lst = lst.values.tolist()
    base = base.values.tolist()

    data_set = { "upper_sigmas": upper_sigmas,
                 "lower_sigmas": lower_sigmas,
                 "price_list": lst,
                 "base_lines": base }
    return data_set

def extraBollingerDataSet(data_set, sigma_length, candle_width):
    # 過去5本分（50分）のsigmaだけ抽出
    sigma_length = sigma_length * candle_width
    sigma_length = sigma_length * -1

    upper_sigmas = data_set["upper_sigmas"]
    lower_sigmas = data_set["lower_sigmas"]
    price_list   = data_set["price_list"]
    base_lines   = data_set["base_lines"]

    upper_sigmas = upper_sigmas[sigma_length:]
    lower_sigmas = lower_sigmas[sigma_length:]
    price_list = price_list[sigma_length:]
    base_lines = base_lines[sigma_length:]

    data_set = { "upper_sigmas": upper_sigmas,
                 "lower_sigmas": lower_sigmas,
                 "price_list": price_list,
                 "base_lines": base_lines}

    return data_set

# 加重移動平均を計算
# wma_length = 期間（200日移動平均、など）
#def getWMA(ask_price_list, bid_price_list, wma_length, candle_width):
#    ask_price_list = pd.Series(ask_price_list)
#    bid_price_list = pd.Series(bid_price_list)
#    average_price_list = (ask_price_list + bid_price_list) / 2
#    average_price_list = average_price_list.values.tolist()
#    #logging.info("wma_length = %s" % wma_length)
#    #logging.info("candle_width = %s" % candle_width)
#
#    wma_length = (candle_width * wma_length) * -1
#    #logging.info("wma_length = %s" % wma_length)
#
#    # wma_lengthの分だけ抽出
#    average_price_list = average_price_list[wma_length:]
#    #logging.info("average_price_list length = %s" % len(average_price_list))
#
#    # wma_lengthの分だけ、重みの積を積み上げる
#    tmp_value = 0
#    denominator = 0
#    for i in range(0, len(average_price_list)):
#        weight = i + 1
#        denominator = denominator + weight
#        tmp_value = tmp_value + (average_price_list[i]*weight)
#
#   # 総数をwma_lengthの総和（シグマ）で割る⇒ 移動平均点
#    wma_value = tmp_value / denominator
#    #logging.info("denominator = %s" % denominator)
#    #logging.info("tmp_value = %s" % tmp_value)
#    #logging.info("wma_value = %s" % wma_value)
#
#    return wma_value


def getEWMA(ask_price_list, bid_price_list, wma_length, candle_width):
    ask_price_list = pd.Series(ask_price_list)
    bid_price_list = pd.Series(bid_price_list)
    average_price_list = (ask_price_list + bid_price_list) / 2

    wma_length = (candle_width * wma_length) 
    logging.info("getEWMA price_list length = %s, wma_length = %s" % (len(average_price_list), wma_length))

    wma_value_list = average_price_list.ewm(ignore_na=False, span=wma_length, min_periods=0, adjust=True).mean()

    average_price_list = average_price_list.values.tolist()
    wma_value_list = wma_value_list.values.tolist()

    return wma_value_list

def getSlope(target_list):
    index_list = []
    #length = len(target_list) * 10
    length = len(target_list)
    for i in range(1, len(target_list)+1):
        val = i/length
        index_list.append(val)

    price_list = np.array(target_list)
    index_list = np.array(index_list)

    z = np.polyfit(index_list, price_list, 1)
    slope, intercept = np.poly1d(z)

    return slope

# trendcheckとかの補助的な計算は毎回やる必要ないので
# ここでindex形式でスリープさせる
def countIndex(index, candle_width):
    flag = False
    if index != candle_width:
        index = index + 1
        flag = False
    else:
        index = 0
        flag = True

    return flag, index

def sleepTransaction(sleep_time, test_mode, base_time):
    sleep_time = int(sleep_time)
    if test_mode:
        base_time = base_time + timedelta(seconds=sleep_time)
    else:
        time.sleep(sleep_time)
        base_time = datetime.now()
    #logging.info("base_time=%s" % base_time)

    return base_time
