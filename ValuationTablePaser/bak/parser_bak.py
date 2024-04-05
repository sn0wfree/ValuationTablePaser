# coding = utf-8
#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re

from parsers.plugins.fund.valuation_table.utils import *
from constants import Direction, AssetType


# **date**
def find_date(rows: [[]], patterns):
    """
    >>> rows
    [
    ['TEST01_测试1号私募证券投资基金_资产估值表_20210301', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', ''],
    ['', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', ''],
    ['XX资产管理有限公司__测试1号私募证券投资基金__专用表', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', ''],
    ['日期：2021-03-01', '', '', '', '', '', '', '', '', '', '单位净值:1.1633', '', '', '', '', '', ''],
    ['科目代码', '科目名称', '币种', '汇率', '数量', '单位成本', '成本', '成本', '成本占比', '行情', '市值', '市值', '市值占比', '估值增值', '估值增值', '停牌信息', '权益信息']
    ]

    :param rows: 前5行数据. list类型,第一个元素为第一行内容.
    :param patterns: 配置的正则表达式. 正则表达式必须有date别名
    :return:
    """
    try:
        value = rows[-2][0]
        for pattern in patterns:
            matched = re.match(pattern, value)
            if matched:
                return matched.groupdict()['date']
    except IndexError:
        pass

    for row in rows:
        value = row[0]  # 交易日一般就在第一列
        for pattern in patterns:
            matched = re.match(pattern, value)
            if matched:
                return matched.groupdict()['date']
    for row in rows:
        for value in row[1:]:
            for pattern in patterns:
                matched = re.match(pattern, value)
                if matched:
                    return matched.groupdict()['date']
    return None


# **fund_name**
def find_fund_name(rows: [[]], patterns, **kwargs):
    """
    >>> rows
    [
    ['TEST01_测试1号私募证券投资基金_资产估值表_20210301', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', ''],
    ['', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', ''],
    ['XX资产管理有限公司__测试1号私募证券投资基金__专用表', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', ''],
    ['日期：2021-03-01', '', '', '', '', '', '', '', '', '', '单位净值:1.1633', '', '', '', '', '', ''],
    ['科目代码', '科目名称', '币种', '汇率', '数量', '单位成本', '成本', '成本', '成本占比', '行情', '市值', '市值', '市值占比', '估值增值', '估值增值', '停牌信息', '权益信息']
    ]
    :param rows: 前5行数据. list类型,第一个元素为第一行内容.
    :param patterns: 配置的正则表达式. 正则表达式必须有date别名
    :return:
    """
    blank_regx = re.compile("\s")
    class_id_row_num = kwargs.get('class_id_row_num')
    class_id_col_num = kwargs.get('class_id_col_num')

    if class_id_col_num is not None and class_id_row_num is not None:
        try:
            text = rows[class_id_row_num - 2][class_id_col_num]
            if '_' in text:
                text = str(text).replace('___', '_')
                text = text.replace('__', '_')
                text = re.sub(blank_regx, "", text)
                values = text.split('_')
                values.reverse()
                if len(values) == 3 and values[0] == "专用表" and len(values[1]) > 4:
                    return values[1]
                for value in values:
                    if value.endswith("基金"):
                        return value
                    elif value.endswith("计划"):
                        return value
                    elif '集合（' in value:
                        return value
        except IndexError:
            pass
    if class_id_row_num is not None:
        # 从科目代码上一行开始
        rows = rows[:class_id_row_num]
        rows = reversed(rows)
    for row in rows:
        for value in row:
            value = str(value)
            value = re.sub(blank_regx, "", value)
            if value == '':
                continue
            for pattern in patterns:
                matched = re.match(pattern, value)
                if matched:
                    return matched.groupdict()['fund_name']
    return None


# **nav**
def converter_nav(row, pattern, matched, **kwargs):
    try:
        return float_converter(row['class_name'])
    except ValueError:
        pass
    try:
        return float_converter(row['market_value'])
    except ValueError:
        pass
    return float_converter(row['cost'])


# **market_value**
def get_market_value(row, pattern, matched, **kwargs):
    return float_converter(row['market_value'])


# **equity**
def converter_equity(row, pattern, matched, **kwargs):
    return float_converter(row['market_value'])


# **share**
def converter_share(row, pattern, matched, **kwargs):
    return float_converter(row['volume'])


# **sum_nav**
def converter_sum_nav(row, pattern, matched, **kwargs):
    try:
        return float_converter(row['class_name'])
    except ValueError:
        pass
    try:
        return float_converter(row['market_value'])
    except ValueError:
        pass
    return float_converter(row['cost'])


# **pre_nav**
def converter_pre_nav(row, pattern, matched, **kwargs):
    try:
        return float_converter(row['class_name'])
    except ValueError:
        pass
    try:
        return float_converter(row['market_value'])
    except ValueError:
        pass
    return float_converter(row['cost'])


# **1102**
def converter_1102(row, pattern, matched):
    instrument, asset_type = instrument_converter(row, pattern, matched)
    instrument_name = row['class_name']
    volume = abs(float_converter(row['volume']))
    try:
        price = abs(float_converter(row['price']))
    except ValueError:
        vt_logger.warning("成本价异常,使用0填充. row:%s" % row)
        price = 0
    cost = abs(float_converter(row['cost']))
    cost_ratio = unsafe_float_converter(row['cost_ratio'])
    try:
        mkt_price = abs(float_converter(row['mkt_price']))
    except ValueError:
        vt_logger.warning("市价异常,使用成本价填充. row:%s" % row)
        mkt_price = price
    close_price = mkt_price
    settle_price = mkt_price
    market_value = abs(float_converter(row['market_value']))
    mkt_ratio = abs(unsafe_float_converter(row['mkt_ratio']))
    if row['pct'] == '':
        pct = 0
    else:
        pct = float_converter(row['pct'])
    # 科目上级科目名称, 来设置持仓 是多头还是空头
    if is_sell(row['class_info']):
        direction = Direction.SELL
    else:
        direction = Direction.BUY
    suspended = row['suspended']
    position = dict(
        instrument=instrument,
        instrument_name=instrument_name,
        asset_type=asset_type,
        direction=direction,
        price=price,
        volume=volume,
        cost=cost,
        cost_ratio=cost_ratio,
        close_price=close_price,
        settle_price=settle_price,
        market_value=market_value,
        mkt_ratio=mkt_ratio,
        pct=pct,
        suspended=suspended,
    )
    return position


