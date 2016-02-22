# -*- coding: utf-8 -*-
from datetime import date
from datetime import datetime

import xlrd
from xlrd import book
from xlrd import sheet

DAILY_REPORT_SHEET_NAME = '客户交易结算日报'
REPORT_TITLE =   "客户交易结算日报(逐日盯市)"

# 期货成交汇总 的开始位置 -- '合约'格子
TRADE_RECORD_HEADER_COL = 0
TRADE_RECORD_HEADER_ROW = 22

# 交易日 位置
T_DAY_COL = 7
T_DAY_ROW = 4

# 期货持仓汇总 的开始位置 -- '合约'格子
POS_RECORD_HEADER_COL = 0

# 成交汇总记录
class TradeAggreRecord:
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

    def dump(self, indent = "  "):
        print "%s %s(%s) %s %s %d手 价=%f 金额=%d 平盈亏=%f 费=%f" % ( indent 
                , self.contract
                , self.target
                , self.offset 
                , self.b_or_s 
                , self.volume
                , self.price
                , self.ammount
                , self.profit 
                , self.trade_fee 
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
        print "%s %s (%s) %s %d手 均价=%f 昨=%f 今=%f 盈亏=%f"  % ( indent
                , self.contract
                , self.target
                , self.b_or_s 
                , self.volume
                , self.avg_price
                , self.prev_settle_price
                , self.today_settle_price
                , self.profit 
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

        ret = True
        if ( abs( fee - self.fee) > 0.0001 ):
           print "！！ 当日手续费=%f,  成交手续费之和=%f" % ( self.fee, fee)
           ret = False

        profit = flat_profit + pos_profit 
        if ( abs( profit - self.profit) > 0.0001 ):
           print "！！ 当日盈亏=%f,  平盈亏之和=%f , 仓盈亏之和=%f" % ( self.profit , flat_profit, pos_profit)
           ret = False

        return ret 

    def dump(self):
        print "==== %s ===" % self.T_day

        print "成交汇总:"
        for tr in self.aggregated_tr_arr:
            tr.dump("    ")

        print "持仓汇总"
        for pos in self.aggregated_tr_arr:
            pos.dump("    ")
        
        print "交易日 %s 上日结存=%f 盈亏=%f 手续费=%f 当日结存=%f" % (
                self.T_day
                , self.prev_balance 
                , self.profit
                , self.fee
                , self.balance )




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



#解析一行 成交汇总
def parse_1_tr_row( cells_in_row, rowno ):

    col_count = len(cells_in_row)
    if ( col_count < 9 ):
        print "第%d行只有%d列，不是有效的'成交汇总'行 " % ( rowno, col_count)
        return None

    one_entry =  TradeAggreRecord()

    #合约
    one_entry.contract = cells_in_row[0].value

    #品种
    target = get_target_from_contract( one_entry.contract )
    if (target is None):
        print "第%d行 无法解析出‘标的品种’，不是有效的'成交汇总'行 " % ( rowno, )
        return None

    one_entry.target = target

    #买/卖
    one_entry.b_or_s = cells_in_row[1].value.strip()
    if (one_entry.b_or_s not in ['买', '卖']): 
        print "第%d行 无法解析出‘买卖标志’，不是有效的'成交汇总'行 " % ( rowno, )
        return None

    #开/平
    one_entry.offset = cells_in_row[7].value.strip()
    if (one_entry.offset not in ['开', '平']): 
        print "第%d行 无法解析出‘开平标志’ (%s)，不是有效的'成交汇总'行 " % ( rowno, one_entry.offset)
        return None

    #价
    one_entry.price = float(cells_in_row[3].value)

    #手数
    one_entry.volume = int( cells_in_row[4].value)
 
    #金额
    one_entry.ammount = float(cells_in_row[5].value)

    #平盈亏
    if ('平' == one_entry.offset):
        one_entry.profit = float (cells_in_row[9].value)

    #费
    one_entry.trade_fee = float (cells_in_row[8].value)

    return one_entry

#解析一行 持仓汇总
def parse_1_pos_row( cells_in_row, rowno ):

    col_count = len(cells_in_row)
    if ( col_count < 9 ):
        print "第%d行只有%d列，不是有效的'持仓汇总'行 " % ( rowno, col_count)
        return None

    one_entry =  PositionAggreRecord()

    #合约
    one_entry.contract = cells_in_row[0].value

    #品种
    target = get_target_from_contract( one_entry.contract )
    if (target is None):
        print "第%d行 无法解析出‘标的品种’，不是有效的'持仓汇总'行 " % ( rowno, )
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

    # 获得交易日
    t_day_cv =  sh.cell_value( colx = T_DAY_COL, rowx = T_DAY_ROW )
    #print "Yes, T_day is %s" % ( t_day_cv, )
    t_day = datetime.strptime( t_day_cv , '%Y-%m-%d').date()

    result = SingleFileResult( t_day )

    # 前日结存
    result.prev_balance = sh.cell_value( colx = 2, rowx = 11)

    # 当日盈亏
    result.profit = sh.cell_value( colx = 2, rowx = 13)

    # 当日手续费
    result.fee = sh.cell_value( colx = 2, rowx = 15)

    # 当日结存
    result.balance = sh.cell_value( colx = 2, rowx = 16)

    # 准备处理 期货成交汇总
    header_cv =  sh.cell_value(colx = TRADE_RECORD_HEADER_COL , rowx = TRADE_RECORD_HEADER_ROW)
    if ('合约' !=  header_cv):
        raise Exception ("%s 找不到'期货成交汇总'区域" % (file_path, ) )
    
    row_walker = 1 + TRADE_RECORD_HEADER_ROW 
    col0 = sh.cell_value (colx = TRADE_RECORD_HEADER_COL , rowx =  row_walker)
    while ( '合计' !=  col0):
        #print "processing row %d" % ( row_walker, )
        one_tr_entry = parse_1_tr_row( sh.row( row_walker), row_walker )

        if ( one_tr_entry is not None):
            #one_tr_entry.dump()
            result.aggregated_tr_arr.append( one_tr_entry)

        row_walker = row_walker + 1
        col0 = sh.cell_value (colx = TRADE_RECORD_HEADER_COL , rowx =  row_walker)

    #准备处理 持仓记录
    row_walker = row_walker + 3
    header_cv =  sh.cell_value(colx = TRADE_RECORD_HEADER_COL , rowx = row_walker)
    if ('合约' !=  header_cv):
        raise Exception ("%s 找不到'期货持仓汇总'区域" % (file_path, ) )
 
    row_walker = row_walker + 1
    col0 = sh.cell_value (colx = POS_RECORD_HEADER_COL , rowx =  row_walker)
    while ( '合计' !=  col0):
        #print "processing row %d" % ( row_walker, )
        one_pos_entry = parse_1_pos_row( sh.row( row_walker), row_walker )

        if ( one_pos_entry is not None):
            #one_pos_entry.dump()
            result.aggregated_pos_arr.append( one_pos_entry)

        row_walker = row_walker + 1
        col0 = sh.cell_value (colx = POS_RECORD_HEADER_COL , rowx =  row_walker)

    if ( not result.verify()):
        return None

    return  result
    
