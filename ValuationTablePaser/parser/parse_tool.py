# -*- coding: utf-8 -*-
import re
import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings('ignore')

# from parsers.plugins.fund.valuation_table.utils import *
# from MetaClass import Direction, AssetType
from ValuationTablePaser.config.config import FUND_NAME_PATTERN
from ValuationTablePaser.tools.tools_ht import find_date, find_fund_name, converter_nav, converter_sum_nav, \
    converter_share, \
    converter_pre_nav, \
    converter_equity, get_market_value, converter_1102, converter_1105, converter_1103, converter_1108, converter_1109, \
    converter_1101, converter_1110, converter_1203, converter_2101, converter_3102, header_name_map, float_converter, \
    unsafe_float_converter, Direction


# 上个函数结束需要有两个换行,否则初始化解析规则,最后一个函数匹配不到 参见get_parser_role


# vt_logger = logging.getLogger("parser.vt")
# _ = Direction  # 防止导入优化
# _ = AssetType  # 防止导入优化


def process(input, *args, converter=None, patterns=None, **kwargs):
    func = converter
    patterns = patterns
    res = func(input, patterns, *args)
    return res


def link_header_name(header, header_name_map):
    for h in header:
        for k, v in header_name_map.items():
            if h in v:
                yield k
                break
        else:
            yield h


def level2_header_ravel(header):
    for r1, r2 in header.T:
        if r1 == r2:
            yield r1
        else:
            yield f"{r1}-{r2}"


def get_matched_group(value, patterns, ):
    try:
        for pattern in patterns:
            matched = re.match(pattern, value)
            if matched:
                return matched
    except IndexError:
        pass


def sp_converter_1202(row, patterns, matched):
    instrument, asset_type = row['class_name'], 'BOND'
    instrument_name = row['class_name']
    volume = float_converter(
        row['volume'])  # 1 if np.isnan(abs(float_converter(row['volume']))) else abs(float_converter(row['volume']))
    try:
        price = float_converter(row['price'])
    except ValueError:
        print("成本价异常,使用0填充. row:%s" % row)
        price = 0
    cost = float_converter(row['cost'])
    cost_ratio = unsafe_float_converter(row['cost_ratio'])
    try:
        mkt_price = float_converter(row['mkt_price'])
    except ValueError:
        print("市价异常,使用成本价填充. row:%s" % row)
        mkt_price = price
    close_price = mkt_price
    settle_price = mkt_price
    market_value = float_converter(row['market_value'])
    mkt_ratio = unsafe_float_converter(row['mkt_ratio'])
    pct = unsafe_float_converter(row['pct'])
    # 交易性金融负债 负债 SELL
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
        'patterns': ['^1002$'],  # 银行存款
        'converter': get_market_value,
        'description': '银行存款',
    },
    {
        'name': 'provisions',
        'patterns': ['^1021$'],  # 结算备付金
        'converter': get_market_value,
        'description': '结算备付金',
    },
    {
        'name': 'margin',
        'patterns': ['^1031$'],  # 存出保证金
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
            r'^1109\.?\d\d\.?01\.?(?P<private_fund_code>[A-Z0-9]{6,15})$',
            # 抄1108 场外_私募_成本 11080201SGA772 11080201LX125A
            # 抄1108  场外_私募_成本 1108.02.01.2YFAG1 OTC 1108.02.01.SND51602 OTC
            r'^1109\.?\d\d\.?01\.?(?![A-Z]+($| OTC))(?![0-9]+($| OTC))(?P<private_fund_code>[A-Z0-9]{6}-?([ABC0-9]{1,2})?)($| OTC$)',
            # 11090601HRXDL 这个应该是特殊情况,使用了公司简称
            r'^1109\.?\d\d\.?01\.?(?P<private_fund_code>[A-Z]{5})$',

        ],
        'converter': converter_1109,
        'description': '私募基金持仓',
    },
    # {
    #         'name': '3003',
    #         'patterns': [
    #             # 私募基金产品_成本 110906011HRX26
    #             r'^3003\.?\d\d\.?01\.?(?P<private_fund_code>[A-Z0-9]{6,15})$',
    #             # 抄1108 场外_私募_成本 11080201SGA772 11080201LX125A
    #             # 抄1108  场外_私募_成本 1108.02.01.2YFAG1 OTC 1108.02.01.SND51602 OTC
    #             r'^3003\.?\d\d\.?01\.?(?![A-Z]+($| OTC))(?![0-9]+($| OTC))(?P<private_fund_code>[A-Z0-9]{6}-?([ABC0-9]{1,2})?)($| OTC$)',
    #             # 11090601HRXDL 这个应该是特殊情况,使用了公司简称
    #             r'^3003\.?\d\d\.?01\.?(?P<private_fund_code>[A-Z]{5})$',
    #
    #         ],
    #         'converter': converter_1109,
    #         'description': '私募基金申购',
    #     },

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
        'name': '1202',
        'patterns': [
            # 12020102204001	GC001
            r'^120201[01,21]{2}\d{4,}',
        ],
        'converter': sp_converter_1202,
        'description': '逆回购', },
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

