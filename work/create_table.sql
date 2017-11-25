create table oanda_db.TRADE_HISTORY_TABLE (trade_id int not null,
instrument char(10) not null, order_time timestamp not null, order_price double not null, trade_flag char(5) not null,
stl_flag int, stl_time timestamp, stl_price double, mode char(15), PRIMARY KEY(order_time));

grant all privileges on 'oanda_db'.TRADE_HISTORY_TABLE to 'tomoyan';
use oanda_db

create user tomoyan@'localhost' identified by 'tomoyan180';
grant all privileges on 'oanda_db'.* to tomoyan@'localhost';

  mysql> select * from TEST_TABLE
      -> ;
  +---------+----------+
  | test_id | test_val |
  +---------+----------+
  |       1 | aaa      |
  |       1 | aaa      |
  |       2 | bbb      |
  |       2 | bbb      |
  |       3 | ccc      |
  |       3 | ccc      |
  +---------+----------+
  6 rows in set (0.00 sec)


  create table TEST_TABLE(test_id int, test_val char(5));
  mysqldump -u user -t DB名 テーブル名A テーブル名B > dump.sql
  mysqldump -u root -t oanda_db TEST_TABLE > dump.sql
  テーブルドロップ
  再作成（ユニークキー付与）

  mysqldump -u root -p oanda_db -t -c --skip-extended-insert TEST_TABLE > dump.sqlmysql -u root oanda_db < dump.sql
  create table TEST_TABLE(test_id int unique key, test_val char(5));


  create table TEST_TABLE(id int auto_increment not null primary key, test_id int, test_val char(5));
  insert into TEST_TABLE(test_id, test_val) values(1, 'aaa');
  insert into TEST_TABLE(test_id, test_val) values(2, 'bbb');
  insert into TEST_TABLE(test_id, test_val) values(3, 'ccc');

  重複しているレコードを抽出する
  select * from TEST_TABLE group by test_id having count(*) >= 2;

  mysql> alter table TEST_TABLE add unique unique_index(test_id);
  ERROR 1062 (23000): Duplicate entry '1' for key 'unique_index'


  delete TEST_TABLE where id=(select id from TEST_TABLE group by test_id having count(*) >= 2);

  delete TEST_TABLE where id in (select id from TEST_TABLE group by test_id having count(*) >= 2);


  ↓で重複したデータ消せた
  delete from USD_JPY_TABLE where id in (select id from (select id from USD_JPY_TABLE group by insert_time having count(*) >= 2 and insert_time > '2017-11-11 18:00:00' and insert_time < '2017-11-11 20:00:00') as tmp);
  delete from TEST_TABLE where id in (select id from (select id from TEST_TABLE group by test_id having count(*) >= 2) as tmp);
  alter table TEST_TABLE add unique(test_id);

ALTER TABLE GBP_JPY RENAME to GBP_JPY_TABLE;
ALTER TABLE USD_JPY RENAME to USD_JPY_TABLE;
grant all privileges on 'oanda_db'.GBP_JPY_TABLE to 'tomoyan';
grant all privileges on 'oanda_db'.USD_JPY_TABLE to 'tomoyan';
ALTER TABLE GBP_JPY_TABLE ADD INDEX time_index(insert_time)
ALTER TABLE USD_JPY_TABLE ADD INDEX time_index(insert_time)
