# coding=utf-8

__version__, __author__ = '0.02', 'sn0wfree & gaoyu'
import os
from glob import glob

import pandas as pd
from CodersWheel.QuickTool.boost_up import boost_up

from ValuationTablePaser.parser.parse_tool import auto_run


class ValueTableParseTools(object):

    @staticmethod
    def _map_file_path(base_path, prefix='SQT217', suffixes=('xls', 'xlsx')):
        for suffix in suffixes:
            base_file_name = f'{prefix}_*.{suffix}'
            path_pattern = os.path.join(base_path, base_file_name)
            for f_path in glob(path_pattern):
                yield f_path

    @classmethod
    def run(cls, base_path, prefix='SQT217', suffixes=('xls', 'xlsx')):
        f_path_list = list(cls._map_file_path(base_path, prefix, suffixes))

        h = map(auto_run, f_path_list)
        return pd.concat(h)

    @classmethod
    def fast_run(cls, base_path, prefix='SQT217', suffixes=('xls', 'xlsx'), ):
        f_path_list = list(cls._map_file_path(base_path, prefix, suffixes))

        h = boost_up(auto_run, f_path_list, star=False)

        return pd.concat(h)


if __name__ == "__main__":
    pass