account_code_2_name = {i['name']: i['description'] for i in default_config}

account_code_2_name.update(dict(zip(['1002', '1021', '1031', '1108', '1204', '1221'],
                                    ['cash', 'provisions', 'margin', '其他交易性金融资产投资', '应收利息',
                                     '其他应收款'])))


def load_given_pattern_config(name, config):
    c2 = dict(zip(['1002', '1021', '1031', '1108', '1109'],
                  ['cash', 'provisions', 'margin', ]))
    for c in config:
        # if name == '3102':
        #     print(1)
        if name == c['name']:
            return c
        #
        elif name in ['1002', '1021', '1031', ]:

            par_name = c2.get(name)
            if par_name == c['name']:
                return c
            else:
                pass

        else:
            pass
    else:
        pass
        # raise ValueError(f'connot find {name}!')
        # print((f'connot find {name}!'))


def parse_underlying(c4, lvl1_code='1102', level=4):
    mask_1002 = c4['lvl1_code'] == lvl1_code
    level4_mask = c4['level'] == level
    c1002 = c4[mask_1002 & level4_mask]
    try:
        pc = load_given_pattern_config(lvl1_code, default_config)
        patterns = pc['patterns']
        func = pc['converter']
        # funcs = globals().keys()
        for n, rows in c1002.iterrows():
            matched = get_matched_group(rows['class_id'], patterns)
            # rt2 = matched.groupdict()
            if matched is not None and matched.groupdict() is not None:
                # print(rows['class_info'])
                # d = get_asset_type(rows['class_info'])
                pos = func(rows, patterns, matched)
                yield pos
    except Exception as e:
        # print(e)
        pass


def parse_underlying_lvl1(c4, lvl1_code='1102', level=1):
    if level == 1:
        print('parsing:', lvl1_code)
    if isinstance(lvl1_code, str):
        mask_1002 = c4['lvl1_code'] == lvl1_code
    elif isinstance(lvl1_code, (list, tuple, set)):
        mask_1002 = c4['lvl1_code'].isin(lvl1_code)
    else:
        raise ValueError('unknown lvl1_code!')
    level4_mask = c4['level'] == level
    c1002 = c4[mask_1002 & level4_mask]
    return c1002


def parse_underlying_gtja(c4, lvl1_code='1102', level=4):
    """
    ['instrument', 'instrument_name', 'asset_type', 'direction',
    股票代码，        名称 ，             资产类型，      购买方向
    'price', 'volume', 'cost', 'cost_ratio', 'close_price', 'settle_price',
    收盘价，     数量 ，  单位成本，   成本占比     ,行情          ,成交价格

    'market_value', 'mkt_ratio', 'pct', 'suspended', 'FOF_name', 'value_dt']
    市值           ， 市值比率
    :param c4:
    :param lvl1_code:
    :return:
    """
    # if level == 1:
    #     print(lvl1_code)
    mask_1002 = c4['lvl1_code'] == lvl1_code
    level4_mask = c4['level'] == level
    c1002 = c4[mask_1002 & level4_mask]

    pc = load_given_pattern_config(lvl1_code, default_config)
    if pc is None:
        pass
    else:
        patterns = pc['patterns']
        func = pc['converter']
        # funcs = globals().keys()
        for n, rows in c1002.iterrows():
            matched = get_matched_group(rows['class_id'], patterns)

            if matched is not None:
                if matched.groupdict() is not None and len(matched.groupdict()) != 0:
                    try:
                        pos = func(rows, patterns, matched)
                        ## 国泰君安 比率没有百分比
                        pos['cost_ratio'] = pos['cost_ratio'] / 100
                        pos['mkt_ratio'] = pos['mkt_ratio'] / 100
                        yield pos
                    except Exception as e:
                        print(e)
                else:
                    if lvl1_code == '1202':
                        pos = func(rows, patterns, matched)
                        # c1002.groupby(['class_name'])[['cost', 'cost_ratio', 'market_value', 'mkt_ratio']]
                        {'instrument': '.mo2210C6500', 'instrument_name': '中证1000股指2210-C-6500',
                         'asset_type': 'OPTIONS',
                         'direction': 'BUY', 'price': 67.5, 'volume': 20.0, 'cost': 135000.0, 'cost_ratio': 0.000335,
                         'close_price': 50.2, 'settle_price': 50.2, 'market_value': 100400.0, 'mkt_ratio': 0.000249,
                         'pct': -34600.0, 'suspended': '【正常交易】'}
                        yield pos


