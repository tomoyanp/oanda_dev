source /home/tomoyan/python-2.7-env/bin/activate
nohup python /home/tomoyan/staging/oanda_dev/insert_price.py "USD_JPY" > /dev/null &
sleep 60
nohup python /home/tomoyan/staging/oanda_dev/insert_price.py "GBP_JPY" > /dev/null &
#sleep 60
#nohup python /home/tomoyan/staging/oanda_dev/main.py "USD_JPY" "production" "bollinger" "bollinger_master" > /dev/null &
#sleep 60
#nohup python /home/tomoyan/staging/oanda_dev/main.py "USD_JPY" "production" "startend" "startend_master" > /dev/null &
#nohup python /home/tomoyan/staging/oanda_dev/main.py "USD_JPY" "production" "timetrend" "timetrend_master" > timetrend.out &
