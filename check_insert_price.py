#coding: utf-8

import commands
import time

status = commands.getoutput("ps -ef | grep python | grep insert_price | grep -v check | wc -l")

while True:
    if status == 1:
        pass
    else:
        commands.getoutput("/bin/bash restart_insert_price.sh")
    
    time.sleep(5)