# **1103**
def converter_1103(row, pattern, matched):
    instrument, asset_type = instrument_converter(row, pattern, matched)
    asset_type = AssetType.BOND
    instrument_name = row['class_name']
    volume = abs(float_converter(row['volume']))
    try:
        price = abs(float_converter(row['price']))
    except ValueError:
        vt_logger.warning("成本价异常,使用0填充. row:%s" % row)
        price = 0

    cost = abs(float_converter(row['cost']))
    cost_ratio = unsafe_float_converter(row['cost_ratio'])
    try:
        mkt_price = abs(float_converter(row['mkt_price']))
    except ValueError:
        vt_logger.warning("市价异常,使用成本价填充. row:%s" % row)
        mkt_price = price
    close_price = mkt_price
    settle_price = mkt_price
    market_value = abs(float_converter(row['market_value']))
    mkt_ratio = abs(unsafe_float_converter(row['mkt_ratio']))
    if row['pct'] == '':
        pct = 0
    else:
        pct = float_converter(row['pct'])
    # 科目上级科目名称, 来设置持仓 是多头还是空头
    if is_sell(row['class_info']):
        direction = Direction.SELL
    else:
        direction = Direction.BUY
    suspended = row['suspended']
    position = dict(
        instrument=instrument,
        instrument_name=instrument_name,
        asset_type=asset_type,
        direction=direction,
        price=price,
        volume=volume,
        cost=cost,
        cost_ratio=cost_ratio,
        close_price=close_price,
        settle_price=settle_price,
        market_value=market_value,
        mkt_ratio=mkt_ratio,
        pct=pct,
        suspended=suspended,
    )
    return position


# **1105**
def converter_1105(row, pattern, matched):
    """
    公募基金 和私募基金
    :param row:
    :param pattern:
    :param matched:
    :return:
    """
    matched_items = matched.groupdict()
    instrument, asset_type = instrument_converter(row, pattern, matched)
    instrument_name = str(row['class_name'])
    if instrument_name.count('_') >= 2 and instrument_name.count('-') >= 1:
        # 处理这种科目名称  场外_已上市_开放式_成本-对冲5期私募证券投资基金
        instrument_name = "-".join(instrument_name.split('-')[1:])
    volume = abs(float_converter(row['volume']))
    try:
        price = abs(float_converter(row['price']))
    except ValueError:
        vt_logger.warning("成本价异常,使用0填充. row:%s" % row)
        price = 0
    cost = abs(float_converter(row['cost']))
    cost_ratio = unsafe_float_converter(row['cost_ratio'])
    try:
        mkt_price = abs(float_converter(row['mkt_price']))
    except ValueError:
        vt_logger.warning("市价异常,使用成本价填充. row:%s" % row)
        mkt_price = price
    close_price = mkt_price
    settle_price = mkt_price
    market_value = abs(float_converter(row['market_value']))
    mkt_ratio = abs(unsafe_float_converter(row['mkt_ratio']))
    pct = unsafe_float_converter(row['pct'])
    if is_sell(row['class_info']):
        direction = Direction.SELL
    else:
        direction = Direction.BUY
    suspended = row['suspended']
    position = dict(
        instrument=instrument,
        instrument_name=instrument_name,
        asset_type=asset_type,
        direction=direction,
        price=price,
        volume=volume,
        cost=cost,
        cost_ratio=cost_ratio,
        close_price=close_price,
        settle_price=settle_price,
        market_value=market_value,
        mkt_ratio=mkt_ratio,
        pct=pct,
        suspended=suspended,
    )
    return position


# **1108**
def converter_1108(row, pattern, matched):
    """

    :param row:
    :param pattern:
    :param matched:
    :return:
    """
    matched_items = matched.groupdict()
    code = matched_items['private_fund_code']
    instrument = "%s.%s" % ("OTC", code)
    asset_type = AssetType.PRIVATE_FUND
    instrument_name = row['class_name']
    volume = abs(float_converter(row['volume']))
    try:
        price = abs(float_converter(row['price']))
    except ValueError:
        vt_logger.warning("成本价异常,使用0填充. row:%s" % row)
        price = 0
    cost = abs(float_converter(row['cost']))
    cost_ratio = unsafe_float_converter(row['cost_ratio'])
    try:
        mkt_price = abs(float_converter(row['mkt_price']))
    except ValueError:
        vt_logger.warning("市价异常,使用成本价填充. row:%s" % row)
        mkt_price = price
    close_price = mkt_price
    settle_price = mkt_price
    market_value = abs(float_converter(row['market_value']))
    mkt_ratio = abs(unsafe_float_converter(row['mkt_ratio']))
    pct = unsafe_float_converter(row['pct'])
    # 科目上级科目名称, 来设置持仓 是多头还是空头
    if is_sell(row['class_info']):
        direction = Direction.SELL
    else:
        direction = Direction.BUY
    suspended = row['suspended']
    position = dict(
        instrument=instrument,
        instrument_name=instrument_name,
        asset_type=asset_type,
        direction=direction,
        price=price,
        volume=volume,
        cost=cost,
        cost_ratio=cost_ratio,
        close_price=close_price,
        settle_price=settle_price,
        market_value=market_value,
        mkt_ratio=mkt_ratio,
        pct=pct,
        suspended=suspended,
    )
    return position


# **2101**
def converter_2101(row, pattern, matched):
    """
    交易性融券负债, 包含股票和基金
    direction 写死为-1
    :param row:
    :param pattern:
    :param matched:
    :return:
    """
    matched_items = matched.groupdict()
    instrument, asset_type = instrument_converter(row, pattern, matched)
    instrument_name = row['class_name']
    volume = abs(float_converter(row['volume']))
    try:
        price = abs(float_converter(row['price']))
    except ValueError:
        vt_logger.warning("成本价异常,使用0填充. row:%s" % row)
        price = 0
    cost = abs(float_converter(row['cost']))
    cost_ratio = unsafe_float_converter(row['cost_ratio'])
    try:
        mkt_price = abs(float_converter(row['mkt_price']))
    except ValueError:
        vt_logger.warning("市价异常,使用成本价填充. row:%s" % row)
        mkt_price = price
    close_price = mkt_price
    settle_price = mkt_price
    market_value = abs(float_converter(row['market_value']))
    mkt_ratio = abs(unsafe_float_converter(row['mkt_ratio']))
    pct = unsafe_float_converter(row['pct'])
    # 交易性金融负债 负债 SELL
    direction = Direction.SELL
    suspended = row['suspended']
    position = dict(
        instrument=instrument,
        instrument_name=instrument_name,
        asset_type=asset_type,
        direction=direction,
        price=price,
        volume=volume,
        cost=cost,
        cost_ratio=cost_ratio,
        close_price=close_price,
        settle_price=settle_price,
        market_value=market_value,
        mkt_ratio=mkt_ratio,
        pct=pct,
        suspended=suspended,
    )
    return position


