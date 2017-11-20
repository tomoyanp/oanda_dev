# coding: utf-8
import json
from datetime import datetime, timedelta

def instrument_init(instrument, base_path):
    config_path = "%s/config" % base_path
    config_file = open("%s/instruments.config" % config_path, "r")
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

def decide_up_down_before_day(con, base_time, instrument):
    comp_time = base_time.strftime("%H:%M:%S")
    now = base_time
    if comp_time > "00:00:00" and comp_time < "06:00:00":
      before_day = now - timedelta(days=2)
      now = now - timedelta(days=1)
    else:
      before_day = now - timedelta(days=1)

    before_day = before_day.strftime("%Y-%m-%d")
    before_end_day = now.strftime("%Y-%m-%d")
    sql = u"select ask_price from %s_TABLE where insert_time > \'%s 06:00:00\' and insert_time < \'%s 06:00:10\'" % (instrument, before_day, before_day)
    print sql
    response = con.select_sql(sql)
    before_start_price = response[0][0]

    sql = u"select ask_price from %s_TABLE where insert_time > \'%s 05:59:49\' and insert_time < \'%s 05:59:59\'" % (instrument, before_end_day, before_end_day)
    print sql
    response = con.select_sql(sql)
    tmp_list = []
    for line in response:
        tmp_list.append(line)
    before_end_price = response[0][0]

    if before_end_price - before_start_price > 0:
        before_flag = "buy"
    else:
        before_flag = "sell"

    print "before_start_price : %s" % before_start_price
    print "before_end_price : %s" % before_end_price
    print "before_flag : %s" % before_flag
    return before_flag