def parse_equity_data(df, config, ht=True):
    {
        'name': 'equity',
        'patterns': ['^资产净值', '^基金资产净值', '^资产资产净值', '^信托资产净值'],
        'converter': converter_equity,
        'description': '总权益',
    }
    pattern_regex = '|'.join(config['patterns'])

    na_mask = df['class_id'].isna()
    rm_df = df[~na_mask]

    values = rm_df[rm_df['class_id'].str.contains(pattern_regex)]

    values['class_id'] = values['class_id'].apply(lambda x: x[:-1] if x.endswith(':') else x)
    # 修正单位

    # values.columns = ['名称', '成本', '成本占比', '市值', '市值占比', 'lvl1_code', 'level', 'class_info']
    return values


def auto_run(target):
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

    def get_nav(c4, c):
        import numpy as np
        for row in c4:
            for value in row[1:]:

                if value is np.nan:
                    continue
                else:
                    for pattern in c['patterns']:
                        matched = re.match(pattern, ''.join(value))
                        if matched:
                            if '(' in value and value.endswith(')'):
                                v2d = float_converter(value.strip(pattern).strip('：').strip(':').split('(')[0])
                                return v2d
                            else:
                                return float_converter(value.strip(pattern).strip('：').strip(':'))

    def _parse_lvl(x):
        if '.' in str(x):
            return len(str(x).split('.'))
        else:
            length = len(str(x))
            if length == 4:
                return 1
            elif length == 6:
                return 2
            elif length == 8:
                return 3
            else:
                return 4

    # 解析科目
    data = pd.read_excel(target, header=None)
    ht = '华泰证券股份有限公司' in ' '.join(data.head(5).astype(str).values.ravel().tolist())
    func = parse_underlying if ht else parse_underlying_gtja  ## 确定解析func
    ## 解析科目名称
    c4 = data.head(5).values
    c = default_config[1]
    # fund_name
    fund_name = process(c4, **c)

    ## table header parse
    header_data = c4 = data.head(5).values

    # find_date
    dt = process(header_data, **default_config[0])

    # 单位净值
    nav = get_nav(header_data, default_config[2])

    # 标的解析
    # 科目代码
    loc = data[data[0] == '科目代码'].index
    c4 = data[loc.max() + 1:]

    # 累计单位净值
    # sum_nav = converter_sum_nav(c4, default_config[3])  # converter_equity

    # equity = converter_equity(header_data, default_config[6])
    # 现金

    # others

    header = data.iloc[loc.min(), :] if len(loc) == 1 else list(level2_header_ravel(data[loc.min():loc.max()].values))

    c4.columns = list(link_header_name(header, header_name_map))

    c4['lvl1_code'] = c4['class_id'].apply(lambda x: str(x).split('.')[0] if '.' in str(x) else str(x)[:4])
    c4['level'] = c4['class_id'].apply(_parse_lvl)
    c4['class_info'] = c4['class_name'].apply(lambda x: [None, [None] + [str(x).split('-')[0].split('_')]])

    lvl1code_list = list(filter(lambda x: x.isnumeric(), c4['lvl1_code'].unique().tolist()))
    h = []
    # cls_h = {}
    for lvl1_code in lvl1code_list:
        items = list(func(c4, lvl1_code=lvl1_code, level=4))

        # cls_h[lvl1_code] = cls_items[0] if len(cls_items) == 1 else None
        h.extend(items)

    cls_items = parse_underlying_lvl1(c4, lvl1_code=lvl1code_list, level=1)

    # cls_result = pd.DataFrame([cls_h]).rename(columns=account_code_2_name)
    # 资产净值
    aum_df = parse_equity_data(c4, default_config[6], ht=ht)

    result = pd.DataFrame(h)
    result['FOF_name'] = fund_name
    result['value_dt'] = pd.to_datetime(str(dt)) if '-' in str(dt) else pd.to_datetime(str(dt), format='%Y%m%d')
    result['FOF_NAV'] = nav

    # 处理部分合约名称
    drop_prefix = lambda x: x[17:] if x.startswith('场外_已上市_开放式_私募_成本-') else x
    result['instrument_name'] = result['instrument_name'].apply(drop_prefix)
    return result