# **1109**
def converter_1109(row, pattern, matched):
    """

    :param row:
    :param pattern:
    :param matched:
    :return:
    """
    matched_items = matched.groupdict()
    code = matched_items['private_fund_code']
    instrument = "%s.%s" % ("OTC", code)
    asset_type = AssetType.PRIVATE_FUND
    instrument_name = row['class_name']
    volume = abs(float_converter(row['volume']))
    try:
        price = abs(float_converter(row['price']))
    except ValueError:
        vt_logger.warning("成本价异常,使用0填充. row:%s" % row)
        price = 0
    cost = abs(float_converter(row['cost']))
    cost_ratio = unsafe_float_converter(row['cost_ratio'])
    try:
        mkt_price = abs(float_converter(row['mkt_price']))
    except ValueError:
        vt_logger.warning("市价异常,使用成本价填充. row:%s" % row)
        mkt_price = price
    close_price = mkt_price
    settle_price = mkt_price
    market_value = abs(float_converter(row['market_value']))
    mkt_ratio = abs(unsafe_float_converter(row['mkt_ratio']))
    pct = unsafe_float_converter(row['pct'])
    # 科目上级科目名称, 来设置持仓 是多头还是空头
    if is_sell(row['class_info']):
        direction = Direction.SELL
    else:
        direction = Direction.BUY
    suspended = row['suspended']
    position = dict(
        instrument=instrument,
        instrument_name=instrument_name,
        asset_type=asset_type,
        direction=direction,
        price=price,
        volume=volume,
        cost=cost,
        cost_ratio=cost_ratio,
        close_price=close_price,
        settle_price=settle_price,
        market_value=market_value,
        mkt_ratio=mkt_ratio,
        pct=pct,
        suspended=suspended,
    )
    return position


# **1101**
def converter_1101(row, pattern, matched):
    """

    :param row:
    :param pattern:
    :param matched:
    :return:
    """
    instrument, asset_type = instrument_converter(row, pattern, matched)
    instrument_name = str(row['class_name'])
    if instrument_name.count('_') >= 2 and instrument_name.count('-') >= 1:
        # 处理这种科目名称  场外_已上市_开放式_成本-对冲5期私募证券投资基金
        instrument_name = "-".join(instrument_name.split('-')[1:])
    volume = abs(float_converter(row['volume']))
    try:
        price = abs(float_converter(row['price']))
    except ValueError:
        vt_logger.warning("成本价异常,使用0填充. row:%s" % row)
        price = 0
    cost = abs(float_converter(row['cost']))
    cost_ratio = unsafe_float_converter(row['cost_ratio'])
    try:
        mkt_price = abs(float_converter(row['mkt_price']))
    except ValueError:
        vt_logger.warning("市价异常,使用成本价填充. row:%s" % row)
        mkt_price = price
    close_price = mkt_price
    settle_price = mkt_price
    market_value = abs(float_converter(row['market_value']))
    mkt_ratio = abs(unsafe_float_converter(row['mkt_ratio']))
    pct = unsafe_float_converter(row['pct'])
    # 科目上级科目名称, 来设置持仓 是多头还是空头
    if is_sell(row['class_info']):
        direction = Direction.SELL
    else:
        direction = Direction.BUY
    suspended = row['suspended']
    position = dict(
        instrument=instrument,
        instrument_name=instrument_name,
        asset_type=asset_type,
        direction=direction,
        price=price,
        volume=volume,
        cost=cost,
        cost_ratio=cost_ratio,
        close_price=close_price,
        settle_price=settle_price,
        market_value=market_value,
        mkt_ratio=mkt_ratio,
        pct=pct,
        suspended=suspended,
    )
    return position


# **1110**
def converter_1110(row, pattern, matched):
    """

    :param row:
    :param pattern:
    :param matched:
    :return:
    """
    instrument, asset_type = instrument_converter(row, pattern, matched)
    instrument_name = str(row['class_name'])
    # 处理名称前面的横线 ----------精选量化对冲1号私募证券投资基金
    instrument_name = re.sub("^-+", "", instrument_name)
    cost = abs(float_converter(row['cost']))
    if (not row['volume']) and (not row['price']):
        # 财信信托保障基金 的成本和数量时候是空的, 特殊处理一下
        volume = cost
        price = 1
    else:
        volume = abs(float_converter(row['volume']))
        try:
            price = abs(float_converter(row['price']))
        except ValueError:
            vt_logger.warning("成本价异常,使用0填充. row:%s" % row)
            price = 0
    cost_ratio = unsafe_float_converter(row['cost_ratio'])
    try:
        mkt_price = abs(float_converter(row['mkt_price']))
    except ValueError:
        vt_logger.warning("市价异常,使用成本价填充. row:%s" % row)
        mkt_price = price
    close_price = mkt_price
    settle_price = mkt_price
    market_value = abs(float_converter(row['market_value']))
    mkt_ratio = abs(unsafe_float_converter(row['mkt_ratio']))
    pct = unsafe_float_converter(row['pct'])
    # 科目上级科目名称, 来设置持仓 是多头还是空头
    if is_sell(row['class_info']):
        direction = Direction.SELL
    else:
        direction = Direction.BUY
    suspended = row['suspended']
    position = dict(
        instrument=instrument,
        instrument_name=instrument_name,
        asset_type=asset_type,
        direction=direction,
        price=price,
        volume=volume,
        cost=cost,
        cost_ratio=cost_ratio,
        close_price=close_price,
        settle_price=settle_price,
        market_value=market_value,
        mkt_ratio=mkt_ratio,
        pct=pct,
        suspended=suspended,
    )
    return position


# **3102**
def converter_3102(row, pattern, matched):
    """
    本科目代码下,可能包含期货和etf期权
    :param row:
    :param pattern:
    :param matched:
    :return:
    """
    if row['volume'] == '' and "冲抵" in row['class_info'][-1][-1]:
        # 宁波银行股份有限公司（外包估值)的3102\d\d01 包含了冲抵,需要过滤掉
        return None
    instrument, asset_type = instrument_converter(row, pattern, matched)
    instrument_name = row['class_name']
    volume = abs(float_converter(row['volume']))
    try:
        price = abs(float_converter(row['price']))
    except ValueError:
        vt_logger.warning("成本价异常,使用0填充. row:%s" % row)
        price = 0
    cost = abs(float_converter(row['cost']))
    cost_ratio = unsafe_float_converter(row['cost_ratio'])
    try:
        mkt_price = abs(float_converter(row['mkt_price']))
    except ValueError:
        vt_logger.warning("市价异常,使用成本价填充. row:%s" % row)
        mkt_price = price
    close_price = mkt_price
    settle_price = mkt_price
    market_value = abs(float_converter(row['market_value']))
    mkt_ratio = abs(unsafe_float_converter(row['mkt_ratio']))
    pct = unsafe_float_converter(row['pct'])
    # 科目上级科目名称, 来设置持仓 是多头还是空头
    if is_sell(row['class_info']):
        direction = Direction.SELL
    else:
        direction = Direction.BUY
    suspended = row['suspended']
    position = dict(
        instrument=instrument,
        instrument_name=instrument_name,
        asset_type=asset_type,
        direction=direction,
        price=price,
        volume=volume,
        cost=cost,
        cost_ratio=cost_ratio,
        close_price=close_price,
        settle_price=settle_price,
        market_value=market_value,
        mkt_ratio=mkt_ratio,
        pct=pct,
        suspended=suspended,
    )
    return position


