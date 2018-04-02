# coding: utf-8

import sys
import os
import traceback
import json

current_path = os.path.abspath(os.path.dirname(__file__))
current_path = current_path + "/.."
sys.path.append(current_path)
sys.path.append(current_path + "/trade_algorithm")
sys.path.append(current_path + "/obj")
sys.path.append(current_path + "/lib")

property_path = current_path + "/property"
config_path = current_path + "/config"

from trade_wrapper import TradeWrapper
from datetime import datetime, timedelta
from send_mail import SendMail
from common import decideMarket, sleepTransaction
from expantion_algo_cython import ExpantionAlgoCython
import time
from logging import getLogger, FileHandler, DEBUG


expantion_algo = ExpantionAlgoCython()
