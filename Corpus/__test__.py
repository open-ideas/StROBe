# -*- coding: utf-8 -*-
"""
Created on Wed Oct 09 15:36:23 2013

@author: Ruben Baetens
"""

import os
import unittest
import residential
import feeder
import cPickle

DIR = os.path.dirname(os.path.realpath(__file__))
os.chdir(os.path.dirname(DIR)+'\\Data')

class EquipmentTest(unittest.TestCase):
    '''
    Testing the equipment class.
    '''

class HouseholdTest(unittest.TestCase):
    '''
    Testing the household class.
    '''

    def setUp(self):
        self.name = 'Example'

    def test_creation_1(self):
        test = residential.Household(self.name)
        self.assertEqual(test.name, self.name)
        self.assertTrue(len(test.apps)!=0)
        self.assertTrue(len(test.members)!=0)
        self.assertTrue(len(test.clusters)!=0)
        print '\n'

    def test_creation_2(self):
        test = residential.Household(self.name, members=['FTE','PTE'])
        self.assertEqual(test.name, self.name)
        self.assertTrue(len(test.apps)!=0)
        self.assertTrue(len(test.members)!=0)
        self.assertTrue(len(test.clusters)!=0)
        print '\n'
        
    def test_simulation(self):
        test = residential.Household('Example')
        test.simulate()
        self.assertTrue(len(test.occ)!=0)
        print '\n'

    def test_pickle(self):
        test = residential.Household('Example')
        test.simulate()
        test.pickle()
        bistest = cPickle.load(open('Example.p','rb'))
        self.assertTrue(len(bistest.occ)!=0)
        print '\n'

class FeederTest(unittest.TestCase):
    '''
    Testing of the IDEAS_Feeder class
    '''
    
    def setUp(self):
        self.name = 'Example'
        
    def test_creation1(self):
        test = feeder.IDEAS_Feeder(self.name, 2, r'E:\3_PhD\6_Python\Test')
        self.assertEqual(test.name, self.name)
        print '\n'

        
class CommunityTest(unittest.TestCase):
    '''
    Testing the community class.²
    '''

if __name__ == '__main__':
    suite1 = unittest.TestLoader().loadTestsFromTestCase(FeederTest)
    #suite2 = ...
    alltests = unittest.TestSuite([suite1])
    unittest.TextTestRunner(verbosity=1).run(alltests)
