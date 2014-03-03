#!/usr/bin/env python
from setuptools import setup

VERSION = "0.5"

setup(
    name="evil",
    version=VERSION,
    description="Expression eviluator",
    author="Paul Scott",
    author_email="paul@duedil.com",
    url="https://github.com/icio/evil",
    download_url="https://github.com/icio/evil/tarball/%s" % VERSION,
    packages=["evil"],
    test_suite="tests",
    license="MIT",
    keywords=['expression', 'eval', 'evaluate', 'math', 'set', 'graph'],
    classifiers=[],
)
