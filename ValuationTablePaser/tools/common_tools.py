# !/usr/bin/env python
# -*- coding: utf-8 -*-

import xlrd, re
from xlrd import xldate_as_tuple
import datetime


# 抛出异常的时候使用默认值
def float_converter(string):
    if isinstance(string, str):
        string = string.replace(',', '')
        string = string.replace('(', '')
        string = string.replace(')', '')
        string = string.strip()
        if string.endswith("%"):
            return float(string[:-1]) * 0.01
        else:
            return float(string)
    return float(string)


def unsafe_float_converter(string):
    if string:
        return float_converter(string)
    return 0


def default_converter(row, column):
    return float_converter(row[column])


def date_converter(value):
    if isinstance(value, xlrd.sheet.Cell):
        if value.ctype == 3:
            return datetime.datetime(*xldate_as_tuple(value.value, 0)).strftime("%Y%m%d")
        elif value.ctype == 2:
            value = value.value
            return str(int(value))
        elif value.ctype == 1:
            value = value.value
            value = str(value).replace("/", "-")
            value = value.replace('年', ' ')
            value = value.replace('月', ' ')
            value = value.replace('-', ' ')
            value = value.replace('日', '')
            value = value.strip()
            return "".join(map(lambda x: "%02d" % int(x), value.split()))
    else:
        # 2019年06月01日
        value = str(value).replace('年', ' ')
        value = value.replace('月', ' ')
        value = value.replace('-', ' ')
        value = value.replace('日', '')
        value = value.replace('/', '')
        value = value.strip()
        value = value[:10]
        values = value.split(' ')
        return "".join(map(lambda x: "%02d" % x, map(int, values)))


def int_34(s):
    maps = "0123456789ABCDEFGHJKLMNPQRSTUVWXYZ"
    result = 0
    base = len(maps)
    for index, c in enumerate(s.upper()[::-1]):
        i = maps.index(c)
        result += (base ** index) * i
    return result


def decode_option_code(code="2Y0T51"):
    match = re.match(r'([0-9A-Z]{2})([0-9A-Z]{2})(\d{2})', code)
    if match is not None:
        # etf期权
        x = ("%03d" % int_34(match.group(1)))[:3]
        y = ("%03d" % int_34(match.group(2)))[:3]
        z = int(match.group(3))
        return "%s%s%02d" % (x, y, z)
    else:
        return None


if __name__ == '__main__':
    pass
