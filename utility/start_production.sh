source /home/tomoyan/virtualenv/.python2.7/bin/activate
source /home/tomoyan/python-2.7-env/bin/activate
nohup python /home/tomoyan/staging/oanda_dev/main.py "GBP_JPY" "demo" "multi_evolv" "multi_evolv_test" > /dev/null &
nohup python /home/tomoyan/hayata/oanda_dev/main.py "GBP_JPY" "demo" "multi" "multi_master" > /dev/null &
