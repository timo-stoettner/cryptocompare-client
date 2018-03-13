# -*- coding: utf-8 -*-

from setuptools import setup, find_packages


with open('README.rst') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name='cryptocompare-client',
    version='0.1.0',
    description='Client Wrapper for CryptoCompare API',
    long_description=readme,
    author='Timo Stöttner',
    author_email='mail@timo-stoettner.de',
    url='https://github.com/timo-stoettner/cryptocompare-client',
    license=license,
    packages=find_packages(exclude=('tests', 'docs'))
)

