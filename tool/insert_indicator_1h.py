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
import time, logging

now = datetime.now()
now = now.strftime("%Y%m%d%H%M%S")
logfilename = "%s/log/indicator_%s.log" %(current_path, now)
logging.basicConfig(filename=logfilename, level=logging.INFO)

if __name__ == "__main__":
    instrument = "GBP_JPY"
    base_time = datetime.strptime("2018-03-09 18:00:00", "%Y-%m-%d %H:%M:%S")
#    base_time = datetime.strptime("2018-02-01 00:00:00", "%Y-%m-%d %H:%M:%S")
    end_time = datetime.strptime("2018-03-10 18:00:00", "%Y-%m-%d %H:%M:%S")
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
            logging.info(traceback.format_exc())

