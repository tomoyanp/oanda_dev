# coding: utf-8

####################################################
#
# calculate methods
#
####################################################

def decideLowSurplusPrice(current_price, low_price, threshold):
    flag = False
    mode = "pass"
    if (float(low_price) + float(threshold)) < current_price:
        mode = "surplus"
        flag = True

    return flag, mode

def decideLowExceedPrice(current_price, low_price, threshold):
    flag = False
    mode = "pass"
    if current_price < (float(low_price) - float(threshold)):
        mode = "exceed"
        flag = True

    return flag, mode

def decideHighSurplusPrice(current_price, high_price, threshold):
    flag = False
    mode = "pass"

    if  current_price < (float(high_price) - float(threshold)):
        mode = "surplus"
        flag = True

    return flag, mode

def decideHighExceedPrice(current_price, high_price, threshold):
    flag = False
    mode = "pass"
    if current_price > (float(high_price) + float(threshold)):
        mode = "exceed"
        flag = True

    return flag, mode

def decideVolatility(current_price, volatility_value, volatility_buy_price, volatility_bid_price):
    up_flag = False
    down_flag = False

    if float(volatility_buy_price) + float(volatility_value) < current_price:
        up_flag = True
    elif float(volatility_bid_price) - float(volatility_value) > current_price:
        down_flag = True

    return up_flag, down_flag


def decideDailyVolatilityPrice(max_price, min_price, threshold, side):
    flag = False
    if float(max_price) - float(min_price) < threshold:
        flag = True

    return flag

def updateMaxMinPriceWrapper(current_price, max_price, min_price):
    if current_price > max_price:
        max_price = current_price

    if current_price < min_price:
        min_price = current_price


    return max_price, min_price

