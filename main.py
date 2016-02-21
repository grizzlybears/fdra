#!/usr/bin/python2 -S
# -*- coding: utf-8 -*-
import sys
sys.setdefaultencoding("utf-8")
import site

import analyzer

def print_usage():
    print "Usage %s <日报文件>" % sys.argv[0]

def main():

    i = len(sys.argv)
    if ( i < 2 ):
        print_usage()
        return 1

    s = analyzer.parse_single_file( sys.argv[1]  )

    print "haha", s.T_day

    return 0


if __name__ == "__main__":
    r = main()
    sys.exit(r)


