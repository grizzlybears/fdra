# -*- coding: utf-8 -*-
from datetime import date
from datetime import datetime

import copy

import xlrd
from xlrd import book
from xlrd import sheet

from  operator import  attrgetter

import sqlite3

import dao
from   dao import db_operator

DAILY_REPORT_SHEET_NAME = '客户交易结算日报'
REPORT_TITLE =   "客户交易结算日报(逐日盯市)"

# 期货成交汇总 的搜寻开始位置
TRADE_RECORD_HEADER_COL = 0
TRADE_RECORD_HEADER_ROW = 18

# 交易日 位置
T_DAY_COL = 7
T_DAY_ROW = 4

# 期货持仓汇总 的开始位置 -- '合约'格子
POS_RECORD_HEADER_COL = 0

# 成交汇总记录
class TradeAggreRecord:

    #成交序列号
    trade_seq = 0

    #成交时刻 YYYY-MM-DD hh:mm:ss
    trade_at = ""

    #合约
    contract = ""

    #标的品种
    target = ""
    
    #买/卖  取值必须是'买' or '卖'
    b_or_s = ""

    #成交价 float 
    price = 0.0

    #手数
    volume = 0

    #成交金额 float
    ammount = 0.0

    #开/平  取值必须是'开/平'
    offset = ""

    #手续费 float 
    trade_fee = 0.0

    #平仓盈亏 float
    profit = 0.0

    #内部使用
    sub_seq = 0

    def dump(self, indent = "  "):
        print("%s %s(%s) %s %s %d手 价=%f 金额=%d 平盈亏=%f 费=%f" % ( indent 
                , self.contract
                , self.target
                , self.offset 
                , self.b_or_s 
                , self.volume
                , self.price
                , self.ammount
                , self.profit 
                , self.trade_fee 
                ))

    def __repr__(self):
        s = "%s %s %s 价=%f  费=%f  ( %s - %d @%s)" % ( 
                self.contract
                , self.offset 
                , self.b_or_s 
                , self.price
                , self.trade_fee 
                , self.trade_seq, self.sub_seq , self.trade_at 
                )
        return s

    def dump2(self, indent = "  "):
        print("%s %s %s %s 价=%f  费=%f  ( %s - %d @%s)" % ( indent 
                , self.contract
                , self.offset 
                , self.b_or_s 
                , self.price
                , self.trade_fee 
                , self.trade_seq, self.sub_seq , self.trade_at 
                ))

    def save_to_db(self, dbcur, t_day, record_no):
        dbcur.execute( '''insert into  TradeAggreRecord(t_day,record_no
                , trade_seq , trade_at
                , contract, target, offset, b_or_s
                , volume, price, ammount 
                , profit, trade_fee ) 
            values (?, ?
                 , ?, ?
                 , ?, ?, ?, ?
                 , ?, ?, ?
                 , ?, ?)'''
                , ( t_day , record_no
                    , self.trade_seq , self.trade_at
                    , self.contract, self.target, self.offset, self.b_or_s 
                    , self.volume , self.price, self.ammount 
                    , self.profit , self.trade_fee 
                  )
                )


#持仓汇总
class PositionAggreRecord:
    #合约
    contract = ""

    #标的品种
    target = ""
    
    #买/卖  取值必须是'买' or '卖'
    b_or_s = ""

    #手数
    volume = 0

    #成交均价 float 
    avg_price = 0.0

    #昨结算价 float
    prev_settle_price = 0.0
 
    #今结算价 float
    today_settle_price = 0.0

    #持仓盈亏 float
    profit = 0.0

    def dump(self, indent = "  "):
        print("%s %s (%s) %s %d手 均价=%f 昨=%f 今=%f 盈亏=%f"  % ( indent
                , self.contract
                , self.target
                , self.b_or_s 
                , self.volume
                , self.avg_price
                , self.prev_settle_price
                , self.today_settle_price
                , self.profit 
                ))

    def save_to_db(self, dbcur, t_day, record_no):
        dbcur.execute( '''insert into  PositionAggreRecord(t_day,record_no
                , contract, target, b_or_s, volume, avg_price
                , prev_settle_price, today_settle_price, profit ) 
            values (?, ?
                 , ?, ?, ?, ?, ?
                 , ?, ?, ?)'''
                , ( t_day , record_no
                    , self.contract, self.target, self.b_or_s , self.volume , self.avg_price
                    , self.prev_settle_price , self.today_settle_price , self.profit 
                  )
                )



