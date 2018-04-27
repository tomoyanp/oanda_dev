# coding: utf-8

####################################################
#
# get indicator methods
#
####################################################

from datetime import datetime, timedelta

def getBollingerWrapper(base_time, instrument, ind_type, span, connector):
    sql = "select upper_sigma, lower_sigma, base_line from INDICATOR_TABLE where instrument = \'%s\' and insert_time <= \'%s\' and type = \'%s\' order by insert_time DESC limit %s" % (instrument, base_time, ind_type, span)
    response = connector.select_sql(sql)
    upper_list = []
    lower_list = []
    base_list = []
    for res in response:
        upper_list.append(res[0])
        lower_list.append(res[1])
        base_list.append(res[2])

    upper_list.reverse()
    lower_list.reverse()
    base_list.reverse()

    return upper_list, lower_list, base_list


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

def getHighlowPriceWrapper(instrument, base_time, span, slide_span, connector):
    ind_type = "highlow"
    end_time = base_time - timedelta(hours=slide_span)
    sql = "select high_price, low_price from INDICATOR_TABLE where instrument = \'%s\' and insert_time <= \'%s\' and type = \'%s\' order by insert_time DESC limit %s" % (instrument, end_time, ind_type, span)
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


# select start price the day
def getLastPriceDifferenceWrapper(instrument, base_time, connector):
    span = 3600*24
    start_time = base_time

    sql = "select ask_price, bid_price from %s_TABLE where insert_time < \'%s\' order by insert_time desc limit %s" % (instrument, start_time, span)
    response = connector.select_sql(sql)

    end_price = (response[0][0] + response[0][1]) / 2
    start_price = (response[-1][0] + response[-1][0]) / 2

    return (end_price - start_price)


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
