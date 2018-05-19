source /home/tomoyan/python-2.7-env/bin/activate 
nohup python /home/tomoyan/staging/oanda_dev/main.py "GBP_JPY" "production" "multi" "multi_master" > /dev/null &
nohup python /home/tomoyan/hayata/oanda_dev/main.py "GBP_JPY" "demo" "expantion" "expantion_hayata" > /dev/null &