# 单个日报文件的解析结果
class SingleFileResult:
    #交易日 date
    T_day = "" 

    #当日盈亏(逐日盯市) float
    profit = 0.0

    #当日手续费 float
    fee = 0.0

    #当日结存 float
    balance = 0.0

    #前日结存 float
    prev_balance = 0.0

    #保证金占用 float
    margin = 0.0

    #成交汇总，数组
    aggregated_tr_arr = []

    #持仓汇总， 数组
    aggregated_pos_arr = []

    def __init__(self, t_day = None):
        if ( t_day is None ):
            raise Exception( "必须指定'交易日'" )
        else:
            self.T_day = t_day

    #校验解析结果 
    def verify(self):
        flat_profit = 0.0
        fee =0.0
        for tr in self.aggregated_tr_arr:
            fee = fee + tr.trade_fee 
            if ('平' == tr.offset):
                flat_profit = flat_profit + tr.profit 

        pos_profit = 0.0
        for pos in self.aggregated_pos_arr:
            pos_profit = pos_profit + pos.profit 

        if ( abs( fee - self.fee) > 0.0001 ):
            #raise Exception( "%s: 当日手续费=%f,  成交手续费之和=%f" % (self.T_day,  self.fee, fee))
            print("%s: 当日手续费=%f,  成交手续费之和=%f" % (self.T_day,  self.fee, fee))

        profit = flat_profit + pos_profit 
        if ( abs( profit - self.profit) > 0.0001 ):
            raise Exception("%s: 当日盈亏=%f,  平盈亏之和=%f , 仓盈亏之和=%f" % ( self.T_day, self.profit , flat_profit, pos_profit))

    def dump(self):
        print("==== %s ===" % self.T_day)

        print("成交汇总:")
        for tr in self.aggregated_tr_arr:
            tr.dump("    ")

        print("持仓汇总")
        for pos in self.aggregated_pos_arr:
            pos.dump("    ")
        
        print("交易日 %s 上日结存=%f 盈亏=%f 手续费=%f 当日结存=%f 保证金占用=%f" % (
                self.T_day
                , self.prev_balance 
                , self.profit
                , self.fee
                , self.balance 
                , self.margin
                ))

    def save_to_db(self, conn):

        cur = conn.cursor()

        cur.execute( "select count(*) from DailyReport where t_day=?", (self.T_day, ) )
        rownum = cur.fetchone()[0]

        if ( rownum > 0):
            print("%s already exsists in DB, pass." % ( self.T_day, ))
            return 

        cur.execute( '''insert into DailyReport(t_day, profit, fee, balance, prev_balance, margin) 
                values (?, ?, ?, ?, ?, ?)'''
                , (self.T_day , self.profit , self.fee, self.balance, self.prev_balance, self.margin )
                )

        record_no = 0
        for tr in self.aggregated_tr_arr:
            tr.save_to_db(cur, self.T_day, record_no )
            record_no = record_no + 1
        
        record_no = 0
        for pos in self.aggregated_pos_arr:
            pos.save_to_db(cur, self.T_day, record_no )
            record_no = record_no + 1

        conn.execute( "drop table if exists temp.t")
        
        sql = '''
create table temp.t as 
    select t_day, target, sum(profit) as s  from TradeAggreRecord r
       where r.t_day = ?    and r.offset='平'
       group by t_day, r.target
           '''
        conn.execute( sql, ( self.T_day,  ) )

        sql = '''
insert into  temp.t  
    select t_day, target, sum(profit) as s from PositionAggreRecord r
       where r.t_day = ?
       group by t_day,r.target
           '''
        conn.execute( sql, ( self.T_day,  ) )


        sql = '''
insert into DailyProfitByTraget(t_day,target, profit,fee, volume, pos_vol)
select t2.t_day, t2.target,t2.profit, f.fee, f.vol , pos.vol
from 
(
  select t_day, target, sum(s) as profit
  from temp.t
  group by t_day, target
) t2
left join (
  select t_day, target, sum(trade_fee) as fee, sum(volume) as vol
  from  TradeAggreRecord
  where t_day= ?
  group by t_day, target ) f
on (t2.t_day = f.t_day and t2.target = f.target )
left join (
  select t_day, target, ifnull( sum(volume), 0)  as vol
  from PositionAggreRecord
  where t_day= ?
  group by t_day, target ) pos
on (t2.t_day = pos.t_day and t2.target = pos.target )
        '''
        conn.execute( sql, ( self.T_day,self.T_day,  ) )
        
        conn.execute( "drop table temp.t")
        
        db_operator.check_posi_balance( self.T_day )
        #####end of 'save_to_db' !

