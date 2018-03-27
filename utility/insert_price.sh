source /home/tomoyan/python-2.7-env/bin/activate
nohup python /home/tomoyan/staging/oanda_dev/utility/insert_price.py "GBP_JPY" > /dev/null &
nohup python /home/tomoyan/staging/oanda_dev/utility/insert_indicator_master.py "GBP_JPY" > /dev/null &
nohup python /home/tomoyan/staging/oanda_dev/utility/insert_indicator_master_1m.py "GBP_JPY" > /dev/null &
