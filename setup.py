# -*- coding: utf-8 -*-
"""
Created on Thu Apr 09 16:43:49 2015

@author: mheesema
"""

from setuptools import setup #, find_packages

setup(name='pyONC',
      version='0.1.0',
      description='Python tools for Ocean Networks Canada data access',
      url='https://github.com/MHee/pyONC',
      author='Martin Heesemann',
      author_email='mheesema@uvic.ca',
      license='MIT',
      packages=['pyONC','pyONC.webservices'],
      zip_safe=False)
#print find_packages()