# 根据'合约'获得其'标的品种'
# 失败则返回 None
def get_target_from_contract( contract):
    if ( contract is None):
        return None

    l = len(contract)
    if ( l < 5 ):
        return None

    target = ""
    for walker in contract:
        if ( walker.isalpha()):
            target =  target +  walker
        else:
            break
     
    if ("" == target):
        return None

    return target 


class SimpleTwoLegs:
    leg1   = ""
    leg2   = ""
    target = ""
  
    def __repr__(self):
        s = "%s %s - %s" % ( 
                self.target
                , self.leg1
                , self.leg2
                )
        return s
   
    # to be a 'key' in 'dict', just implement __hash__ and __eq__
    def __hash__(self):
            return hash((self.leg1, self.leg2, self.target))



    def __eq__(self, other):
        return (self.leg1 == other.leg1) and \
            (self.leg2 == other.leg2) and    \
            (self.target == other.target )


class SimpleTwoLegsTr:
    leg1_dir = 0  # 1:买，-1:卖
    leg1_tr  = None 
    leg2_tr  = None 

class SimpleTwoLegsTrArr:
    stl_arr = dict() # SimpleTwoLegs => SimpleTowLegsTr[]

    #def __init__(self, tr_arr):

    def add_stl_pair(self, stl, stl_tr):
        #print("------------------")
        #print( stl) 
        #print( self.stl_arr) 

        if stl not in self.stl_arr.keys():
            self.stl_arr[stl] = []
        #    print( "new comer:  %s " %  stl)
        #else:
        #    print( "exists :  %s" % stl )
        #    
        self.stl_arr[stl].append(stl_tr )

    def dump(self, indent): 
        for he in list(self.stl_arr.keys()):
            print(" %s - %s" % ( he.leg1, he.leg2))

            stl_trs = self.stl_arr[he]
            
            balance = 0
            gross = 0
            fee = 0

            for p in stl_trs:
                p.leg1_tr.dump2(indent)
                p.leg2_tr.dump2(indent)
                balance = balance + p.leg1_dir 

                fee = fee + p.leg1_tr.trade_fee + p.leg2_tr.trade_fee

                if ( 1 ==  p.leg1_dir ):
                    gross = gross + p.leg2_tr.ammount - p.leg1_tr.ammount
                else:
                    gross = gross + p.leg1_tr.ammount - p.leg2_tr.ammount

                print("%s %d,  毛 %d,  净 %d " % (indent, balance, gross, gross - fee))

            print("")