class ParseValueTable(object):
    def __init__(self, file_path, default_config=default_config):

        self.data = pd.read_excel(file_path, header=None)  ## load data

        self._ht = '华泰证券股份有限公司' in ' '.join(self.data.head(5).astype(str).values.ravel().tolist())

        self.parser_underlying_func = parse_underlying if self._ht else parse_underlying_gtja  ## 确定解析func

        self.default_config = default_config

    def get_all_info(self):
        fund_name = self.get_fund_name()

        dt = self.get_date()
        value_dt = pd.to_datetime(str(dt)) if '-' in str(dt) else pd.to_datetime(str(dt), format='%Y%m%d')
        nav = self.get_nav()

        c4 = self.get_body()

        net_aum = self.get_net_aum(c4)
        net_aum['FOF_name'] = fund_name
        net_aum['value_dt'] = value_dt
        net_aum['FOF_NAV'] = nav
        if not self._ht:
            net_aum['cost_ratio'] = net_aum['cost_ratio'] / 100
            net_aum['mkt_ratio'] = net_aum['mkt_ratio'] / 100

        cls_result, result = self.parse_body(c4)
        cls_result['FOF_name'] = fund_name
        cls_result['value_dt'] = value_dt
        cls_result['FOF_NAV'] = nav
        if not self._ht:
            cls_result['cost_ratio'] = cls_result['cost_ratio'] / 100
            cls_result['mkt_ratio'] = cls_result['mkt_ratio'] / 100

        result['FOF_name'] = fund_name
        result['value_dt'] = value_dt
        result['FOF_NAV'] = nav

        if not self._ht and not result.empty:
            result['cost_ratio'] = result['cost_ratio'] / 100
            result['mkt_ratio'] = result['mkt_ratio'] / 100
        # result['cost_ratio'] = result['cost_ratio'] * 1 if self._ht else result['cost_ratio'] / 100
        # result['mkt_ratio'] = result['mkt_ratio'] * 1 if self._ht else result['mkt_ratio'] / 100

        return net_aum, cls_result, result

    @property
    def account_info(self):
        ## 解析科目名称
        c4 = self.data.head(5).values
        # c = default_config[1]
        return c4

    def get_body(self):
        # others
        loc = self.data[self.data[0] == '科目代码'].index
        c4 = self.data[loc.max() + 1:]

        header = self.data.iloc[loc.min(), :] if len(loc) == 1 else list(
            level2_header_ravel(self.data[loc.min():loc.max()].values))

        c4.columns = list(link_header_name(header, header_name_map))

        c4['lvl1_code'] = c4['class_id'].apply(lambda x: str(x).split('.')[0] if '.' in str(x) else str(x)[:4])
        c4['level'] = c4['class_id'].apply(self._parse_lvl)
        c4['class_info'] = c4['class_name'].apply(lambda x: [None, [None] + [str(x).split('-')[0].split('_')]])
        return c4

    def parse_body(self, c4):

        lvl1code_list = list(filter(lambda x: x.isnumeric(), c4['lvl1_code'].unique().tolist()))
        h = []
        cls_h = {}
        func = self.parser_underlying_func
        for lvl1_code in lvl1code_list:
            if lvl1_code == '3003':
                print(1)
            items = list(func(c4, lvl1_code=lvl1_code, level=4))
            if lvl1_code == '1202' and len(items) > 1:
                groupby_cols = ['instrument', 'instrument_name', 'asset_type', 'direction']
                temp_items_df = pd.DataFrame(items)
                temp_sum_items = temp_items_df.groupby(groupby_cols).sum(numeric_only=True).reset_index()
                # ['instrument', 'instrument_name', 'asset_type', 'direction', 'price', 'volume', 'cost',
                #  'cost_ratio', 'close_price', 'settle_price', 'market_value', 'mkt_ratio', 'pct', 'suspended']
                temp_sum_items['price'] = temp_sum_items['price'].replace(0, 100)
                temp_sum_items['close_price'] = temp_sum_items['price']
                temp_sum_items['settle_price'] = temp_sum_items['price']
                # temp_sum_items['pct'] = temp_sum_items['pct'].replace(0, 1)
                temp_sum_items['suspended'] = temp_sum_items['suspended'].replace(0, '逆回购强制设定价格为100')

                names = ','.join(temp_sum_items['instrument_name'].unique().tolist())
                temp2 = []
                for _, df in temp_sum_items.groupby(groupby_cols):
                    if (df['volume'] == 0).all():
                        df['volume'] = df['cost'] / df['price']
                    temp2.append(df)
                altered_volume = pd.concat(temp2)

                items = altered_volume.to_dict('records')
                print(f'merge items named {names}  with 1202 lvl1_code as one!')
            h.extend(items)

        # cls_result = pd.DataFrame([cls_h]).rename(columns=account_code_2_name)
        cls_result = parse_underlying_lvl1(c4, lvl1_code=lvl1code_list, level=1)

        result = pd.DataFrame(h)
        if not result.empty:
            # '场外_已上市_开放式_私募_成本-'
            result['instrument_name'] = result['instrument_name'].apply(
                lambda x: x.replace('场外_已上市_开放式_私募_成本-', ''))
            # 中金所_投机_卖方_股指_成本-
            # result['instrument_name'].aplly(lambda x: '中金所_投机_卖方_股指_成本-' in x)
            result['instrument_name'] = result['instrument_name'].apply(
                lambda x: x.replace('中金所_投机_卖方_股指_成本-', ''))
        # result['FOF_name'] = fund_name
        # result['value_dt'] = pd.to_datetime(str(dt)) if '-' in str(dt) else pd.to_datetime(str(dt), format='%Y%m%d')
        # result['FOF_NAV'] = nav
        return cls_result, result

    def get_fund_name(self):
        # fund_name
        fund_name = process(self.account_info, **self.default_config[1])
        return fund_name

    def get_date(self):
        # find_date
        dt = process(self.account_info, **self.default_config[0])
        return dt

    @staticmethod
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

    def get_nav(self, c4=None, c=None):
        c4 = self.account_info if c4 is None else c4
        c = self.default_config[2] if c is None else c

        for row in c4:
            for value in row[1:]:
                if value is np.nan:
                    continue
                else:
                    for pattern in c['patterns']:
                        matched = re.match(pattern, ''.join(value))
                        if matched:
                            if '(' in value and value.endswith(')'):
                                v2d = self.float_converter(value.strip(pattern).strip('：').strip(':').split('(')[0])
                                return v2d
                            else:
                                return self.float_converter(value.strip(pattern).strip('：').strip(':'))

    @staticmethod
    def _parse_lvl(x):
        if '.' in str(x):
            return len(str(x).split('.'))
        else:
            length = len(str(x))
            if length == 4:
                return 1
            elif length == 6:
                return 2
            elif length == 8:
                return 3
            else:
                return 4

    def get_net_aum(self, c4):
        # 资产净值
        aum_df = parse_equity_data(c4, self.default_config[6], ht=self._ht)
        return aum_df


if __name__ == '__main__':
    pass
    # load level3 net value table
    target = "D:\紫金矿业\组合基金部周报\\ValuationTablePaser\\SSP881_紫金资产星辉私募证券投资基金_产品估值表_日报_20220624 (3).xls"
    target = "D:\紫金矿业\组合基金部周报\\ValuationTablePaser\\data\\估值表8_16\九泽\SQT217_紫金资产九泽私募证券投资基金_估值表_20220725.xls"

    result = auto_run(target)
    print(1)

    # 转化code
