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
       , margin  NUMERIC
       , PRIMARY KEY( t_day)
       )
    '''
    conn.execute( sql)

    sql = ''' CREATE TABLE IF NOT EXISTS TradeAggreRecord (
       t_day     TEXT
       , record_no integer
       , trade_seq integer
       , trade_at  TEXT
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

    # 冗余表， 每日按品种的盈亏，成交手数，持仓量统计
    sql = ''' CREATE TABLE IF NOT EXISTS DailyProfitByTraget (
       t_day     TEXT
       , target  TEXT
       , profit  NUMERIC    NULL
       , fee     NUMERIC    NULL
       , volume  integer    NULL
       , pos_vol integer    NULL
       , PRIMARY KEY(t_day, target)
       )
    '''
    conn.execute( sql)

    conn.commit()

    return conn 

def simplest_stat_by_target():
    sql = "select target,ifnull(sum(profit),0) - ifnull(sum(fee),0) , sum(volume) " \
         +      ", printf('%.2f', (total(profit) - total(fee)) /  sum(volume)  )" \
         + "  from DailyProfitByTraget " \
         + "  group by target order by 2 desc " 
    cmd = "sqlite3 %s '%s'" % ( DB_NAME, sql)
    subprocess.call([
            'sqlite3'
            , DB_NAME
            , sql
            ])


def show_total():
    sql = "select total(r.profit) - total(r.fee)  , t.v  " \
         + " , printf('%.2f', ( total(r.profit) - total(r.fee)) / t.v )" \
         + " from DailyReport r" \
         + " left join ( select  t_day , total(volume) as v from TradeAggreRecord  ) t on r.t_day = t.t_day"
    print "净盈亏|成交量|平均每手盈亏"
    subprocess.call([
            'sqlite3'
            , DB_NAME
            , sql
            ])


def lastday_stat_by_target():
    print "标的|净盈亏|成交量|持仓量|平均每手盈亏"
    sql = "select target, profit - ifnull(fee,0),  volume " \
         +      ", pos_vol " \
         +      ", printf('%.2f', ( profit - ifnull(fee,0))/volume) " \
         + "  from DailyProfitByTraget " \
         + "  where t_day = (select max(t_day) from DailyReport)" \
         + "  order by 2 desc " 
    subprocess.call([
            'sqlite3'
            , DB_NAME
            , sql
            ])


def lastday_total():
    print "盈亏|成交手续费|净盈亏|成交量|平均每手盈亏"
    sql = "select sum(profit),  sum(fee), sum(profit) - sum(fee), sum(volume) " \
         +      ", printf('%.2f', (sum(profit) - sum(fee)) /  sum(volume) )" \
         + "  from DailyProfitByTraget "  \
         + "  where t_day = (select max(t_day) from DailyReport)"

    subprocess.call([
            'sqlite3'
            , DB_NAME
            , sql
            ])

    print "当日结存|保证金占用|当日手续费"
    sql = "select sum(balance), sum(margin), sum(fee) " \
         + "  from  DailyReport "  \
         + "  where t_day = (select max(t_day) from DailyReport)"

    subprocess.call([
            'sqlite3'
            , DB_NAME
            , sql
            ])


def day_stat_by_target( t_day):
    print "标的|净盈亏|成交量|持仓量|平均每手盈亏"
    sql = "select target, profit - ifnull(fee,0), volume" \
         +      ", pos_vol " \
         +      ", printf('%.2f', ( profit - ifnull(fee,0))/volume) " \
         + "  from DailyProfitByTraget " \
         + "  where t_day = '%s'" % (t_day, )\
         + "  order by 2 desc "  
    #print "%s\n" % sql
    subprocess.call([
            'sqlite3'
            , DB_NAME
            , sql
            ])

def day_total( t_day ):
    print "盈亏|成交手续费|净盈亏|成交量|平均每手盈亏"
    sql = "select sum(profit),  sum(fee), sum(profit) - sum(fee), sum(volume) " \
         +      ", printf('%.2f', (total(profit) - total(fee)) /  sum(volume)  )" \
         + "  from DailyProfitByTraget "  \
         + "  where t_day = '%s'" % (t_day, )

    subprocess.call([
            'sqlite3'
            , DB_NAME
            , sql
            ])

    print "当日结存|保证金占用|当日手续费"
    sql = "select sum(balance), sum(margin),sum(fee) " \
         + "  from  DailyReport "  \
         + "  where t_day = '%s'" % (t_day, )

    subprocess.call([
            'sqlite3'
            , DB_NAME
            , sql
            ])

def month_stat_by_target( t_month):
    # DB中的 t_day 是 text型 ^_^
    range_stat_by_target( t_month + '-01' , t_month + '-31' )
 
def year_stat_by_target( t_year):
    # DB中的 t_day 是 text型 ^_^
    range_stat_by_target( t_year + '-01-01' , t_year + '-12-31' )
    
def month_total( t_month ):
    # DB中的 t_day 是 text型 ^_^
    range_total( t_month + '-01' , t_month + '-31' )
 
def year_total( t_year ):
    # DB中的 t_day 是 text型 ^_^
    range_total( t_year + '-01-01' , t_year + '-12-31' )
 
def range_stat_by_target( d_from, d_until):

    # DB中的 t_day 是 text型 ^_^
    sql = "select target, sum(profit - ifnull(fee,0)) , sum(volume) " \
         +      ", printf('%.2f', (total(profit) - total(fee)) /  sum(volume)  )" \
         + "  from DailyProfitByTraget " \
         + "  where t_day >= '%s'  and t_day <= '%s-31'" % (d_from, d_until)\
         + "  group by target order by 2 desc "  
    #print "%s\n" % sql
    subprocess.call([
            'sqlite3'
            , DB_NAME
            , sql
            ])

def range_total( d_from, d_until ): 
    
    sql = "select total(r.profit) - total(r.fee)  , t.v  " \
         + " , printf('%.2f', ( total(r.profit) - total(r.fee)) / t.v )" \
         + " from DailyReport r" \
         + " left join ( select  t_day , total(volume) as v from TradeAggreRecord where t_day >= '%s' and t_day <= '%s' ) t on r.t_day = t.t_day" % (d_from, d_until) \
         + " where r.t_day >= '%s' and r.t_day <= '%s' " % (d_from, d_until)

    print "净盈亏|成交量|平均每手盈亏"
    subprocess.call([
            'sqlite3'
            , DB_NAME
            , sql
            ])


def check_posi_balance( t_day ):
    sql = '''
        select p.target, ifnull( b.s, 0) - ifnull( s.s, 0)   as ba
        from 
        (
          select distinct target
          from PositionAggreRecord 
          where t_day =  '%s' 
          ) p
        left join 
        (
        select target, sum(volume) as s 
        from PositionAggreRecord 
        where t_day = '%s' and b_or_s='买'
        group by target
         ) b on ( p.target = b.target )
        left join 
        (
        select target, sum(volume) as s 
        from PositionAggreRecord 
        where t_day = '%s' and b_or_s='卖'
        group by target
         ) s on ( p.target = s.target )
        where ba <> 0 
    '''  
    sql = sql  % (t_day, t_day, t_day )
   
    subprocess.call([
            'sqlite3'
            , DB_NAME
            , sql
            ])

def daily_stat():
    sql = "select t_day,  ifnull(profit,0) - ifnull(fee,0) " \
         + "  from DailyReport "  \
         + "order by t_day asc" 

    subprocess.call([
            'sqlite3'
            , DB_NAME
            , sql
            ])

  
def daily_stat_sorted():
    sql = "select t_day,  ifnull(profit,0) - ifnull(fee,0) " \
         + "  from DailyReport "  \
         + "order by 2 asc" 

    subprocess.call([
            'sqlite3'
            , DB_NAME
            , sql
            ])