# **test**
def converter_1203(row, pattern, matched):
    """
    打印分红信息
    :param row:
    :param pattern:
    :param matched:
    :return:
    """
    instrument, asset_type = instrument_converter(row, pattern, matched)
    instrument_name = row['class_name']
    suspended = row['suspended']
    direction = Direction.BUY
    market_value = abs(float_converter(row['market_value']))
    mkt_ratio = abs(unsafe_float_converter(row['mkt_ratio']))
    pct = unsafe_float_converter(row['pct'])
    position = dict(
        instrument=instrument,
        instrument_name=instrument_name,
        asset_type=AssetType.BONUS_DIVIDEND,
        direction=direction,
        price=0,
        volume=1,
        cost=0,
        cost_ratio=0,
        close_price=market_value,
        settle_price=market_value,
        market_value=market_value,
        mkt_ratio=mkt_ratio,
        pct=0,
        suspended=suspended,
    )
    return position


# 上个函数结束需要有两个换行,否则初始化解析规则,最后一个函数匹配不到 参见get_parser_role

# ####
#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
import datetime
import logging
from logging import LogRecord

import xlrd
from xlrd import xldate_as_tuple
from constants import AssetType, Direction

vt_logger = logging.getLogger("parser.vt")
_ = Direction  # 防止导入优化
_ = AssetType  # 防止导入优化

ETF_OPTIONS_NAME_PATTERN = re.compile(r"[A-Z0-9]*?[沽|购].*?\d+月\d+")  # etf期权
FUTURE_OPTION_PATTERN = re.compile(r"([a-zA-Z]{1,2})(\d{3,4})([CP])(\d+)")

"""
(?!基金|私募|证券|[0-9a-zA-Z]) 不能以这些开始
(?![a-zA-Z]+$) 不能是纯字母
(?<!估值表) 不能以估值表结束
(?<![12][09][0-9][0-9]([-/年])[01][0-9]([-/月])[0-3][0-9])" 不能以日期格式结束
"""

FUND_NAME_PATTERN = r"(?P<fund_name>" \
                    r"(?!基金|私募|证券|[0-9a-zA-Z]{6})" \
                    r"(?![a-zA-Z]+$)" \
                    r"(?!单位.元$)" \
                    r"(?!.*净值)" \
                    r"(?!.*是否)" \
                    r"(?!\d+$)" \
                    r"[^\s`~!@#$%^&*_=\|[\]{};\"'<>,.?/·~！@#￥%……&*=|、｛｝【】；“”‘’《》，。？、]{3,}?" \
                    r"(?<!估值表)" \
                    r"(?<!科目代码)" \
                    r"(?<!科目..代码)" \
                    r"(?<![12][09][0-9][0-9]([-/年])[01][0-9]([-/月])[0-3][0-9])" \
                    r"(?<![12][09][0-9][0-9][01][0-9][0-3][0-9])" \
                    r")"

"""
FUND_NAME_INSPECTOR
不能包含 估值表 等词语, 以及不能包含日期格式 
排除了一些特殊字符, 以及空白符, 至少3个字符以上
必须以 基金, 计划  括号 结尾. 特殊情况: 测试001集合（2019-1761）
"""
# 基金名称检查正则, 没有匹配到则认为 基金名称错误
FUND_NAME_INSPECTOR = r"(?!.*?(估值表|[12][09][0-9][0-9]([-/年])?[01][0-9]([-/月])?[0-3][0-9]).*(?:基金|计划))" \
                      r"[^\s`~!@#$%^&*_=\|[\]{}:;\"'<>,.?/·~！@#￥%……&*=|、｛｝【】；“”‘’《》，。？、]{3,}?" \
                      r"(?:基金|计划|号|\d\)|\d）)"

FUND_NAME_INSPECTOR = re.compile(FUND_NAME_INSPECTOR)  # 设置为 None, 将跳过检查
FUND_NAME_INSPECTOR = None


class LogStore(logging.Handler):
    log_records = []

    def emit(self, record: LogRecord):
        if isinstance(record.msg, str):
            self.log_records.append(record.msg)
        else:
            self.log_records.append(repr(record.msg))
        # if getattr(record, "show", False):
        #     self.log_records.append(record.msg)


vt_logger.addHandler(LogStore())


# 估值表字段
class ValuationTableField(object):
    class_id = "class_id"               # 科目代码
    class_name = "class_name"           # 科目名称
    volume = "volume"                   # 数量
    price = "price"                     # 单位成本
    cost = "cost"                       # 成本
    mkt_price = "mkt_price"             # 市价
    market_value = "market_value"       # 市值
    cost_ratio = "cost_ratio"           # 成本占净值比例
    mkt_ratio = "mkt_ratio"             # 市值占净值比例
    pct = "pct"                         # 估值增值
    suspended = "suspended"             # 停牌信息


# 交易所 简称映射
EXCHANGE_MAP = {
    'SZ': 'SZSE',
    'SC': 'INE',
    'SH': 'SHSE',
    'CFX': 'CFFEX',
    'SQ': 'SHFE',
    'SHF': 'SHFE',
    'DCE': 'DCE',
    'CZC': 'CZCE',
}

# 用科目名称映射资产类型,可能不准确
ASSET_TYPE_CN_MAP = {
    "股票": AssetType.STOCK,
    "A股": AssetType.STOCK,
    "债": AssetType.BOND,
    "期货": AssetType.FUTURE,
    "期权": AssetType.OPTIONS,
    "个股期权": AssetType.FUTURE,
    "ETF基金": AssetType.PUBLIC_FUND,
    "基金_开放式_ETF": AssetType.PUBLIC_FUND,
    "ETF": AssetType.PUBLIC_FUND,
}

# 股票交易所中文名称映射
STOCK_EXCHANGE_CN_MAP = {
    '上证所': 'SHSE',
    '上交所': 'SHSE',
    '深交所': 'SZSE',
    '场外_已上市': 'OF',
    # '深港通': 'HS',
    # '沪港通': 'HG',
    '深港通': 'HK',
    '沪港通': 'HK',
}

# 交易所中文名称映射
FUTURE_EXCHANGE_CN_MAP = {
    "上交所": 'SHSE',
    "深交所": 'SZSE',

    '大商所': 'DCE',
    '中金所': 'CFFEX',
    '上期所': 'SHFE',
    '郑商所': 'CZCE',

    "上海": 'SHFE',
    "大连": 'DCE',
    "郑州": 'CZCE',
    "中金": 'CFFEX',
    "金融": 'CFFEX',
    "能源": 'INE',
}

