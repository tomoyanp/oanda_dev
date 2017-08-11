# coding: utf-8
from datetime import datetime
from datetime import timedelta

now = datetime.now()
week_ago = now - timedelta(days=14)
week_ago = week_ago.strftime("%Y-%m-%d")

sql = u"delete from GBP_JPY_TABLE where insert_time < \'%s\'" % week_ago
print sql
