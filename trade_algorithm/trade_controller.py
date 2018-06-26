# coding: utf-8
####################################################
# Trade Decision
# if trade timing is between 14:00 - 04:00
# if upper and lower sigma value difference is smaller than 2 yen
# if current price is higher or lower than bollinger band 5m 3sigma
# if current_price is higher or lower than max(min) price last day
#
# Stop Loss Decision
# Same Method Above
#
# Take Profit Decision
# Special Trail mode
# if current profit is higher than 50Pips, 50Pips trail mode
# if current profit is higher than 100Pips, 30Pips trail mode
####################################################

from super_algo import SuperAlgo
from common import instrument_init, account_init
from datetime import datetime, timedelta
from logging import getLogger, FileHandler, DEBUG

class TradeContoller(SuperAlgo):
    def __init__(self, base_path, base_time):
        super(TradeContoller, self).__init__(base_path, base_time)
        self.debug_logger = getLogger("debug")
        self.result_logger = getLogger("result")
        self.scalping = Scalping(base_time, base_path)
        self.expantion = Scalping(base_time, base_path)
        self.volatility = Scalping(base_time, base_path)

    # decide trade entry timing
    def decideTradeController(self, base_time):
        trade_flag = "pass"
        try:
           trade_flag, priority, instrument, units, algorithm = self.scalping.decideTrade(base_time)
           trade_flag, priority, instrument, units, algorithm = self.expantion.decideTrade(base_time)
           trade_flag, priority, instrument, units, algorithm = self.volatility.decideTrade(base_time)

           if trade_flag != "pass" and self.order_flag:
               if priority > self.priority or trade_flag == self.order_kind:
                   pass
               else:
                   trade_flag = "pass"
                   self.result_logger.info("# execute all over the world")
    
            return trade_flag, instrument, units, algorithm
        except:
            raise

    # settlement logic
    def decideStlController(self, base_time):
        stl_flag = False
        try:
            if self.order_flag:
                if weekday == 5 and hour >= 5:
                    self.result_logger.info("# weekend stl logic")
                    stl_flag = True

                else:
                    stl_flag = self.scalping.decideStl(base_time, self.algorithm, self.order_price, self.order_kind)
                    stl_flag = self.expantion.decideStl(base_time, self.algorithm, self.order_price, self.order_kind)
                    stl_flag = self.volatility.decideStl(base_time, self.algorithm, self.order_price, self.order_kind)

            else:
                pass

            return stl_flag
        except:
            raise