# 大写品种映射到期货交易所
FUTURE_PRODUCT_MAP = {
    'IC': 'CFFEX',
    'IF': 'CFFEX',
    'IH': 'CFFEX',
    'T': 'CFFEX',
    'TF': 'CFFEX',
    'TS': 'CFFEX',
    'AP': 'CZCE',
    'CF': 'CZCE',
    'CJ': 'CZCE',
    'CY': 'CZCE',
    'FG': 'CZCE',
    'JR': 'CZCE',
    'LR': 'CZCE',
    'MA': 'CZCE',
    'OI': 'CZCE',
    'PF': 'CZCE',
    'PK': 'CZCE',
    'PM': 'CZCE',
    'RI': 'CZCE',
    'RM': 'CZCE',
    'RS': 'CZCE',
    'SA': 'CZCE',
    'SF': 'CZCE',
    'SM': 'CZCE',
    'SR': 'CZCE',
    'TA': 'CZCE',
    'UR': 'CZCE',
    'WH': 'CZCE',
    'ZC': 'CZCE',
    'A': 'DCE',
    'B': 'DCE',
    'BB': 'DCE',
    'C': 'DCE',
    'CS': 'DCE',
    'EB': 'DCE',
    'EG': 'DCE',
    'FB': 'DCE',
    'I': 'DCE',
    'J': 'DCE',
    'JD': 'DCE',
    'JM': 'DCE',
    'L': 'DCE',
    'LH': 'DCE',
    'M': 'DCE',
    'P': 'DCE',
    'PG': 'DCE',
    'PP': 'DCE',
    'RR': 'DCE',
    'V': 'DCE',
    'Y': 'DCE',
    'BC': 'INE',
    'LU': 'INE',
    'NR': 'INE',
    'SC': 'INE',
    'AG': 'SHFE',
    'AL': 'SHFE',
    'AU': 'SHFE',
    'BU': 'SHFE',
    'CU': 'SHFE',
    'FU': 'SHFE',
    'HC': 'SHFE',
    'NI': 'SHFE',
    'PB': 'SHFE',
    'RB': 'SHFE',
    'RU': 'SHFE',
    'SN': 'SHFE',
    'SP': 'SHFE',
    'SS': 'SHFE',
    'WR': 'SHFE',
    'ZN': 'SHFE',

}

# 卖方向的 科目名称 正则
SELL_DIRECTION_PATTERN = [
    re.compile(r'^\S*?-空$'),
    re.compile(r'^\S*?义务方.*?成本$'),
    re.compile(r'^\S*?空头'),
    re.compile(r'^\S*?卖方'),
    re.compile(r'^\S*?卖.*?成本$'),
]

# 估值表字段名称映射表, 用于查找每个字段的列号. 另外有一些相对定位则用代码实现
# 估值增值 成本 市值 ,在代码中使用了逻辑查找,固没有在下面的配置中
header_name_map = {
    ValuationTableField.class_id: {"科目代码", "科目编码", "科目格式代码"},
    ValuationTableField.class_name: {"科目名称", "科目格式名称"},
    ValuationTableField.volume: {"数量", "证券数量"},
    ValuationTableField.price: {"单位成本"},
    ValuationTableField.cost: {"成本-本币", "证券成本"},
    ValuationTableField.mkt_price: {"行情", "市价", "行情收市价", "行情价格"},
    ValuationTableField.market_value: {"市值-本币", "证券市值"},
    ValuationTableField.cost_ratio: {"成本占净值%", "成本占比", "成本占净值(%)", "成本占净值", "成本占净值市值比例(%)"},
    ValuationTableField.mkt_ratio: {"市值占净值%", "市值占比", "市值占净值(%)", "市值占净值", "市值占净值市值比例(%)", "市值比"},
    ValuationTableField.suspended: {"停牌信息", "行情类型描述"},
    ValuationTableField.pct: {"估值增值-本币"},

}


def is_sell(class_info):
    class_name = class_info[-1][1]
    if class_name == '初始合约价值':
        class_name = class_info[-2][1]
    for pattern in SELL_DIRECTION_PATTERN:
        if re.match(pattern, class_name):
            return True
    else:
        return False


def get_asset_type(class_info):
    """
    用科目名称映射资产类型,可能不准确, 也不完整
    在使用科目代码不能判断的资产类型的时候使用
    :param class_info:
    :return:
    """
    for items in reversed(class_info):
        class_name = items[1]
        for key, value in ASSET_TYPE_CN_MAP.items():
            if key in class_name:
                return value
    return None


def get_stock_exchange_from_class_info(class_info):
    class_name = class_info[-1][1]
    for key, value in STOCK_EXCHANGE_CN_MAP.items():
        if key in class_name:
            return value
    return None


def get_future_exchange_from_class_info(class_info):
    class_name = class_info[-1][1]
    for key, value in FUTURE_EXCHANGE_CN_MAP.items():
        if key in class_name:
            return value
    return None


def get_exchange_from_product(product):
    """
    根据期货品种获取交易所
    :param product: 期货品种
    :return:
    """
    return FUTURE_PRODUCT_MAP.get(product.upper())


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


def unsafe_float_converter(string):
    if string:
        return float_converter(string)
    return 0


def pattern_compiler(pattern):
    """
    正则编译, 并且忽略非字符串和正则的值
    :param pattern:
    :return:
    """
    if isinstance(pattern, (list, tuple)):
        result = []
        for _pattern in pattern:
            if isinstance(_pattern, str):
                result.append(re.compile(_pattern))
            elif isinstance(_pattern, re.Pattern):
                result.append(_pattern)
        return result
    elif isinstance(pattern, str):
        return re.compile(pattern)
    elif isinstance(pattern, re.Pattern):
        return pattern
    else:
        return []


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


def default_converter(row, column):
    return float_converter(row[column])


