source /home/tomoyan/python-2.7-env/bin/activate
nohup python /home/tomoyan/staging/oanda_dev/utility/insert_price.py "GBP_JPY" > /dev/null &
sleep 10
nohup python /home/tomoyan/staging/oanda_dev/utility/insert_price.py "USD_JPY" > /dev/null &
sleep 10
nohup python /home/tomoyan/staging/oanda_dev/utility/insert_multi_table.py "GBP_JPY" "production" > /dev/null & 
sleep 10
nohup python /home/tomoyan/staging/oanda_dev/utility/insert_multi_table.py "USD_JPY" "production" > /dev/null & 
