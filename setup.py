#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Jan 15 23:18:10 2017

@author: danw
"""

from setuptools import setup, find_packages

setup(
      name='archon_emu',
      packages=find_packages(),
      scripts = ['archon_emu/scripts/dump_timing_script.py',
                 'archon_emu/scripts/dump_timing_states.py']
)