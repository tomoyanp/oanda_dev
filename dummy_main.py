#coding: utf-8

## dummy
import os, sys
current_path = os.path.abspath(os.path.dirname(__file__))
sys.path.append(current_path)
sys.path.append(current_path + "/lib")
config_name = "trendfollow_dummy"

from compute_indicator import ComputeIndicator
from datetime import datetime, timedelta
import time

if __name__ == "__main__":
    instrument = "GBP_JPY"
    base_time = datetime.strptime("2017-02-10 00:00:00", "%Y-%m-%d %H:%M:%S")
    end_time = datetime.now()
    compute_indicator = ComputeIndicator(instrument, current_path, config_name, base_time)

    while base_time < end_time:
        try:
            base_time = base_time + timedelta(seconds=1)
            compute_indicator.computeInsertIndicator(base_time)

        except:
            pass
