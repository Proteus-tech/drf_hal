# -*- coding: utf-8 -*-
import os

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

from distutils.core import setup

setup(
    name='drf-hal',
    version='0.1.16',
    description='Library that provides Hal specification capability on top of django-rest-framework',
    author='Proteus Technologies',
    author_email='team@proteus-tech.com',
    url='http://proteus-tech.com',
    long_description=read('README.md'),
    install_requires=['djangorestframework>=2.3.12'],
    packages=['drf_hal'],
)

