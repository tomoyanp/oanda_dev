# coding: utf-8

####################################################
#
# get indicator methods
#
####################################################

from datetime import datetime, timedelta
from common import getBollingerDataSet

def getBollingerWrapper(base_time, instrument, table_type, window_size, connector, sigma_valiable, length):
    sql = "select end_price from %s_%s_TABLE where insert_time < \'%s\' order by insert_time DESC limit %s" % (instrument, table_type, base_time, (window_size+length))
    print sql
    response = connector.select_sql(sql)
    price_list = []
    for res in response:
        price_list.append(res[0])

    price_list.reverse()
    data_set = getBollingerDataSet(price_list, window_size=window_size, sigma_valiable=sigma_valiable)

    return data_set

def getRsiWrapper(base_time, instrument, table_type, connector, span):
    sql = "select end_price from %s_%s_TABLE where insert_time < \'%s\' order by insert_time DESC limit %s" % (instrument, table_type, base_time, span)
    print sql
    response = connector.select_sql(sql)
    price_list = []
    for res in response:
        price_list.append(res[0])
    price_list.reverse()

    up_value = 0
    down_value = 0

    for i in range(1, len(price_list)):
        if price_list[i-1] < price_list[i]:
            up_value = up_value + (price_list[i] - price_list[i-1])
        else:
            down_value = down_value + (price_list[i-1] - price_list[i])

    rsi_value = (up_value/(up_value + down_value))*100

    return rsi_value


def getEwmaWrapper(instrument, base_time, ind_type, span, connector):
    sql = "select ewma_value from INDICATOR_TABLE where instrument = \'%s\' and insert_time <= \'%s\' and type = \'%s\' order by insert_time DESC limit %s" % (instrument, base_time, ind_type, span)
    response = connector.select_sql(sql)
    ewma_list = []
    for res in response:
        ewma_list.append(res[0])

    ewma_list.reverse()

    return ewma_list

def getVolatilityPriceWrapper(instrument, base_time, span, connector):
    start_time = base_time
    sql = "select ask_price, bid_price from %s_TABLE where insert_time < \'%s\' order by insert_time desc limit %s" % (instrument, start_time, span)
    response = connector.select_sql(sql)
    volatility_buy_price = response[-1][0]
    volatility_bid_price = response[-1][0]

    return volatility_buy_price, volatility_bid_price

def getHighlowPriceWrapper(instrument, base_time, span, table_type, connector):
    sql = "select max_price, min_price from %s_%s_TABLE where insert_time < \'%s\' order by insert_time DESC limit %s" % (instrument, table_type, base_time, span)
    response = connector.select_sql(sql)
    high_price_list = []
    low_price_list = []
    for res in response:
        high_price_list.append(res[0])
        low_price_list.append(res[1])

    high_price = max(high_price_list)
    low_price =  min(low_price_list)

    return high_price, low_price

# select start price the day
def getStartPriceWrapper(instrument, base_time, connector):
    start_time = base_time.strftime("%Y-%m-%d 07:00:00")
    sql = "select ask_price, bid_price from %s_TABLE where insert_time = \'%s\'" % (instrument, start_time)
    response = connector.select_sql(sql)

    ask_price = response[0][0]
    bid_price = response[0][0]

    return (ask_price + bid_price) / 2


# select start and end price the last day
def getLastPriceWrapper(instrument, base_time, connector):
    if base_time.weekday() == 0:
        start_time = base_time - timedelta(days=3)
        end_time = base_time - timedelta(days=2)
    else:
        start_time = base_time - timedelta(days=1)
        end_time = base_time

    start_time = start_time.strftime("%Y-%m-%d 07:00:00")
    end_time = end_time.strftime("%Y-%m-%d 07:00:00")

    sql = "select ask_price, bid_price from %s_TABLE where insert_time = \'%s\'" % (instrument, start_time)
    response = connector.select_sql(sql)
    start_price = (response[0][0] + response[0][1]) / 2

    sql = "select ask_price, bid_price from %s_TABLE where insert_time = \'%s\'" % (instrument, end_time)
    response = connector.select_sql(sql)
    end_price = (response[0][0] + response[0][1]) / 2

    return start_price, end_price


def getWeekStartPrice(instrument, base_time, week_start_price, current_price):
    weekday = base_time.weekday()
    hour = base_time.hour
    minutes = base_time.minute

    if weekday == 0 and hour == 7 and minutes == 0:
        week_start_price = current_price

    elif week_start_price == 0:
        week_start_price = current_price

    else:
        pass

    return week_start_price
