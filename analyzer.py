# -*- coding: utf-8 -*-
# 单个日报文件的解析结果
class SingleFileResult:
    #交易日
    T_day = "" 

    def __init__(self, t_day = None):
        if ( t_day is None ):
            raise Exception( "必须指定'交易日'" )
        else:
            self.T_day = t_day




