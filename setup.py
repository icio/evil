#!/usr/bin/env python
from setuptools import setup

VERSION = "0.4"

setup(
    name="setquery",
    version=VERSION,
    description="Set arithmetic evaluator",
    author="Paul Scott",
    author_email="paul@duedil.com",
    url="https://github.com/icio/setquery",
    download_url="https://github.com/icio/setquery/tarball/%s" % VERSION,
    py_modules=["setquery"],
    license="MIT",
    keywords=['set', 'expression', 'eval', 'evaluate'],
    classifiers=[],
)
