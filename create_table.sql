create table oanda_db.TRADE_HISTORY_TABLE (trade_id int not null,
instrument char(10) not null, order_time timestamp not null, order_price double not null, trade_flag char(5) not null,
stl_flag int, stl_time timestamp, stl_price double, mode char(15), PRIMARY KEY(order_time));

grant all privileges on 'oanda_db'.TRADE_HISTORY_TABLE to 'tomoyan';
use oanda_db

create user tomoyan@'localhost' identified by 'tomoyan180';
grant all privileges on 'oanda_db'.* to tomoyan@'localhost';