def instrument_converter(row, pattern, matched):
    """
    转换标准合约代码
    :param row:
    :param pattern:
    :param matched:
    :return: 标准合约代码以及合约类型
    """
    items = matched.groupdict()
    class_info = row['class_info']
    class_name = row['class_name']
    code = items.get('code')  # 在通过科目代码不能确定类型的时候使用code
    stock_code = items.get('stock_code')  # 股票代码 六位数字
    fund_code = items.get('fund_code')  # 公募基金 六位数字
    bond_code = items.get('bond_code')  # 债券 六位数字
    hk_stock = items.get('hk_stock')  # 港股通
    future_code = items.get('future_code')  # 期货
    etf_option_code = items.get('etf_option_code')  # etf 期权
    future_option_code = items.get('future_option_code')  # 期货期权
    private_fund_code = items.get('private_fund_code')  # 私募基金
    exchange = items.get('exchange')
    exchange = EXCHANGE_MAP.get(exchange)

    if code is not None:
        asset_type = get_asset_type(class_info)
        if asset_type == AssetType.STOCK:
            stock_code = code
        elif asset_type == AssetType.PUBLIC_FUND:
            fund_code = code
        elif asset_type == AssetType.FUTURE:
            future_code = code
        elif asset_type == AssetType.BOND:
            bond_code = code
        elif asset_type == AssetType.OPTIONS:
            etf_option_code = code
        else:
            raise ValueError("不能根据class_info识别资产类别")

    if stock_code is not None:
        # 股票转换
        if exchange:
            return "%s.%s" % (exchange, stock_code), AssetType.STOCK
        else:
            idx = stock_code[0]
            if idx in {'0', '3'}:
                return "SZSE.%s" % stock_code, AssetType.STOCK
            else:
                return "SHSE.%s" % stock_code, AssetType.STOCK
    elif bond_code is not None:
        if not exchange:
            exchange = get_stock_exchange_from_class_info(row['class_info'])
        return "%s.%s" % (exchange, bond_code), AssetType.BOND
    elif future_code is not None:
        # 可能匹配到 期货和期权. 单靠科目代码正则无法区分
        # 个股期权 310240012Y0H40 310239012Y0G12   31027001SG0111
        # 套期工具 31020101IC1609  31020101TF1609 310202010C1701 310202010FG609
        if re.match(ETF_OPTIONS_NAME_PATTERN, class_name):
            options_code = decode_option_code(future_code)
            if options_code is None:
                vt_logger.warning("合约代码转换失败. row:%s" % str(row))
                raise ValueError("合约代码转换失败. row:%s" % str(row))
            # if exchange is None:
            #     exchange = get_stock_exchange_from_class_info(row['class_info'])
            if exchange is None:
                if options_code.startswith('10'):
                    exchange = "SHSE"
                elif options_code.startswith('90'):
                    exchange = 'SZSE'
                else:
                    vt_logger.warning("找不到交易所. row:%s" % str(row))
                    raise ValueError("找不到交易所. row:%s" % str(row))
            return "%s.%s" % (exchange, options_code), AssetType.OPTIONS
        else:
            # 期货转换
            if exchange is None:
                product = re.sub(r'\d', '', future_code)
                exchange = get_exchange_from_product(product)
            if exchange is None:
                exchange = get_future_exchange_from_class_info(row['class_info'])
            if exchange is None:
                vt_logger.warning("找不到交易所. row:%s" % str(row))
                raise ValueError("找不到交易所. row:%s" % str(row))
            if exchange in {'CZCE', 'CFFEX'}:
                # 这两个交易所的合约代码大写
                future_code = future_code.upper()
            else:
                future_code = future_code.lower()
            if exchange == 'CZCE':
                # CZCE.ZC605 郑商所的数字只有3位
                num = re.match(r'[a-zA-Z]*?(\d+)', future_code).group(1)
                if len(num) == 4:
                    future_code = future_code.replace(num, num[1:])
            return "%s.%s" % (exchange, future_code), AssetType.FUTURE

    elif etf_option_code is not None:
        if etf_option_code.isdigit() and len(etf_option_code) == 8:
            options_code = etf_option_code
        else:
            options_code = decode_option_code(etf_option_code)
            if options_code is None:
                vt_logger.warning("合约代码转换失败. row:%s" % str(row))
                raise ValueError("合约代码转换失败. row:%s" % str(row))
        # if exchange is None:
        #     exchange = get_stock_exchange_from_class_info(row['class_info'])
        if exchange is None:
            if options_code.startswith('10'):
                exchange = "SHSE"
            elif options_code.startswith('90'):
                exchange = 'SZSE'
            else:
                vt_logger.warning("找不到交易所. row:%s" % str(row))
                raise ValueError("找不到交易所. row:%s" % str(row))
        return "%s.%s" % (exchange, options_code), AssetType.OPTIONS
    elif fund_code is not None:
        if not exchange:
            exchange = get_stock_exchange_from_class_info(row['class_info'])
        if not exchange:
            if fund_code.startswith("5"):
                exchange = "SHSE"
            elif fund_code.startswith("1"):
                exchange = "SZSE"
            else:
                exchange = 'OF'
            vt_logger.debug("根据合约代码(%s)首尾将交易所设置成%s, 可能不正确. row:%s" % (fund_code, exchange, str(row)))
        return "%s.%s" % (exchange, fund_code), AssetType.PUBLIC_FUND
    elif hk_stock is not None:
        if not exchange:
            exchange = get_stock_exchange_from_class_info(row['class_info'])
        if exchange is None:
            exchange = "HK"
        return "%s.%s" % (exchange, hk_stock), AssetType.HK_STOCK
    elif future_option_code is not None:
        if exchange is None:
            exchange = get_future_exchange_from_class_info(row['class_info'])
        if exchange is None:
            vt_logger.warning("找不到交易所. row:%s" % str(row))
            raise ValueError("找不到交易所. row:%s" % str(row))
        instrument = standardizing_future_option_code(future_option_code, exchange)
        return instrument, AssetType.OPTIONS
    elif private_fund_code is not None:
        return "%s.%s" % ("OTC", private_fund_code), AssetType.PRIVATE_FUND
    raise ValueError("未能匹配合约代码")


def standardizing_future_option_code(code, exchange):
    """
    标准化期货期权合约代码
    CZCE CFFEX 这两个交易所合约品种均是大写,其余交易所均小写, 认估认购标志CP 均大写.
    CFFEX DCE 这两个交易所 认估认购标志CP 两边均有-, 其余交易所,则无.
    :param code:
    :param exchange:
    :return:
    """
    # FUTURE_OPTION_PATTERN = re.compile(r"([a-zA-Z]{1,2})(\d{3,4})([CP])(\d+)")
    temp_code = str(code).upper().replace('-', '')
    matched = re.match(FUTURE_OPTION_PATTERN, temp_code)
    if matched is None:
        raise ValueError("期权合约代码格式错误. code:%s" % repr(code))
    resp = list(matched.groups())
    if exchange in {"CZCE", "CFFEX"}:
        resp[0] = resp[0].upper()
    else:
        resp[0] = resp[0].lower()
    resp[2] = resp[2].upper()
    if exchange in {"DCE", "CFFEX"}:
        resp[2] = "-%s-" % resp[2]
    if exchange == 'CZCE':
        # CZCE.ZC605 郑商所的数字只有3位
        resp[1] = resp[1][-3:]
    return exchange + (".%s%s%s%s" % tuple(resp))


