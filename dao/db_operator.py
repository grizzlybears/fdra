## -*- coding: utf-8 -*-
from datetime import date
from datetime import datetime

import sqlite3


DB_NAME='fdra.db'

 # 打开DB，并酌情建表，返回 sqlite3.Connection
def get_db_conn():
    conn = sqlite3.connect( DB_NAME)

    sql = ''' CREATE TABLE IF NOT EXISTS DailyReport (
       t_day     TEXT
       , profit  NUMERIC
       , fee     NUMERIC
       , balance NUMERIC
       , prev_balance NUMERIC
       , PRIMARY KEY( t_day)
       )
    '''
    conn.execute( sql)

    sql = ''' CREATE TABLE IF NOT EXISTS TradeAggreRecord (
       t_day     TEXT
       , record_no integer
       , contract  TEXT
       , target    TEXT
       , b_or_s    TEXT
       , price     NUMERIC
       , volume    INTERGER
       , ammount   NUMERIC
       , offset    TEXT
       , trade_fee   NUMERIC
       , profit      NUMERIC    NULL
       , PRIMARY KEY(t_day, record_no)
       , FOREIGN KEY(t_day) references DailyReport(t_day) on delete cascade
       )
    '''
    conn.execute( sql)

    sql = ''' CREATE TABLE IF NOT EXISTS PositionAggreRecord (
       t_day     TEXT
       , record_no integer
       , contract  TEXT
       , target    TEXT
       , b_or_s    TEXT
       , volume    INTERGER
       , avg_price     NUMERIC
       , prev_settle_price  NUMERIC
       , today_settle_price NUMERIC
       , profit      NUMERIC    NULL
       , PRIMARY KEY(t_day, record_no)
       , FOREIGN KEY(t_day) references DailyReport(t_day) on delete cascade
       )
    '''
    conn.execute( sql)

    # 冗余表， 每日按品种的盈亏统计
    sql = ''' CREATE TABLE IF NOT EXISTS DailyProfitByTraget (
       t_day     TEXT
       , target    TEXT
       , volume    INTERGER
       , flat_profit  NUMERIC
       , pos_profit   NUMERIC
       , profit      NUMERIC    NULL
       , PRIMARY KEY(t_day, target)
       )
    '''
    conn.execute( sql)


    conn.commit()


    return conn 
