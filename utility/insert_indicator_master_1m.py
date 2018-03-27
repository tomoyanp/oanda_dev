#coding: utf-8

## dummy
import os, sys
current_path = os.path.abspath(os.path.dirname(__file__))
current_path = current_path + "/.."
sys.path.append(current_path)
sys.path.append(current_path + "/lib")
config_name = "trendfollow_dummy"

import traceback
from compute_indicator import ComputeIndicator
from datetime import datetime, timedelta
import time
import logging

now = datetime.now()
now = now.strftime("%Y%m%d%H%M%S")
logfilename = "%s/log/indicator_%s.log" %(current_path, now)
logging.basicConfig(filename=logfilename, level=logging.INFO)


if __name__ == "__main__":
#    instrument = "GBP_JPY"
    args = sys.argv
    instrument = args[1]
    base_time = datetime.now()
#    base_time = base_time.strftime("%Y-%m-%d %H:00:00")
    base_time = base_time.strftime("%Y-%m-%d 00:00:00")
    base_time = datetime.strptime(base_time, "%Y-%m-%d %H:%M:%S")
    time_width = 60 * 200
    compute_indicator = ComputeIndicator(instrument, time_width, base_time)

    while True:
        try:
            now = datetime.now()
            base_time = base_time + timedelta(minutes=1)
            while now < base_time:
                time.sleep(1)
                now = datetime.now()
            
            span = "1m"
            compute_indicator.computeInsertIndicator(base_time, span)

        except Exception as e:
            logging.info(e.args)
            logging.info(traceback.format_exc())


