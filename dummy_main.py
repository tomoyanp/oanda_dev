#coding: utf-8

## dummy
current_path = os.path.abspath(os.path.dirname(__file__))
sys.path.append(current_path)
sys.path.append(current_path + "/lib")
config_path = current_path + "/config"
config_name = "trendfollow_dummy"

from compute_price_thread import ComputePriceThread
from indicator_object import IndicatorObject
from datetime import datetime, timedelta

if __name__ == "__main__":
    instrument = "GBP_JPY"
    indicator_object = IndicatorObject()
    base_time = datetime.now()
    thread = ComputePriceThread(instrument, base_path, config_name, indicator_object, base_time)
    thread.start()
    base_time = datetime.strptime("2018-02-01 00:00:00", "%Y-%m-%d %H:%M:%S")

    for i in range(0, 10000):
        base_time = base_time + timedelta(seconds=2)
        thread.setBaseTime(base_time)
        ask_price_list, bid_price_list, insert_time_list = indicator_object.getPriceList()
        for elm in insert_time_list:
            print elm
        print "============================"
