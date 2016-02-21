# -*- coding: utf-8 -*-
from datetime import date
from datetime import datetime

import xlrd
from xlrd import book
from xlrd import sheet

DAILY_REPORT_SHEET_NAME = '客户交易结算日报'

# 期货成交汇总 的开始位置 -- '合约'格子
TRADE_RECORD_HEADER_COL = 0
TRADE_RECORD_HEADER_ROW = 22

# 交易日 位置
T_DAY_COL = 7
T_DAY_ROW = 4


# 单个日报文件的解析结果
class SingleFileResult:
    #交易日
    T_day = "" 

    def __init__(self, t_day = None):
        if ( t_day is None ):
            raise Exception( "必须指定'交易日'" )
        else:
            self.T_day = t_day


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
 
    # 获得交易日
    t_day_cv =  sh.cell_value( colx = T_DAY_COL, rowx = T_DAY_ROW )
    #print "Yes, T_day is %s" % ( t_day_cv, )
    t_day = datetime.strptime( t_day_cv , '%Y-%m-%d').date()

    result = SingleFileResult( t_day )

    # 准备处理 期货成交汇总
    tr_header_cv =  sh.cell_value(colx = TRADE_RECORD_HEADER_COL , rowx = TRADE_RECORD_HEADER_ROW)
    if ('合约' !=  tr_header_cv):
        raise Exception ("%s 找不到'期货成交汇总'区域" % (file_path, ) )

    return  result
    
