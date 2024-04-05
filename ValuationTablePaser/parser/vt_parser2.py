# coding=utf-8
import os
from glob import glob

import numpy as np
import pandas as pd

from ValuationTablePaser.parser.parse_tool import ParseValueTable


class ValueTableAnalysis(object):
    def __init__(self, value_file_store_base_path, value_secu_name_replace=None):
        self._value_file_store_base_path = value_file_store_base_path
        self._value_secu_name_replace = value_secu_name_replace

    @staticmethod
    def name_replace_dict(
            name_indx_path='C:\\Users\\linlu\\Documents\\GitHub\\pf_analysis\\pf_analysis\\product_analysis3\\交易流水估值表名称映射表.xlsx'):

        name_idx = pd.read_excel(name_indx_path)
        name_idx_dict = dict(name_idx[['valuetable_name', 'transca_scripts_name']].values)
        return name_idx_dict

    def parse(self, dt=None, value_secu_name_replace=None):
        value_secu_name_replace = self._value_secu_name_replace if value_secu_name_replace is None else value_secu_name_replace

        return self.parse_value_table(value_file_store_base_path=self._value_file_store_base_path,
                                      value_secu_name_repalce=value_secu_name_replace, dt=dt)

    @classmethod
    def parse_value_table(cls, value_file_store_base_path, value_secu_name_repalce=None, dt=None, ):

        # 解析估值表

        cols = ['FOF_name', '估值日期', 'FOF_NAV', '证券代码', '证券名称', '产品类型', '交易方向', '单位成本',
                '数量', '成本', '成本占净值比例', '行情', '行情价格', '市值', '市值占净值比例', '估值增值',
                '行情类型描述']
        old_cols = ['FOF_name', 'value_dt', 'FOF_NAV', 'instrument', 'instrument_name',
                    'asset_type', 'direction', 'price', 'volume', 'cost', 'cost_ratio',
                    'close_price', 'settle_price', 'market_value', 'mkt_ratio', 'pct',
                    'suspended']

        if dt is None:

            suffix = '*'
        else:
            suffix = pd.to_datetime(dt).strftime("%Y%m%d")

        aum_list, cls_result_list, instrument_list = zip(*list(
            cls.parse_prod_value_table(value_file_store_base_path, suffix=suffix, file_type='xls',
                                       return_all=True)))

        aum_df = pd.concat(aum_list)
        aum_df = aum_df.rename(columns=dict(zip(old_cols, cols)))

        cls_result_df = pd.concat(cls_result_list)
        cls_result_df = cls_result_df.rename(columns=dict(zip(old_cols, cols)))
        cls_result_df['盈亏'] = cls_result_df['市值'] - cls_result_df['成本']
        cls_result_df['盈亏比例'] = cls_result_df['盈亏'] / cls_result_df['成本']

        result = pd.concat(instrument_list)

        # rename
        result = result.rename(columns=dict(zip(old_cols, cols)))[cols]
        # '场外_已上市_开放式_私募_成本-'
        result['证券名称'] = result['证券名称'].apply(lambda x: x.replace('场外_已上市_开放式_私募_成本-', ''))

        # 中金所_投机_卖方_股指_成本-
        # result['证券名称'].aplly(lambda x: '中金所_投机_卖方_股指_成本-' in x)
        result['证券名称'] = result['证券名称'].apply(lambda x: x.replace('中金所_投机_卖方_股指_成本-', ''))

        result['盈亏'] = result['市值'] - result['成本']

        pnl_va_diff_mask = result['盈亏'].round(2) == result['估值增值'].round(2) * -1
        devr_mask = result['产品类型'].isin(['FUTURE', 'OPTION', 'OPTIONS'])
        required_alter_mask = pnl_va_diff_mask & devr_mask
        if not result[required_alter_mask].empty:  # 修正价格方向
            result.loc[required_alter_mask, '成本'] = result.loc[required_alter_mask, '成本'] * -1
            result.loc[required_alter_mask, '市值'] = result.loc[required_alter_mask, '市值'] * -1
            # result.loc[required_alter_mask, '盈亏'] = result.loc[required_alter_mask, '盈亏'] * -1
            result.loc[required_alter_mask, '交易方向'] = result.loc[required_alter_mask, '交易方向'].replace(
                {'BUY': 'SELL'})
            print('修正交易方向：', result.loc[required_alter_mask, '证券名称'])
        result['盈亏'] = pnl = result['市值'] - result['成本']
        result['盈亏比例'] = result['估值增值'] / np.abs(result['成本'])
        result['证券名称'] = result['证券名称'].replace(value_secu_name_repalce)
        result['估值日期'] = pd.to_datetime(result['估值日期'])

        return aum_df, cls_result_df, result

    @staticmethod
    # @file_cache(enable_cache=True, granularity='d')
    def _parse_valutable_get_all_info(f: str):
        net_aum, cls_result, result = ParseValueTable(f).get_all_info()
        return net_aum, cls_result, result

    @classmethod
    def parse_prod_value_table(cls, base_path, suffix='*', file_type='xls', return_all=False):
        if suffix != '*':
            suffix = '*' + suffix
        for f in glob(os.path.join(base_path, f'{suffix}.{file_type}')):
            try:
                net_aum, cls_result, result = cls._parse_valutable_get_all_info(f)

                if not return_all:
                    yield result
                else:
                    yield net_aum, cls_result, result
            except Exception as e:
                print(e)
                raise e

    @classmethod
    def parse_value_with_alternative_option(cls, value_file_store_base_path,
                                            category2_path, scripts_path, prod_code,
                                            value_secu_name_repalce=None):
        name = os.path.split(value_file_store_base_path)[-1]

        # 解析估值表
        result = cls.parse_value_table(value_file_store_base_path, value_secu_name_repalce=value_secu_name_repalce)
        # cate 导入大类类别
        cate = pd.read_excel(category2_path, sheet_name='category')

        # 初次投出日
        scripts = pd.read_excel(scripts_path)
        scripts = scripts[scripts['产品代码'] == prod_code]
        scripts['交易日期'] = pd.to_datetime(scripts['交易日期'])
        mask = scripts['交易方式'].isin(['申购申请', '申购确认'])
        init_buy = scripts[mask].groupby('证券名称')['交易日期'].min().reset_index()
        init_buy.columns = ['证券名称', '首次投出日期']

        ## replace option
        def replace_MO_option_name(result_cols):
            for c in result_cols:
                if c.startswith('中证1000股指'):
                    yield c.replace('中证1000股指', 'MO') + '.CFE'
                else:
                    yield c

        result['证券名称'] = list(replace_MO_option_name(result['证券名称'].values))

        result_with_init_buy = pd.merge(result, init_buy, left_on='证券名称', right_on='证券名称', how='left')
        result_with_cate_init_buy = pd.merge(result_with_init_buy, cate, left_on='证券名称', right_on='fund_name',
                                             how='left')
        return result_with_cate_init_buy, scripts, init_buy


if __name__ == '__main__':
    prod_name = '九泽'
    target_product_code = 'SQT217'

    transaction_kwargs = dict(
        transact_file_path='C:\\Users\\linlu\\Documents\\GitHub\\pf_analysis\\pf_analysis\\product_analysis3\\成交清算日报表_2022-07-24至2023-09-11.xls',
        business_flag_path='C:\\Users\\linlu\\Documents\\GitHub\\pf_analysis\\pf_analysis\\product_analysis3\\成交清算业务标签映射.xls', )

    valuetable_kwargs = dict(
        value_file_store_base_path=f'D:\\紫金矿业\\组合基金部周报\\ValuationTablePaser\\data\\估值表8_16\\{prod_name}',
        value_secu_name_replace=None)

    vta = ValueTableAnalysis(**valuetable_kwargs)
    vta.parse()
    print(1)
    pass
