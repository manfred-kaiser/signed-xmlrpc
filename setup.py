# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

# read the contents of your README file
from os import path
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()


setup(
    name='signed_xmlrpc',
    version='0.0.1',
    author='Manfred Kaiser',
    author_email='manfred.kaiser@logfile.at',
    description='xml rpc library for sending signed data',
    long_description=long_description,
    long_description_content_type='text/markdown',
    packages=find_packages(),
    url="https://github.com/manfred-kaiser/signed-xmlrpc",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Topic :: System :: Networking"
    ],
    install_requires=[
        'ecdsa'
    ]
)