class TrScannerForSimple2L:
    tr_arr = [] 
    hedged_tr = SimpleTwoLegsTrArr()
  
    unhedged_arr = dict() # contract =>  'TradeAggreRecord arr'

    def __init__(self, tr_arr):
        self.tr_arr = tr_arr

    def dump(self):
        # 已对冲成交
        print(" ===== 已对冲成交 start ===== ")

        self.dump_hedged()
        print(" ===== 已对冲成交 end ===== ")


        # 未对冲成交
        print("")
        print("")
        print("")
        print(" ===== 未对冲成交 start !!! === ")
        self.dump_unhedged()
        print(" ===== 未对冲成交 end === ")

    def dump_hedged(self):
        self.hedged_tr.dump("    ")

    def dump_unhedged(self):
        for k,v in self.unhedged_arr.items():
            for tr in v:
                tr.dump("    ");

    def scan(self):
        for tr in self.tr_arr:
            if tr.volume == 1:
                self.process_1_tr( copy.copy(tr))
            else:
                #人为拆分为多条vol = 1 的记录
                i = 1
                while i <= tr.volume :
                    dupped = copy.deepcopy(tr)
                    dupped.volume = 1
                    dupped.sub_seq = i
                    dupped.ammount = tr.ammount / tr.volume 
                    self.process_1_tr(dupped)
                    i = i+1

    
    def process_1_tr ( self, tr ):

        #合约
        contract = tr.contract

        #品种
        target = tr.target

        if contract in self.unhedged_arr:
            #有未对冲的该合约
            #因为成交是确实发生的，这里没有必要去人为地‘平掉’
            #无条件记录下即可
            self.unhedged_arr[contract].append( tr)
        else:
            #我们试图为其‘对冲’
            got_hedged = False
            for unh_contra in self.unhedged_arr.keys():

                #品种不同，我们认为不能对冲
                if  get_target_from_contract(unh_contra ) != tr.target:
                    continue

                #存在同品种的未对冲成交
                unh_trs = self.unhedged_arr[unh_contra]

                #我们找到一个同品种反方向的即认为其‘对冲’ ^_^
                for tr_walker in unh_trs:
                    if tr_walker.b_or_s == tr.b_or_s:
                        continue

                    #‘对冲’了 
                    got_hedged = True
                    he_key = SimpleTwoLegs()
                    if ( contract < tr_walker.contract ):
                        leg1 = tr
                        leg2 = tr_walker
                    else:
                        leg2 = tr
                        leg1 = tr_walker

                    he_key.target = target
                    he_key.leg1 = leg1.contract 
                    he_key.leg2 = leg2.contract 

                    #print( "对冲的组合: %s" % he_key )
                    
                    he_value = SimpleTwoLegsTr()
                    he_value.leg1_tr = leg1
                    he_value.leg2_tr = leg2
                    if (leg1.b_or_s == '买'):
                        he_value.leg1_dir = 1
                    else:
                        he_value.leg1_dir = -1
                    
                    self.hedged_tr.add_stl_pair( he_key, he_value)

                    unh_trs.remove( tr_walker)

                    if ( len(unh_trs) == 0) :
                        del self.unhedged_arr[unh_contra]
                    break;

                if got_hedged:
                    break;

            if not got_hedged:
                self.unhedged_arr[contract] = []
                self.unhedged_arr[contract].append(tr)




 
# 检查'成交明细'数组
def scan_tr_detail(tr_arr): 
    
    scanner = TrScannerForSimple2L(tr_arr)
    scanner.scan()
    scanner.dump()
  


#解析一行 成交明细
def parse_1_tr_row( cells_in_row, rowno ):

    col_count = len(cells_in_row)
    if ( col_count < 12 ):
        print("第%d行只有%d列，不是有效的'成交明细'行 " % ( rowno, col_count))
        return None

    one_entry =  TradeAggreRecord()
 
    #成交序列号
    one_entry.trade_seq = cells_in_row[1].value

    #成交时刻 YYYY-MM-DD hh:mm:ss
    one_entry.trade_at = "%s %s" % (cells_in_row[11].value, cells_in_row[2].value )

    #合约
    one_entry.contract = cells_in_row[0].value

    #品种
    target = get_target_from_contract( one_entry.contract )
    if (target is None):
        print("第%d行 无法解析出‘标的品种’，不是有效的'成交汇总'行 " % ( rowno, ))
        return None

    one_entry.target = target

    #买/卖
    one_entry.b_or_s = cells_in_row[3].value.strip()
    if (one_entry.b_or_s not in ['买', '卖']): 
        print("第%d行 无法解析出‘买卖标志’，不是有效的'成交汇总'行 " % ( rowno, ))
        return None

    #开/平
    one_entry.offset = cells_in_row[8].value.strip()
    if (one_entry.offset not in ['开', '平']): 
        print("第%d行 无法解析出‘开平标志’ (%s)，不是有效的'成交汇总'行 " % ( rowno, one_entry.offset))
        return None

    #价
    one_entry.price = float(cells_in_row[5].value)

    #手数
    one_entry.volume = int( cells_in_row[6].value)
 
    #金额
    one_entry.ammount = float(cells_in_row[7].value)

    #平盈亏
    if ('平' == one_entry.offset):
        one_entry.profit = float (cells_in_row[10].value)

    #费
    one_entry.trade_fee = float (cells_in_row[9].value)

    return one_entry

