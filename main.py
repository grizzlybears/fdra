#!/usr/bin/python2 -S
import sys
sys.setdefaultencoding("utf-8")
import site

import analyzer


def main():
    s = analyzer.SingleFileResult("aaa")

    print "haha", s.T_day


if __name__ == "__main__":
    main()



