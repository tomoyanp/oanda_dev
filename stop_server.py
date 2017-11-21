# coding: utf-8

import sys
import os
import traceback
import json
import commands

# 実行スクリプトのパスを取得して、追加
current_path = os.path.abspath(os.path.dirname(__file__))
sys.path.append(current_path)

import time
import logging
now = datetime.now()
now = now.strftime("%Y%m%d%H%M%S")
logfilename = "/var/log/oanda_dev/stop_service_%s.log" %(now)
logging.basicConfig(filename=logfilename, level=logging.INFO)

def exec_cmd(cmd):
    now = datetime.now()
    now = now.strftime("%Y%m%d%H%M%S")
    logging.info("### %s ===> %s" % (now, cmd))
    out = commands.getoutput(cmd)
    logging.info("%s" % (out))
    logging.info("==========================================")
    return out

# processが起動状態かどうか確認
# プロセスが存在しなければtrueを返す
def check_process(process):
    cmd = "ps -ef | grep %s | grep -v grep |wc -l"
    out = exec_cmd(cmd)
    process_numbers = int(out)
    flag = False
    if process_numbers == 0:
        flag = True

    return flag

def stop_service(process):
    cmd = "ps -ef |grep %s |grep -v grep" % process
    process_list = exec_cmd(cmd)

    for process in process_list:
        flag = True
        while flag:
            flag = False
            for i in range(0, len(process)):
                if pslist[i] == "":
                    flag = True
                    process.pop(i)
                    break

    pid_list = []
    for pid in process_list:
        pid_list.append(pid[1].strip())

    for pid in pid_list:
        cmd = "kill -9 %s" % pid
        exec_cmd(cmd)

    time.sleep(5)

    if checkprocess(process):
        pass
    else:
        raise ValueError("Cannot Stop Service at %s" % process)


def stop_daemon(daemon):
    cmd = "service %s stop"
    exec_cmd(cmd)
    time.sleep(5)

    if check_process(daemon):
        pass
    else:
        raise ValueError("Cannot Stop Service at %s" % process)


# python stop_service.py main.py
# python stop_sevice.py insert_price.py

if __name__ == '__main__':
    sendmail = SendMail("tomoyanpy@gmail.com", "tomoyanpy@softbank.ne.jp", property_path)

    try:
        # コマンドライン引数から、停止対象のプロセスを受け取る
        #args = sys.argv
        #process = args[1]
        #process = process.strip()

        process = "main.py"
        stop_service(process)

        process = "insert_price.py"
        stop_service(process)

        daemon = "mysqld"
        stop_daemon(daemon)

        # 一応、リブート前にメール通知
        message = "Complete Stop Service & daemon"
        sendmail.set_msg(message)
        sendmail.send_mail()

        cmd = "reboot"
        exec_cmd(cmd)

    except:
        message = traceback.format_exc()
        sendmail.set_msg(message)
        sendmail.send_mail()