#解析一行 持仓汇总
# 2018年底为止的格式，第一列是‘合约’
def parse_1_pos_row_until2018( cells_in_row, rowno ):

    col_count = len(cells_in_row)
    if ( col_count < 9 ):
        print("第%d行只有%d列，不是有效的'持仓汇总'行 " % ( rowno, col_count))
        return None

    one_entry =  PositionAggreRecord()

    #合约
    one_entry.contract = cells_in_row[0].value

    #品种
    target = get_target_from_contract( one_entry.contract )
    if (target is None):
        print("第%d行 无法解析出‘标的品种’，不是有效的'持仓汇总'行 " % ( rowno, ))
        return None

    one_entry.target = target

    #买/卖
    buy_vol_cell = cells_in_row[1]
    if ( buy_vol_cell.ctype == xlrd.XL_CELL_NUMBER  ):
        one_entry.b_or_s = '买'
        one_entry.volume = int(buy_vol_cell.value)
        one_entry.avg_price = float(cells_in_row[2].value)
    else:
        one_entry.b_or_s = '卖'
        one_entry.volume = int(cells_in_row[3].value)
        one_entry.avg_price = float(cells_in_row[4].value)

    #昨价
    one_entry.prev_settle_price = float(cells_in_row[5].value)
    #今价
    one_entry.today_settle_price = float(cells_in_row[6].value)

    #盈亏
    one_entry.profit = float (cells_in_row[7].value)

    return one_entry

#解析一行 持仓汇总
# 2019年开始的格式，第一列是‘日期’
def parse_1_pos_row_2019( cells_in_row, rowno ):

    col_count = len(cells_in_row)
    if ( col_count < 10 ):
        print("第%d行只有%d列，不是有效的'持仓汇总'行 " % ( rowno, col_count))
        return None

    one_entry =  PositionAggreRecord()

    #合约
    one_entry.contract = cells_in_row[1].value

    #品种
    target = get_target_from_contract( one_entry.contract )
    if (target is None):
        print("第%d行 无法解析出‘标的品种’，不是有效的'持仓汇总'行 " % ( rowno, ))
        return None

    one_entry.target = target

    #买/卖
    buy_vol_cell = cells_in_row[2]
    if ( buy_vol_cell.ctype == xlrd.XL_CELL_NUMBER  ):
        one_entry.b_or_s = '买'
        one_entry.volume = int(buy_vol_cell.value)
        one_entry.avg_price = float(cells_in_row[3].value)
    else:
        one_entry.b_or_s = '卖'
        one_entry.volume = int(cells_in_row[4].value)
        one_entry.avg_price = float(cells_in_row[5].value)

    #昨价
    one_entry.prev_settle_price = float(cells_in_row[6].value)
    #今价
    one_entry.today_settle_price = float(cells_in_row[7].value)

    #盈亏
    one_entry.profit = float (cells_in_row[8].value)

    return one_entry


# 解析'成交明细' sheet， 返回一个 TradeAggreRecord的数组
def parse_tr_details_sheet( file_path, sh):
    tr_arr = []

    #定位'成交明细'格子
    row_walker = 0 
    found = False
    while row_walker < sh.nrows:
        if ('成交明细' ==  sh.cell_value(colx = 0 , rowx = row_walker)):
            found = True
            break;
        row_walker = row_walker +1
   
    if  not found :
        raise Exception (" 找不到'成交明细'格子" % (file_path, ) )

    row_walker = row_walker + 2
    col0 = sh.cell_value (colx = 0 , rowx =  row_walker)
    while ( '合计' !=  col0): 
        #print "processing row %d" % ( row_walker, )
        one_tr_entry = parse_1_tr_row( sh.row( row_walker), row_walker )

        if ( one_tr_entry is not None):
            #one_tr_entry.dump()
            tr_arr.append( one_tr_entry)

        row_walker = row_walker + 1
        col0 = sh.cell_value (colx = 0 , rowx =  row_walker)

    # 法克！美尔雅的日报里，‘实际成交日期’永远等于‘交易日’
    # 只能用‘成交序列号’先排一下
    tr_arr.sort( key = attrgetter('trade_seq'))

    return tr_arr


