
def decide_up_down_before_day(con):
    now = datetime.now()
    # 前日が陽線引けかどうかでbuy or sellを決める
    before_day = now - timedelta(days=1)
    before_day = before_day.strftime("%Y-%m-%d")
    before_end_day = now.strftime("%Y-%m-%d")
    sql = u"select ask_price from %s_TABLE where insert_time > \'%s 06:00:00\' and insert_time < \'%s 06:00:10\'" % (currency, before_day, before_day)
    print sql
    response = con.select_sql(sql)
    before_start_price = response[0][0]

    sql = u"select ask_price from %s_TABLE where insert_time > \'%s 05:59:49\' and insert_time < \'%s 05:59:59\'" % (currency, before_end_day, before_end_day)
    print sql
    response = con.select_sql(sql)
    tmp_list = []
    for line in response:
        tmp_list.append(line)
    before_end_price = response[0][0]

    if before_end_price - before_start_price > 0:
        before_flag = "buy"
    else:
        before_flag = "bid"

    before_flag = "buy"

    print "before_start_price : %s" % before_start_price
    print "before_end_price : %s" % before_end_price
    print "before_flag : %s" % before_flag
    return before_flag
