#!/usr/bin/env python

import os, sys
from setuptools import setup, find_packages

setup(name='emerald_monitor',
      version='0.0.22',
      url='https://github.com/emerald-geomodelling/emerald-monitor',
      author='Benjamin Bloss',
      author_email='bb@emrld.no',
      description='Monitoring utility',
      install_requires=["psutil",
                        "numpy",
                        "pandas",
                        "matplotlib",
                        # "time",
                        # "threading",
                        ],
      extras_require={'test': ["pytest"]},
      long_description="Monitoring utility",
      include_package_data=True,
      packages=find_packages(),
      )
