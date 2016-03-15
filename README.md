Future Daily Report Analyzer
============================

简介
----
    期货日报分析工具(下称'fdra')是一个工具，用于分析 [中国期货市场监控中心](https://investorservice.cfmmc.com) 给出的日报。  

安装依赖
-------

###  Fedora:
   sudo yum install python-xlrd sqlite

###  Windows:
   to be done.

用法概要
-------
>fdra import    <日报文件>   解析导入逐日盯市日报文件
>
>fdra importdir <日报目录>   导入指定目录下所有逐日盯市日报文件
>
>fdra stat [lastday|YYYY-MM|YYYY-MM-DD]  显示按品种的盈亏统计
>
>fdra total      显示总盈亏

