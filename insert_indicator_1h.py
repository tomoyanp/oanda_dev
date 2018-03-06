#coding: utf-8

## dummy
import os, sys
current_path = os.path.abspath(os.path.dirname(__file__))
sys.path.append(current_path)
sys.path.append(current_path + "/lib")
config_name = "trendfollow_dummy"

import traceback
from compute_indicator import ComputeIndicator
from datetime import datetime, timedelta
import time

if __name__ == "__main__":
    instrument = "GBP_JPY"
#    base_time = datetime.strptime("2017-02-10 00:00:00", "%Y-%m-%d %H:%M:%S")
    base_time = datetime.strptime("2018-03-05 19:00:00", "%Y-%m-%d %H:%M:%S")
    end_time = datetime.strptime("2018-03-06 00:00:00", "%Y-%m-%d %H:%M:%S")
#    end_time = datetime.now()
    time_width = 3600 * 200
    compute_indicator = ComputeIndicator(instrument, time_width, base_time)

    while base_time < end_time:
        try:
#            base_time = base_time + timedelta(seconds=1)
#            base_time = base_time + timedelta(minutes=5)
            base_time = base_time + timedelta(minutes=20)
            span = "1h"
            compute_indicator.computeInsertIndicator(base_time, span)
        except Exception as e:
            print e.args
            print traceback.format_exc()

