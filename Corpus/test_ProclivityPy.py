# -*- coding: utf-8 -*-
"""
Created on Wed Oct 09 15:36:23 2013

@author: Ruben Baetens
"""

import os

STR = ['\\Corpus','\\Data']
DIR = os.path.dirname(os.path.realpath(__file__))

os.chdir(os.path.dirname(DIR)+STR[0])
import residential

os.chdir(os.path.dirname(DIR)+STR[1])

test = residential.Household('Example')
test.simulate()
