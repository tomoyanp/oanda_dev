nohup python insert_price.py "USD_JPY" > /dev/null &
nohup python insert_price.py "GBP_JPY" > /dev/null &
nohup python check_insert_price.py "GBP_JPY" > /dev/null &
nohup python check_insert_price.py "USD_JPY" > /dev/null &
