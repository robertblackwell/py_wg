# -*- coding: utf-8 -*-


"""setup.py: setuptools control."""


import re
from setuptools import setup


version = re.search(
    '^__version__\s*=\s*"(.*)"',
    open('py_wg/main.py').read(),
    re.M
    ).group(1)


with open("README.rst", "rb") as f:
    long_descr = f.read().decode("utf-8")


setup(
    name = "py_wg",
    packages = ["py_wg"],
    entry_points = {
        "console_scripts": ['py_wg = py_wg.main:main']
        },
    version = version,
    description = "Python script to run commands in parallel (think xargs and GNU parallel) without intermixing the output. The name `py_wg` is for python_workgang.",
    long_description = long_descr,
    
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 2.7',
        'Topic :: Text Processing :: Linguistic',
      ],

    keywords='xargs, parallel, cli',

    test_suite="tests.test_py_wg",

    author = "Robert Blackwell",
    author_email = "rob@whiteacorn.com",
    url = "http://github.com/robertoblackwell/py_wg.git",
    license ='MIT',
    zip_safe = False
    )
