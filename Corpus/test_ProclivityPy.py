# -*- coding: utf-8 -*-
"""
Created on Wed Oct 09 15:36:23 2013

@author: Ruben Baetens
"""

import os
import unittest
import residential

DIR = os.path.dirname(os.path.realpath(__file__))
os.chdir(os.path.dirname(DIR)+'\\Data')

class TestSequenceHouseholdFunctions(unittest.TestCase):
    '''
    Testing the household class.
    '''
    def CreationAndSimulation(self):
        test = residential.Household('Example')
        test.simulate()

if __name__ == '__main__':
    unittest.main()
