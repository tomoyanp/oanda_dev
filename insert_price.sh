nohup python insert_price.py "USD_JPY" > /dev/null &
sleep 10
nohup python insert_price.py "GBP_JPY" > /dev/null &
sleep 10
nohup python check_insert_price.py "GBP_JPY" > /dev/null &
sleep 10
nohup python check_insert_price.py "USD_JPY" > /dev/null &
