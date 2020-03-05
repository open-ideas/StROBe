# -*- coding: utf-8 -*-
"""
Created on Wed Oct 09 15:36:23 2013

@author: Ruben Baetens

Reviewed and automated  Oct 2017, Christina Protopapadaki

Updated in March 2020 to include flow calibration, Christina Protopapadaki
"""

import os
import numpy as np
import json
import cPickle
import residential
from Data.Appliances import set_appliances
from collections import defaultdict
import matplotlib.pyplot as plt

DIR = os.path.dirname(os.path.realpath(__file__))
cwd=os.path.dirname(DIR)+'\\Data'
os.chdir(cwd)

appliances = ['MusicPlayer','HiFi','Iron','Vacuum','Fax','PC','Printer','TV1','TV2','TV3','DVD',
              'TVReceiver','Hob','Oven','Microwave','Kettle','DishWasher',
              'TumbleDryer','WashingMachine','WasherDryer','UprightFreezer', 'ChestFreezer','FridgeFreezer','Refrigerator']
apps_noVal=['AnswerMachine','Clock','CordlessPhone'] # These appliances work constantly: infinate cycles, no calibration needed       
flows=['shortFlow','mediumFlow','showerFlow','bathFlow']

N=100  # amount of simulated households for calibration 
rep=10  # amount of repeated calibration rounds to check convergence
conv=defaultdict(list) #dictionary to save convergence factors per repetition 

for j in range(rep):
    print 'repetition ' , j
    ## Simulate N test households
#    if not os.path.exists(cwd + '\\Calibration'):
#        os.makedirs(cwd + '\\Calibration') # make folder to save test households for validation (if needed)
   
    n = dict()
    # initiate with zeros
    for app in appliances:
        n.update({app:0}) # total cycles
        n.update({app+'_n':0}) # amount of household that have the appliance
    
    for flow in flows:
        n.update({flow:0})
        n.update({flow+'_n':0})
        
    n.update({'Eload':0}) # annual electricity load in kWh
    n.update({'QCon':0}) # annual convective internal heat gains in kWh
    
    for i in range(N):
        if i in range(0,N,10) : print 'Test house '+str(i) + ' created'
        test = residential.Household('Test_'+str(i))
        test.simulate()
        test.roundUp()
###########  to save time & space, don't save individual simulation results       
#        os.chdir(cwd + '\\Calibration')
#        test.pickle()
#        os.chdir(cwd)

    # fill dictionary with data from calibration simulations
#    for i in range(N):
#        if i in range(0,N,10) : print 'Test house '+str(i) + ' being processed'
#        test = cPickle.load(open('Calibration\\Test_'+str(i)+'.p','rb'))
        n.update({'Eload':n['Eload']+ int(np.sum(test.P)/60/1000)}) # annual electricity load in kWh
        n.update({'QCon':n['QCon']+ int(np.sum(test.QCon)/60/1000)}) # annual convective internal heat gains in kWh
        for app in appliances:
            if app in test.n_receptacles.keys(): # if household has the appliance
                n.update({app:n[app]+test.n_receptacles[app]})
                n.update({app+'_n':n[app+'_n']+1.})
        for flow in flows:
            if flow in test.n_flows.keys(): # if household has the flow
                n.update({flow:n[flow]+test.n_flows[flow]})
                n.update({flow+'_n':n[flow+'_n']+1.})
    
    # compare number of cycles with reference eq.cycle_n: "convergence factors"
    print 'Reference over new cycles \n----------'
    for app in appliances:
        eq = residential.Equipment(**set_appliances[app])
        if n[app+'_n'] != 0 and n[app] != 0:
            print app, eq.cycle_n/(n[app]/n[app+'_n']) #average amount of cycles per household
            conv[app].append(eq.cycle_n/(n[app]/n[app+'_n']))
    for flow in flows:
        eq = residential.Equipment(**set_appliances[flow])
        if n[flow+'_n'] != 0 and n[flow] != 0:
            print flow, eq.cycle_n/(n[flow]/n[flow+'_n']) #average amount of cycles per household
            conv[flow].append(eq.cycle_n/(n[flow]/n[flow+'_n']))
    conv['Eload'].append(n['Eload']/N) # average Electricity demand per household
    conv['QCon'].append(n['QCon']/N) # average Convective heat gains per household

    #calculate new calibration factors
    print 'New calibration factors \n-----------'
    for app in appliances:
        eq = residential.Equipment(**set_appliances[app])
        if n[app+'_n'] != 0 and n[app] != 0:
#            print app, (eq.cal*eq.cycle_n/(n[app]/n[app+'_n'])+eq.cal)/2
            set_appliances[app]['cal'] = (eq.cal*eq.cycle_n/(n[app]/n[app+'_n'])+eq.cal)/2
            
    for flow in flows:
        eq = residential.Equipment(**set_appliances[flow])
        if n[flow+'_n'] != 0 and n[flow] != 0:
#            print flow, (eq.cal*eq.cycle_n/(n[flow]/n[flow+'_n'])+eq.cal)/2
            set_appliances[flow]['cal'] = (eq.cal*eq.cycle_n/(n[flow]/n[flow+'_n'])+eq.cal)/2
     
    # rewrite Appliances.py with new calibration factors 
    # change ownership of cold appliances back to original (they are changed in beginning of "residential", 
    # but we want to keep original value in Appliances.py for reference)
    set_appliances['Refrigerator']['owner']=0.430
    set_appliances['FridgeFreezer']['owner']=0.651
    set_appliances['ChestFreezer']['owner']=0.163
    set_appliances['UprightFreezer']['owner']=0.291 
          
    with open('Appliances.py', 'w') as file:
         file.write('set_appliances = \\\n' + json.dumps( set_appliances,file, indent=2))

    #save convergence factors
    with open('Convergence.py', 'w') as file:
        file.write('conv = \\\n' + json.dumps( conv,file, indent=2))

#plot convergence 
conv['Eload']=[x / np.mean(conv['Eload']) for x in conv['Eload']]
conv['QCon']=[x / np.mean(conv['QCon']) for x in conv['QCon']]

colormap = plt.cm.gist_ncar
plt.gca().set_color_cycle([colormap(i) for i in np.linspace(0, 0.9,22)])

plt.plot(range(rep),np.ones(rep), color='k',label='1');
for k in conv:  
    p=plt.plot(range(rep),conv[k],label=k);
    if k=='Eload':
        p[0].set_color('k')
        p[0].set_linestyle('--')
    if k=='QCon':
        p[0].set_color('k')
        p[0].set_linestyle('-.')

plt.legend(loc='lower right');
plt.gca().grid()
plt.show()
