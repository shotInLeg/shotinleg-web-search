#!/usr/bin/env python
# coding: utf8
import os
import sys

import crawler
import indexer


def main(args):
    # crawler.crawler(['http://stankin.ru/'], os.path.join(os.getcwd(), 'data'), depth=5)
    indexer.indexer(os.path.join(os.getcwd(), 'data', 'downloaded.json'), os.path.join(os.getcwd(), 'data2'))
    return 0


if __name__ == '__main__':
    ret_value = main(sys.argv)
    sys.exit(ret_value)

