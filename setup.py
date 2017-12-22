# -*- coding: utf-8 -*-


"""setup.py: setuptools control."""


import re
from setuptools import setup


version = re.search(
    '^__version__\s*=\s*"(.*)"',
    open('xa/main.py').read(),
    re.M
    ).group(1)


with open("README.rst", "rb") as f:
    long_descr = f.read().decode("utf-8")


setup(
    name = "xa",
    packages = ["xa"],
    entry_points = {
        "console_scripts": ['xa = xa.main:main']
        },
    version = version,
    description = "Python command to run commands in parallel (think xargs and GNU parallel) without intermixing the output",
    long_description = long_descr,
    author = "Robert Blackwell",
    author_email = "rob@whiteacorn.com",
    url = "http://blackwellapps.com",
    )
