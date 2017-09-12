#coding: utf-8

import commands
import time
import send_mail


while True:
    status = commands.getoutput("ps -ef | grep python | grep main.py | grep -v grep | wc -l")
    if status == 1:
        pass
    else:
        commands.getoutput("/bin/bash restart_insert_price.sh")

    time.sleep(5)
