# -*- coding: utf-8 -*-
"""
Created on Wed Oct 09 15:36:23 2013

@author: Ruben Baetens
"""

import os
import ast
import residential
import cPickle

DIR = os.path.dirname(os.path.realpath(__file__))
os.chdir(os.path.dirname(DIR)+'\\Data')

#for i in range(5):
#    test = residential.Household('Test_'+str(i))
#    test.simulate()
#    test.pickle()

appliances = ['AnswerMachine','MusicPlayer','Clock','CordlessPhone','HiFi',
              'Iron','Vacuum','Fax','PC','Printer','TV1','TV2','TV3','DVD',
              'TVReceiver','Hob','Oven','Microwave','Kettle','DishWasher',
              'TumbleDryer','WashingMachine','WasherDryer']

flows = ['shortFlow','mediumFlow','showerFlow','bathFlow']

n = dict()

for app in appliances:
    n.update({app:0})
    n.update({app+'_n':0})

for flow in flows:
    n.update({flow:0})
    n.update({flow+'_n':0})

for i in range(5):
    print i
    test = cPickle.load(open('Test_'+str(i)+'.p','rb'))
    for app in appliances:
        if app in test.n_receptacles.keys():
            n.update({app:n[app]+test.n_receptacles[app]})
            n.update({app+'_n':n[app+'_n']+1})

dataset = ast.literal_eval(open('Appliances.py').read())

for app in appliances:
    eq = residential.Equipment(**dataset[app])
    if n[app+'_n'] != 0 and n[app] != 0:
        print app, eq.cycle_n/(n[app]/n[app+'_n'])

