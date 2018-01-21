source /home/tomoyan/python-2.7-env/bin/activate
nohup python /home/tomoyan/staging/oanda_dev/insert_wma.py "USD_JPY" > /dev/null &
nohup python /home/tomoyan/staging/oanda_dev/insert_wma.py "GBP_JPY" > /dev/null &
