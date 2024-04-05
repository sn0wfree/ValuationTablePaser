# coding =utf-8


from ValuationTablePaser.config.cls_meta import AssetType, Direction

import re

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
    "个股期权": AssetType.FUTURE,  # OPTIONS
    "ETF基金": AssetType.PUBLIC_FUND,
    "基金_开放式_ETF": AssetType.PUBLIC_FUND,
    "开放式_ETF": AssetType.PUBLIC_FUND,
    "ETF": AssetType.PUBLIC_FUND,
    "私募": AssetType.PRIVATE_FUND,
    '质押式': AssetType.BOND,
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


# 估值表字段
class ValuationTableField(object):
    class_id = "class_id"  # 科目代码
    class_name = "class_name"  # 科目名称
    volume = "volume"  # 数量
    price = "price"  # 单位成本
    cost = "cost"  # 成本
    mkt_price = "mkt_price"  # 市价
    market_value = "market_value"  # 市值
    cost_ratio = "cost_ratio"  # 成本占净值比例
    mkt_ratio = "mkt_ratio"  # 市值占净值比例
    pct = "pct"  # 估值增值
    suspended = "suspended"  # 停牌信息


# 卖方向的 科目名称 正则
SELL_DIRECTION_PATTERN = [
    re.compile(r'^\S*?-空$'),
    re.compile(r'^\S*?义务方.*?成本$'),
    re.compile(r'^\S*?空头'),
    re.compile(r'^\S*?卖方'),
    re.compile(r'^\S*?卖.*?成本$'),
]

if __name__ == '__main__':
    pass
