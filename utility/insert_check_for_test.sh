source /home/tomoyan/virtualenv/.python2.7/bin/activate
nohup python /home/tomoyan/staging/oanda_dev/utility/check_insert_price.py "GBP_JPY" > /dev/null &
nohup python /home/tomoyan/staging/oanda_dev/utility/check_insert_price.py "USD_JPY" > /dev/null &
