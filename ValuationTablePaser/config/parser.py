# -*- coding: utf-8 -*-
# !/usr/bin/env python


from ValuationTablePaser.config.config import FUND_NAME_PATTERN


def create_default_config():
    from ValuationTablePaser.tools.tools_ht import find_date, find_fund_name, converter_nav, converter_sum_nav, \
        converter_share, \
        converter_pre_nav, \
        converter_equity, get_market_value, converter_1102, converter_1105, converter_1103, converter_1108, \
        converter_1109, \
        converter_1101, converter_1110, converter_1203, converter_2101, converter_3102

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
                r'^([A-Z0-9]{6})?%(fund_name_pattern)s委?托?资?产?资产估值表' % dict(
                    fund_name_pattern=FUND_NAME_PATTERN),
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
    return default_config
