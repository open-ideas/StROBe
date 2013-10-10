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

class HouseholdTest(unittest.TestCase):
    '''
    Testing the household class.
    '''

    def setUp(self):
        self.name = 'Example'

    def test_creation(self):
        test = residential.Household(self.name)
        self.assertEqual(test.name, self.name)

    def test_simulation(self):
        test = residential.Household('Example')
        test.simulate()

if __name__ == '__main__':
    suite1 = unittest.TestLoader().loadTestsFromTestCase(HouseholdTest)
    #suite2 = ...
    alltests = unittest.TestSuite([suite1])
    unittest.TextTestRunner(verbosity=1).run(alltests)
