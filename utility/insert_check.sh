source /home/tomoyan/python-2.7-env/bin/activate
nohup python /home/tomoyan/staging/oanda_dev/check_insert_price.py "USD_JPY" > /home/tomoyan/staging/oanda_dev/check_usd.txt &
nohup python /home/tomoyan/staging/oanda_dev/check_insert_price.py "GBP_JPY" > /home/tomoyan/staging/oanda_dev/check_gbp.txt &
nohup python /home/tomoyan/staging/oanda_dev/check_insert_price.py "NZD_JPY" > /home/tomoyan/staging/oanda_dev/check_nzd.txt &
