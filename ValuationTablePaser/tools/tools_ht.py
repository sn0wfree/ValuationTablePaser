# coding = utf-8
# !/usr/bin/env python
# -*- coding: utf-8 -*-
import warnings

vt_logger = warnings

print = warnings.warn
from ValuationTablePaser.config.cls_meta import Direction, AssetType
from ValuationTablePaser.tools.common_tools import float_converter, unsafe_float_converter, decode_option_code
import re

from ValuationTablePaser.config.config import SELL_DIRECTION_PATTERN, ASSET_TYPE_CN_MAP, STOCK_EXCHANGE_CN_MAP, \
    FUTURE_EXCHANGE_CN_MAP, \
    FUTURE_PRODUCT_MAP, ValuationTableField, EXCHANGE_MAP, ETF_OPTIONS_NAME_PATTERN, FUTURE_OPTION_PATTERN


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
    exchange = EXCHANGE_MAP.get(exchange) if exchange is not None else exchange

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
                print("合约代码转换失败. row:%s" % str(row))
                raise ValueError("合约代码转换失败. row:%s" % str(row))
            # if exchange is None:
            #     exchange = get_stock_exchange_from_class_info(row['class_info'])
            if exchange is None:
                if options_code.startswith('10'):
                    exchange = "SHSE"
                elif options_code.startswith('90'):
                    exchange = 'SZSE'
                else:
                    print("找不到交易所. row:%s" % str(row))
                    exchange = ''
                    # raise ValueError("找不到交易所. row:%s" % str(row))
            return "%s.%s" % (exchange, options_code), AssetType.OPTIONS
        else:
            # 期货转换
            if exchange is None:
                product = re.sub(r'\d', '', future_code)
                exchange = get_exchange_from_product(product)
            if exchange is None:
                exchange = get_future_exchange_from_class_info(row['class_info'])
            if exchange is None:
                print("找不到交易所. row:%s" % str(row))
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
                print("合约代码转换失败. row:%s" % str(row))
                raise ValueError("合约代码转换失败. row:%s" % str(row))
        # if exchange is None:
        #     exchange = get_stock_exchange_from_class_info(row['class_info'])
        if exchange is None:
            if options_code.startswith('10'):
                exchange = "SHSE"
            elif options_code.startswith('90'):
                exchange = 'SZSE'
            else:
                print("找不到交易所. row:%s" % str(row))
                exchange = ''
                # print("找不到交易所. row:%s" % str(row))
                # raise ValueError("找不到交易所. row:%s" % str(row))
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
            print("根据合约代码(%s)首尾将交易所设置成%s, 可能不正确. row:%s" % (fund_code, exchange, str(row)))
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
            print("找不到交易所. row:%s" % str(row))
            exchange = ''
            # print("找不到交易所. row:%s" % str(row))
            # raise ValueError("找不到交易所. row:%s" % str(row))
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
def converter_nav(rows, patterns, **kwargs):
    try:
        row_result = find_date(rows, patterns)
        return float_converter(row_result)
    except ValueError:
        pass
    try:
        return float_converter(rows['market_value'])
    except ValueError:
        pass
    return float_converter(rows['cost'])


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


# 估值表字段名称映射表, 用于查找每个字段的列号. 另外有一些相对定位则用代码实现
# 估值增值 成本 市值 ,在代码中使用了逻辑查找,固没有在下面的配置中
header_name_map = {
    ValuationTableField.class_id: {"科目代码", "科目编码", "科目格式代码"},
    ValuationTableField.class_name: {"科目名称", "科目格式名称"},
    ValuationTableField.volume: {"数量", "证券数量"},
    ValuationTableField.price: {"单位成本"},
    ValuationTableField.cost: {"成本-本币", "证券成本", "成本"},
    ValuationTableField.mkt_price: {"行情", "市价", "行情收市价", "行情价格"},
    ValuationTableField.market_value: {"市值-本币", "证券市值", "市值"},
    ValuationTableField.cost_ratio: {"成本占净值%", "成本占比", "成本占净值(%)", "成本占净值", "成本占净值市值比例(%)"},
    ValuationTableField.mkt_ratio: {"市值占净值%", "市值占比", "市值占净值(%)", "市值占净值", "市值占净值市值比例(%)",
                                    "市值比"},
    ValuationTableField.suspended: {"停牌信息", "行情类型描述"},
    ValuationTableField.pct: {"估值增值-本币", "估值增值"},

}


