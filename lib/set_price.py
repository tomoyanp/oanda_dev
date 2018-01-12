# coding: utf-8

##############################################################
# 
# 1) initPrice()
#     => start time(now - time_width)
#     => select table
# 2) addPrice()
#     => getBaseTime() from main algorithm thread
#     => select 1 record where insert_time = getBaseTime().value
#
# *** caution ***
#  It's may exists brank time between initPrice and addPrice
#
##############################################################
