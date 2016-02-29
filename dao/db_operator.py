## -*- coding: utf-8 -*-
from datetime import date
from datetime import datetime

import sqlite3
import subprocess

DB_NAME='fdra.db'

 # 打开DB，并酌情建表，返回 sqlite3.Connection
def get_db_conn():
    conn = sqlite3.connect( DB_NAME)
    conn.text_factory = str

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

    # 冗余表， 每日按品种的盈亏以及成交手数统计
    sql = ''' CREATE TABLE IF NOT EXISTS DailyProfitByTraget (
       t_day     TEXT
       , target  TEXT
       , profit  NUMERIC    NULL
       , fee     NUMERIC    NULL
       , volume  integer    NULL
       , PRIMARY KEY(t_day, target)
       )
    '''
    conn.execute( sql)

    conn.commit()

    return conn 

def simplest_stat_by_target():
    sql = "select target,sum(profit) - sum(fee) , sum(volume) " \
         + "  from DailyProfitByTraget " \
         + "  group by target order by 2 desc " 
    cmd = "sqlite3 %s '%s'" % ( DB_NAME, sql)
    subprocess.call(cmd, shell=True)

def show_total():
    sql = "select sum(profit) - sum(fee), sum(volume) " \
         + "  from DailyProfitByTraget " 
    cmd = "sqlite3 %s '%s'" % ( DB_NAME, sql)
    subprocess.call(cmd, shell=True)

def lastday_stat_by_target():
    sql = "select target,sum(profit) - sum(fee) , sum(volume) " \
         + "  from DailyProfitByTraget " \
         + "  where t_day = (select max(t_day) from DailyReport)" \
         + "  group by target order by 2 desc " 
    cmd = "sqlite3 %s '%s'" % ( DB_NAME, sql)
    subprocess.call(cmd, shell=True)

def lastday_total():
    sql = "select sum(profit) - sum(fee), sum(volume) " \
         + "  from DailyProfitByTraget "  \
         + "  where t_day = (select max(t_day) from DailyReport)"

    cmd = "sqlite3 %s '%s'" % ( DB_NAME, sql)
    subprocess.call(cmd, shell=True)


