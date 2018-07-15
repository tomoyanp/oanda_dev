source /home/tomoyan/python-2.7-env/bin/activate 
source /home/tomoyan/virtualenv/.python2.7/bin/activate
#nohup python /home/tomoyan/staging/oanda_dev/main.py "GBP_JPY" "production" "multi" "multi_master" > /dev/null &
#nohup python /home/tomoyan/hayata/oanda_dev/main.py "GBP_JPY" "production" "multi" "multi_master" > /dev/null &
#nohup python /home/tomoyan/staging/oanda_dev//main.py "GBP_JPY" "production" "volatility" "volatility_master" > /dev/null &
#nohup python /home/tomoyan/hayata/oanda_dev/main.py "GBP_JPY" "demo" "volatility" "volatility_master" > /dev/null &
nohup python /home/tomoyan/staging/oanda_dev/main.py "GBP_JPY" "demo" "multi" "multi_test" > /dev/null &
nohup python /home/tomoyan/hayata/oanda_dev/main.py "GBP_JPY" "demo" "multi" "multi_test" > /dev/null &
