source /home/tomoyan/python-2.7-env/bin/activate
nohup python /home/tomoyan/staging/oanda_dev/utility/check_insert_price.py "GBP_JPY" > /dev/null &
nohup python /home/tomoyan/staging/oanda_dev/utility/check_insert_price.py "USD_JPY" > /dev/null &
