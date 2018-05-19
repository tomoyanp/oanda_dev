source /home/tomoyan/python-2.7-env/bin/activate 
nohup python /home/tomoyan/staging/oanda_dev/main.py "GBP_JPY" "demo" "multi" "multi_master" > /dev/null &
nohup python /home/tomoyan/staging/oanda_dev/main.py "USD_JPY" "demo" "trendreverse" "trendreverse_master" > /dev/null &
