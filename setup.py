#!/usr/bin/env python

import os
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

setup(name='emerald_monitor',
      version='0.1.0',
      url='https://github.com/YmerFlow/emerald-monitor',
      author='Benjamin Bloss',
      author_email='benjamin@blossgeo.com',
      description='Monitor CPU and RAM usage of a Python process between start and stop',
      long_description=long_description,
      long_description_content_type='text/markdown',
      license='MIT',
      classifiers=[
          'Programming Language :: Python :: 3',
          'Topic :: System :: Monitoring',
      ],
      python_requires='>=3.9',
      install_requires=["psutil",
                        "numpy",
                        "pandas",
                        "matplotlib",
                        ],
      extras_require={'test': ["pytest"]},
      include_package_data=True,
      packages=find_packages(exclude=["tests", "tests.*"]),
      )
