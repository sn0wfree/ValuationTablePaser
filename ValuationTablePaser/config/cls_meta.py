# coding=utf-8
class AssetType(object):
    STOCK = 'STOCK'
    BOND = 'BOND'
    FUTURE = 'FUTURE'
    OPTIONS = 'OPTIONS'
    PUBLIC_FUND = 'PUBLIC_FUND'
    BONUS_DIVIDEN = 'BONUS_DIVIDEND'
    PRIVATE_FUND = 'PRIVATE_FUND'
    HK_STOCK = 'HK_STOCK'
    # FUTURE: 'FUTURE'
    # OPTIONS: 'OPTIONS'

    pass


class Direction(object):
    BUY = 'BUY'
    SELL = 'SELL'