# 解析单个日报文件
# 返回一个 SingleFileResult
def parse_single_file(file_path ):
    book = xlrd.open_workbook(file_path)
    
    sheet_count = book.nsheets
    if ( sheet_count < 1):
        raise Exception( "%s has no sheet!" % (file_path, ) )
    
    # 获得第一个sheet
    sh = book.sheet_by_index(0)
    if ( sh.name != DAILY_REPORT_SHEET_NAME ):
        raise Exception( "%s 的第一个sheet不是 '%s'" % (file_path,DAILY_REPORT_SHEET_NAME ) )
   
    # 确认是'逐日盯市'
    title = sh.cell_value(colx=0 , rowx=1)
    if (REPORT_TITLE != title):
        raise Exception( "%s 的不是 '%s'" % (file_path,REPORT_TITLE ) )

    # 获得'成交明细' sheet
    sh_tr_details = book.sheet_by_name("成交明细")
    if (sh_tr_details  is None ):
        raise Exception( "%s 里找不到'成交明细'sheet" % (file_path) )

    # 获得交易日
    t_day_cv =  sh.cell_value( colx = T_DAY_COL, rowx = T_DAY_ROW )
    #print "Yes, T_day is %s" % ( t_day_cv, )
    t_day = datetime.strptime( t_day_cv , '%Y-%m-%d').date()

    result = SingleFileResult( t_day )
 
    # 定位'期货期权账户资金状况'
    row_walker =  7 
    found = False
    while row_walker < sh.nrows:
        header_balance =  sh.cell_value(colx = 0 , rowx = row_walker)
        if ('期货期权账户资金状况' ==  header_balance):
            found = True
            break
        row_walker = row_walker +1

    if not found:
        raise Exception ("%s 找不到'期货期权账户资金状况'" % (file_path, ) )
    
    base_row_num = row_walker 
    # 前日结存
    result.prev_balance = sh.cell_value( colx = 2, rowx = base_row_num + 1)

    # 当日盈亏
    result.profit = sh.cell_value( colx = 2, rowx = base_row_num + 3)

    # 当日手续费
    result.fee = sh.cell_value( colx = 2, rowx = base_row_num + 5)

    # 当日结存
    result.balance = sh.cell_value( colx = 2, rowx = base_row_num + 6)
 
    # 保证金占用
    result.margin = sh.cell_value( colx = 7, rowx = base_row_num + 6)

    # 准备处理 期货成交汇总
    row_walker =  TRADE_RECORD_HEADER_ROW
    found = False
    while row_walker < sh.nrows:
        header_cv =  sh.cell_value(colx = TRADE_RECORD_HEADER_COL , rowx = row_walker)
        if ('期货成交汇总' ==  header_cv):
            found = True
            break
        row_walker = row_walker +1

    if not found:
        print("%s 找不到'期货成交汇总'区域" % file_path )
        row_walker =  TRADE_RECORD_HEADER_ROW - 1  #we will '+3' before seek '持仓记录'
    else:    
        row_walker = 2 + row_walker 
        col0 = sh.cell_value (colx = TRADE_RECORD_HEADER_COL , rowx =  row_walker)
        while ( '合计' !=  col0):
            #print "processing row %d" % ( row_walker, )
            #one_tr_entry = parse_1_tr_row( sh.row( row_walker), row_walker )

            #if ( one_tr_entry is not None):
            #    #one_tr_entry.dump()
            #    result.aggregated_tr_arr.append( one_tr_entry)
            
            #
            #  之后会解析 '成交明细' sheet，这里一概跳过即可
            #
            row_walker = row_walker + 1
            col0 = sh.cell_value (colx = TRADE_RECORD_HEADER_COL , rowx =  row_walker)

    #准备处理 持仓记录
    row_walker = row_walker + 3
    header_cv =  sh.cell_value(colx = TRADE_RECORD_HEADER_COL , rowx = row_walker)
    if ('合约' !=  header_cv and  '日期'!= header_cv):
        print("row_walker: %d, header: %s" % (row_walker, header_cv)  )
        raise Exception ("%s 找不到'期货持仓汇总'区域" % (file_path, ) )
 
    row_walker = row_walker + 1
    col0 = sh.cell_value (colx = POS_RECORD_HEADER_COL , rowx =  row_walker)
    while ( '合计' !=  col0):
        #print "processing row %d" % ( row_walker, )

        if '合约' ==  header_cv:
            one_pos_entry = parse_1_pos_row_until2018( sh.row( row_walker), row_walker )
        else:
            one_pos_entry = parse_1_pos_row_2019( sh.row( row_walker), row_walker )


        if ( one_pos_entry is not None):
            #one_pos_entry.dump()
            result.aggregated_pos_arr.append( one_pos_entry)

        row_walker = row_walker + 1
        col0 = sh.cell_value (colx = POS_RECORD_HEADER_COL , rowx =  row_walker)

    # 成交明细
    result.aggregated_tr_arr =   parse_tr_details_sheet(file_path, sh_tr_details )

    result.verify()

    scan_tr_detail(result.aggregated_tr_arr)
    #result.dump()

    return  result

# save a 'SingleFileResult' to sqlite db
def save_report_to_db( parse_result ):
    conn = db_operator.get_db_conn()

    parse_result.save_to_db( conn)

    conn.commit()


