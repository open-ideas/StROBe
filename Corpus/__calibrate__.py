# -*- coding: utf-8 -*-
"""
Created on Wed Oct 09 15:36:23 2013

@author: Ruben Baetens

Reviewed and automated  Oct 2017, Christina Protopapadaki
"""

import os
import json
import cPickle
import residential
from Data.Appliances import set_appliances
from collections import defaultdict
import matplotlib.pyplot as plt

DIR = os.path.dirname(os.path.realpath(__file__))
cwd=os.path.dirname(DIR)+'\\Data'
os.chdir(cwd)

appliances = ['AnswerMachine','MusicPlayer','Clock','CordlessPhone','HiFi',
              'Iron','Vacuum','Fax','PC','Printer','TV1','TV2','TV3','DVD',
              'TVReceiver','Hob','Oven','Microwave','Kettle','DishWasher',
              'TumbleDryer','WashingMachine','WasherDryer']

flows = ['shortFlow','mediumFlow','showerFlow','bathFlow']

N=500 # amount of simulated households for calibration 
rep=10 # amount of repeated calibration rounds to check convergence
conv=defaultdict(list) #dictionary to save convergence factors per repetition 

for j in range(rep):
    print 'repetition ' , j
    ## Simulate N test households
    if not os.path.exists(cwd + '\\Calibration'):
        os.makedirs(cwd + '\\Calibration') # make folder to keep test households for validation 
    for i in range(N):
        if i in range(0,N,10) : print 'Test house '+str(i) + ' created'
        test = residential.Household('Test_'+str(i))
        test.simulate()
        test.roundUp()
        os.chdir(cwd + '\\Calibration')
        test.pickle()
        os.chdir(cwd)
    
    n = dict()
    # initiate with zeros
    for app in appliances:
        n.update({app:0}) # total cycles
        n.update({app+'_n':0}) # amount of household that have the appliance
    
    for flow in flows:
        n.update({flow:0})
        n.update({flow+'_n':0})
    
    # fill dictionary with data from calibration simulations
    for i in range(N):
        if i in range(0,N,10) : print 'Test house '+str(i) + ' checked'
        test = cPickle.load(open('Calibration\\Test_'+str(i)+'.p','rb'))
        for app in appliances:
            if app in test.n_receptacles.keys(): # if household has the appliance
                n.update({app:n[app]+test.n_receptacles[app]})
                n.update({app+'_n':n[app+'_n']+1.})
    
    # compare number of cycles with reference: "convergence factors"
    print 'Reference over new cycles \n----------'
    for app in appliances:
        eq = residential.Equipment(**set_appliances[app])
        if n[app+'_n'] != 0 and n[app] != 0:
            print app, eq.cycle_n/(n[app]/n[app+'_n']) #average amount of cycles per household
         #   conv.update({app:eq.cycle_n/(n[app]/n[app+'_n'])})
            conv[app].append(eq.cycle_n/(n[app]/n[app+'_n']))

    #calculate new calibration factors
    print 'New calibration factors \n-----------'
    for app in appliances:
        eq = residential.Equipment(**set_appliances[app])
        if n[app+'_n'] != 0 and n[app] != 0:
            print app, (eq.cal*eq.cycle_n/(n[app]/n[app+'_n'])+eq.cal)/2
            set_appliances[app]['cal'] = (eq.cal*eq.cycle_n/(n[app]/n[app+'_n'])+eq.cal)/2
     
    # rewrite Appliances.py with new calibration factors        
    with open('Appliances.py', 'w') as file:
         file.write('set_appliances = \\\n' + json.dumps( set_appliances,file, indent=2))

#save convergence factors
with open('Convergence.py', 'w') as file:
    file.write('conv = \\\n' + json.dumps( conv,file, indent=2))

#plot convergence 
for k in conv:  
    plt.plot(range(rep),conv[k]);
plt.axis();
plt.legend(conv.keys(), loc='lower right');
plt.show()
