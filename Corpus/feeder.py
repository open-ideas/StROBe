# -*- coding: utf-8 -*-
"""
Created on Mon Feb 24 11:39:35 2014

@author: Ruben
"""

import residential
import cPickle
import numpy as np
import os

class IDEAS_Feeder(object):
    '''
    The Community class defines a set of hosueholds.
    '''
    
    def __init__(self, name, nBui, path):
        '''
        Create the community based on number of households and simulate for
        output towards IDEAS model.
        '''
        self.name = name
        self.nBui = nBui
        # we create, simulate and pickle all 'nBui' buildings
        self.simulate(path)
        # then we loop through all variables and output as single file
        # for reading in IDEAS.mo
        os.chdir(path)
        variables = ['P','Q','QRad','QCon','mDHW','sh_day','sh_bath','sh_night']
        self.output(variables)
        # and conclude
        print '\n'
        print ' - Feeder %s outputted.' % str(self.name)

    def simulate(self, path):
        '''
        Simulate all households in the depicted feeder
        '''
        #######################################################################
        # we loop through all households for creation, simulation and pickling.
        # whereas the output is done later-on.
        cwd = os.getcwd()
        for i in range(self.nBui):
            hou = residential.Household(str(self.name)+'_'+str(i))
            hou.simulate()
            hou.roundUp()
            os.chdir(path)
            hou.pickle()
            os.chdir(cwd)

    def output(self, variables):
        '''
        Output the variables for the dwellings in the feeder as a *.txt readable
        for Modelica.
        '''
        #######################################################################
        # we loop through all households for loading all variables 
        # which are stored in the object pickle.
        print ('loading pickled household objects')
        dat=dict.fromkeys(variables,[])
        for i in range(self.nBui):
         #   print(i)
            hou = cPickle.load(open(str(self.name)+'_'+str(i)+'.p','rb'))
            for variable in variables:       
                var = eval('hou.'+variable)
                if len(dat[variable]) != 0:
                    dat[variable] = np.vstack((dat[variable],var))
                else:
                    dat[variable] = var
        
        
        #######################################################################
        # and output the array to txt
        print ('writing')
        for variable in variables:
            print (variable)
            tim = np.linspace(0,31536000,dat[variable].shape[1])
            data = np.vstack((tim,dat[variable]))
            hea ='#1 \ndouble data('+str(int(data.shape[1]))+','+str(int(data.shape[0]))+')'
            np.savetxt(fname=variable+'.txt', X=data.T, header=hea,comments='', fmt='%.10g')


