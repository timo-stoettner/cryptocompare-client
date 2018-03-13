# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

setup(
    name='cryptocompare-client',
    version='0.1.3',
    description='Client Wrapper for CryptoCompare API',
    author='Timo Stöttner',
    author_email='mail@timo-stoettner.de',
    url='https://github.com/timo-stoettner/cryptocompare-client',
    packages=find_packages(exclude=('tests', 'docs')),
    install_requires=['requests', 'pymongo', 'socketIO_client']
)