def is_sell(class_info):
    class_name = class_info[-1][1]
    if class_name == '初始合约价值':
        class_name = class_info[-2][1]
    for pattern in SELL_DIRECTION_PATTERN:
        if re.match(pattern, '_'.join(class_name)):
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


# **1102**
def converter_1102(row, pattern, matched):
    instrument, asset_type = instrument_converter(row, pattern, matched)
    instrument_name = row['class_name']
    volume = abs(float_converter(row['volume']))
    try:
        price = abs(float_converter(row['price']))
    except ValueError:
        print("成本价异常,使用0填充. row:%s" % row)
        price = 0
    cost = abs(float_converter(row['cost']))
    cost_ratio = unsafe_float_converter(row['cost_ratio'])
    try:
        mkt_price = abs(float_converter(row['mkt_price']))
    except ValueError:
        print("市价异常,使用成本价填充. row:%s" % row)
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
        print("成本价异常,使用0填充. row:%s" % row)
        price = 0

    cost = abs(float_converter(row['cost']))
    cost_ratio = unsafe_float_converter(row['cost_ratio'])
    try:
        mkt_price = abs(float_converter(row['mkt_price']))
    except ValueError:
        print("市价异常,使用成本价填充. row:%s" % row)
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
        print("成本价异常,使用0填充. row:%s" % row)
        price = 0
    cost = abs(float_converter(row['cost']))
    cost_ratio = unsafe_float_converter(row['cost_ratio'])
    try:
        mkt_price = abs(float_converter(row['mkt_price']))
    except ValueError:
        print("市价异常,使用成本价填充. row:%s" % row)
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
        print("成本价异常,使用0填充. row:%s" % row)
        price = 0
    cost = abs(float_converter(row['cost']))
    cost_ratio = unsafe_float_converter(row['cost_ratio'])
    try:
        mkt_price = abs(float_converter(row['mkt_price']))
    except ValueError:
        print("市价异常,使用成本价填充. row:%s" % row)
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
        print("成本价异常,使用0填充. row:%s" % row)
        price = 0
    cost = abs(float_converter(row['cost']))
    cost_ratio = unsafe_float_converter(row['cost_ratio'])
    try:
        mkt_price = abs(float_converter(row['mkt_price']))
    except ValueError:
        print("市价异常,使用成本价填充. row:%s" % row)
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
        print("成本价异常,使用0填充. row:%s" % row)
        price = 0
    cost = abs(float_converter(row['cost']))
    cost_ratio = unsafe_float_converter(row['cost_ratio'])
    try:
        mkt_price = abs(float_converter(row['mkt_price']))
    except ValueError:
        print("市价异常,使用成本价填充. row:%s" % row)
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
        print("成本价异常,使用0填充. row:%s" % row)
        price = 0
    cost = abs(float_converter(row['cost']))
    cost_ratio = unsafe_float_converter(row['cost_ratio'])
    try:
        mkt_price = abs(float_converter(row['mkt_price']))
    except ValueError:
        print("市价异常,使用成本价填充. row:%s" % row)
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
            print("成本价异常,使用0填充. row:%s" % row)
            price = 0
    cost_ratio = unsafe_float_converter(row['cost_ratio'])
    try:
        mkt_price = abs(float_converter(row['mkt_price']))
    except ValueError:
        print("市价异常,使用成本价填充. row:%s" % row)
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
        print("成本价异常,使用0填充. row:%s" % row)
        price = 0
    cost = abs(float_converter(row['cost']))
    cost_ratio = unsafe_float_converter(row['cost_ratio'])
    try:
        mkt_price = abs(float_converter(row['mkt_price']))
    except ValueError:
        print("市价异常,使用成本价填充. row:%s" % row)
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