default_config = [
    {
        'name': 'date',
        'patterns': [
            r'估?值?日期[：|:]\s?(?P<date>20\d\d[\-年\\]?\d+[\-月\\]?\d+)',
            r'^(?P<date>20\d\d[\-年\\/]?[01]?[0-9][\-月\\/]?[0-3]?[0-9])$',
            r'^[A-Z0-9]{6}}?_%(fund_name_pattern)s_(?P<date>20\d\d[\-年\\]?\d+[\-月\\]?\d+)_资?产?估值表' % dict(
                fund_name_pattern=FUND_NAME_PATTERN),
        ],
        'converter': find_date,
        'description': '日期',
    },
    {
        'name': 'fund_name',
        'patterns': [
            r'^([A-Z0-9]{6})?%(fund_name_pattern)s委?托?资?产?资产估值表' % dict(fund_name_pattern=FUND_NAME_PATTERN),
            r".*(_{1,3})%(fund_name_pattern)s(_{1,3}专用报?表)" % dict(fund_name_pattern=FUND_NAME_PATTERN),
            r'^[A-Z0-9]{6}_%(fund_name_pattern)s_资?产?估值表' % dict(fund_name_pattern=FUND_NAME_PATTERN),
            r'^[A-Z0-9]{6}_%(fund_name_pattern)s_\d{4}-?\d{2}-?\d{2}_资?产?估值表' % dict(
                fund_name_pattern=FUND_NAME_PATTERN),
            r'^%(fund_name_pattern)s_估值表' % dict(fund_name_pattern=FUND_NAME_PATTERN),
            r"^%(fund_name_pattern)s$" % dict(fund_name_pattern=FUND_NAME_PATTERN),
        ],
        'converter': find_fund_name,
        'description': '基金名称',
    },
    {
        'name': 'nav',
        'patterns': ['^今日单位净值', '^单位净值', '^基金单位净值.$', r'^基金单位净值\D*?$'],
        'converter': converter_nav,
        'description': '单位净值',
    },
    {
        'name': 'sum_nav',
        'patterns': ['^累计单位净值.?$', ],
        'converter': converter_sum_nav,
        'description': '累计净值',
    },
    {
        'name': 'pre_nav',
        'patterns': [r"^昨日单位净值"],
        'converter': converter_pre_nav,
        'description': '昨日单位净值',
    },
    {
        'name': 'share',
        'patterns': ['^实收资本$', '^实收信托'],
        'converter': converter_share,
        'description': '份额',
    },
    {
        'name': 'equity',
        'patterns': ['^资产净值', '^基金资产净值', '^资产资产净值', '^信托资产净值'],
        'converter': converter_equity,
        'description': '总权益',
    },
    {
        'name': 'cash',
        'patterns': ['^1002$'],     # 银行存款
        'converter': get_market_value,
        'description': '银行存款',
    },
    {
        'name': 'provisions',
        'patterns': ['^1021$'],     # 结算备付金
        'converter': get_market_value,
        'description': '结算备付金',
    },
    {
        'name': 'margin',
        'patterns': ['^1031$'],     # 存出保证金
        'converter': get_market_value,
        'description': '存出保证金',
    },
    {
        'name': 'financing',
        'patterns': ['^1108$', '^1109$'],  # 理财投资
        'converter': get_market_value,
        'description': '理财投资',
    },
    {
        'name': '1102',
        'patterns': [
            # 股票投资 11024101300001 1102.01.01.600000
            # 股票成本_新股_上交所_科创板 1102C301688038
            r'^1102\.?[A-Z0-9][A-Z0-9]\.?01\.?(?P<stock_code>\d{6})$',
            # 股票投资 1102.05.01.600177 SH
            r'^1102\.[A-Z0-9][A-Z0-9]\.01\.(?P<stock_code>\d{6})\s(?P<exchange>[A-Z]{2})$',
            # 沪港通联合市场_已上市_普通_股票_成本  1102.65.01.00267 HG
            # 深港通联合市场_已上市_普通_股票_成本   1102.66.01.00004 HS
            r'^1102\.[A-Z0-9][A-Z0-9]\.01\.(?P<hk_stock>\d{5})\s(?P<exchange>[A-Z]{2})$',
            r'^1102\.[A-Z0-9][A-Z0-9]\.01\.(?P<hk_stock>\d{5})$',
            # 股票成本_股票成本_深港通 11028301H03331
            r'^1102[A-Z0-9][A-Z0-9]01H(?P<hk_stock>\d{5})$',
        ],
        'converter': converter_1102,
        'description': '股票持仓',
    },
    {
        'name': '1103',
        'patterns': [
            r'^1103\.?\d\d\.?01\.?(?P<bond_code>\d{6})$',
            r'^1103\.\d\d\.01\.(?P<bond_code>\d{6})\s(?P<exchange>[A-Z]{2})$',
        ],
        'converter': converter_1103,
        'description': '债券持仓',
    },
    {
        'name': '1105',
        'patterns': [
            # 上交所_已上市_开放式_货币_信用 11053801511880
            r'^1105\.?\d\d\.?01\.?(?P<fund_code>[0-9]{6})$',
            # 上交所_已上市_开放式_货币_成本 1105.04.01.511880 SH
            r'^1105\.?\d\d\.?01\.?(?P<fund_code>[0-9]{6})\s(?P<exchange>[A-Z]{2,4})$',
            # 场外_已上市_开放式_成本 1105.21.01.SCT530 OTC
            r'^1105\.?\d\d\.?01\.?(?![A-Z]+($| OTC))(?![0-9]+($| OTC))(?P<private_fund_code>[A-Z0-9]{6}-?([ABC0-9]{1,2})?)($| OTC$)',
            # 开放式基金成本  11050201005721
        ],
        'converter': converter_1105,
        'description': '公募基金私募基金持仓',
    },
    {
        'name': '1108',
        'patterns': [
            # 1108.02.01.GY22SGDCTAJQ2 OTC  申万宏源证券 使用产品名称拼音作为代码
            r'^1108\.\d{2}\.01\.(?P<private_fund_code>[A-Z0-9]{6,15}) OTC$',
            # 场外_私募_成本 11080201SGA772 11080201LX125A
            # 场外_私募_成本 1108.02.01.2YFAG1 OTC 1108.02.01.SND51602 OTC
            # 银河证券 场外_私募_成本 11080201SCT694-XN
            r'^1108\.?\d\d\.?01\.?(?![A-Z]+($| OTC))(?![0-9]+($| OTC))(?P<private_fund_code>[A-Z0-9]{6}-?([A-Z0-9]{1,2})?)($| OTC$)',
        ],
        'converter': converter_1108,
        'description': '私募基金持仓',
    },
    {
        'name': '1109',
        'patterns': [
            # 私募基金产品_成本 110906011HRX26
            # 抄1108 场外_私募_成本 11080201SGA772 11080201LX125A
            # 抄1108  场外_私募_成本 1108.02.01.2YFAG1 OTC 1108.02.01.SND51602 OTC
            r'^1109\.?\d\d\.?01\.?(?![A-Z]+($| OTC))(?![0-9]+($| OTC))(?P<private_fund_code>[A-Z0-9]{6}-?([ABC0-9]{1,2})?)($| OTC$)',
            # 11090601HRXDL 这个应该是特殊情况,使用了公司简称
            r'^1109\.?\d\d\.?01\.?(?P<private_fund_code>[A-Z]{5})$',

        ],
        'converter': converter_1109,
        'description': '私募基金持仓',
    },
    {
        'name': '1101',
        'patterns': [
            # 抄1108 场外_私募_成本 11080201SGA772 11080201LX125A
            # 1101050101YC07QC class_info 多了一级
            # 抄1108  场外_私募_成本 1108.02.01.2YFAG1 OTC 1108.02.01.SND51602 OTC
            r'^1101\.?([A-Z0-9]{2}|[A-Z0-9]{4})\.?01\.?(?![A-Z]+($| OTC))(?![0-9]+($| OTC))(?P<private_fund_code>[A-Z0-9]{6}-?([ABC0-9]{1,2})?)($| OTC$)',
            # 1101	交易性金融资产
            # 110104	基金投资
            # 11010432	货币基金
            # 1101043201	货币基金成本
            # 1101043201000905	鹏华安盈宝
            # 6个数字的是公募基金
            r'^1101\.?([A-Z0-9]{2}|[A-Z0-9]{4})\.?01\.?(?P<fund_code>\d{6})$',
            # 特殊私募基金, 估计没有备案号
            r'^1101\.?([A-Z0-9]{2}|[A-Z0-9]{4})\.?01\.?(?P<private_fund_code>[A-Z]{5,6})$',

        ],
        'converter': converter_1101,
        'description': '私募基金持仓',
    },
    {
        # 财信信托估值表
        'name': '1110',
        'patterns': [
            # 1110-343-04-1001203-01-SND516  成本|面值|初始确认金额 财信信托
            r'^1110-\d+-\d+-\d+-01-(?P<private_fund_code>[A-Z0-9]{6}-?([ABC0-9]{1,2})?)($| OTC$)',
            # 1108-341-04-04-01-CXXT 信托计划 场外（特定资产） 场外   财信信托
            r'^1108-\d+-\d+-\d+-01-(?P<private_fund_code>[A-Z]{4})',
        ],
        'converter': converter_1110,
        'description': '私募基金持仓',
    },
    {
        'name': '1203',
        'patterns': [
            # 12032006	应收红利_私募理财产品
            # 12032006SGJ236	丽岙新动力盈十组合私募证券投资基金
            # 1203.03.15	应收基金红利_场外_开放式_货币
            # 1203.03.15.000917 OTC	货币嘉实快线货币A
            # 12030502	应收股利_开放式
            # 12030502000917	嘉实快线货币A
            r'^1203\.?\d\d\.?\d\d\.?(?![A-Z]+($| OTC))(?![0-9]+($| OTC))(?P<private_fund_code>[A-Z0-9]{6}-?([ABC0-9]{1,2})?)($| OTC$)',
            r'^1203\.?\d\d\.?\d\d\.?(?P<fund_code>[0-9]{6})($| (?P<exchange>[A-Z]{2,4})$)',
        ],
        'converter': converter_1203,
        'description': '私募基金持仓',
    },
    {
        'name': '2101',
        'patterns': [
            # 证券负债_基金_开放式_ETF_成本_上交所 2101 21 01 510500
            # 交易性金融负债_融券_股票成本_上交所 21010101600006
            r'^2101\.?\d\d\.?01\.?(?P<code>[0-9]{6})$',
            # 融入证券_股票_成本_上交所     2101.01.01.688981 SH
            r'^2101\.?\d\d\.?01\.?(?P<code>[0-9]{6})\s(?P<exchange>[A-Z]{2})$',
        ],
        'converter': converter_2101,
        'description': '交易性金融负债',
    },
    {
        'name': '3102',
        'patterns': [
            # 套期工具 31020101IC1609  31020101TF1609 310202010C1701 310202010FG609
            r'^3102[A-Z0-9]{2}010?(?P<future_code>[A-Za-z]{1,2}\d{3,4})$',
            # 其他衍生工具 个股期权 310240012Y0H40 310239012Y0G12   31027001SG0111
            # 正则可能会匹配到 商品期货, 这里先写死  [1-9][XYZ0]开头 两个数字结尾
            r'^3102[A-Z0-9]{2}01(?P<etf_option_code>[1-9][XYZ0][A-Za-z0-9]{2}\d{2})$',
            # 衍生工具 3102.95.01.90000438 SZ 3102.43.01.10002750 SH
            # /home/email_client/data/fof_file/208281746509422/95cada54-1632-4c1c-afd9-36b50e1cbe13.xls
            r'^3102\.[A-Z0-9]{2}\.01\.(?P<etf_option_code>\d{8})\s(?P<exchange>[A-Za-z]{2,3})$',
            # 上海_非备兑_买方_期权_ETF基金_成本  3102430110002870
            r'^3102\.?[A-Z0-9]{2}\.?01\.?(?P<etf_option_code>\d{8})$',
            # 衍生工具 3102.01.02.IH2103 CFX  3102.41.02.I2105 DCE 商品期货
            r'^3102\.[A-Z0-9]{2}\.01\.(?P<future_code>[A-Za-z]{1,2}\d{3,4})\s(?P<exchange>[A-Za-z]{2,3})$',
            # 衍生工具 3102.17.01.IO2012-C-4950 CFX 商品期权
            r'^3102\.[A-Z0-9]{2}\.01\.(?P<future_option_code>[A-Za-z]{1,2}\d{3,4}-[CP]-\d{4})\s(?P<exchange>[A-Za-z]{2,3})$',
            # 套期工具 32010201IF1809  股指期货
            r'^3201[A-Z0-9]{2}010?(?P<future_code>[A-Za-z]{1,2}\d{3,4})$',
            # 大商所_投机_卖方_期权品种_商品期货_成本 31025801L2109-P-6200 3102DF01RU2109P12750
            r'^3102\.?[A-Z0-9]{2}\.?01\.?(?P<future_option_code>[A-Za-z]{1,2}\d{3,4}-?[CP]-?\d{3,5})$',
            # 没有碰到例子, 猜测 后面有交易所的 3102DF01RU2109P12750 SHF
            r'^3102\.?[A-Z0-9]{2}\.?01\.?(?P<future_option_code>[A-Za-z]{1,2}\d{3,4}-?[CP]-?\d{3,5})\s(?P<exchange>[A-Za-z]{2,3})$$',
        ],
        'converter': converter_3102,
        'description': '期货期权持仓',
    },
]

