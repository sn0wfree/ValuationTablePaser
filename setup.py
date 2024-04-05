# coding=utf-8
from setuptools import setup, find_packages

from ValuationTablePaser import __version__, __author__

setup(
    name="ValuationTablePaser",
    version=__version__,
    keywords=("parse valuetable", "tools"),
    description="parse valuetable for analysis tools",
    long_description="valuetable tools",
    license="MIT Licence",

    url="http://www.github.com/sn0wfree",
    author=__author__,
    author_email="snowfreedom0815@gmail.com",

    packages=find_packages(),
    include_package_data=False,

)
