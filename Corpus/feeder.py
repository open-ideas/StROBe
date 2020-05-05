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
    The Community class defines a set of households.
    '''
    
    def __init__(self, name, nBui, path, sh_K=True):
        '''
        Create the community based on number of households and simulate for
        output towards IDEAS model.
        '''
        self.name = name
        self.nBui = nBui
        self.sh_K = sh_K #defines whether space heating set-point temperature will be written in K (otherwise deg Celsius)
        
        # we create, simulate and pickle all 'nBui' buildings
        self.simulate(path)
        # then we loop through all variables and output as single file
        # for reading in IDEAS.mo
        os.chdir(path)
        self.output()
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
            os.chdir(path)
            hou.pickle()
            os.chdir(cwd)

    def output(self):
        '''
        Output the variables for the dwellings in the feeder as a *.txt readable
        for Modelica.
        '''
        #######################################################################
        # we loop through all households for loading all variables 
        # which are stored in the object pickle.
        print ('loading pickled household objects')
        # first load one house and grab dictionary of variables: 
        hou = cPickle.load(open(str(self.name)+'_0.p','rb'))
        variables=hou.variables # dictionary with explanation of main outputs
        dat=dict.fromkeys(variables.keys(),[]) 
        for i in range(self.nBui): # loop over all households
         #   print(i)
            hou = cPickle.load(open(str(self.name)+'_'+str(i)+'.p','rb')) #load results
            for variable in variables.keys(): #loop over variables       
                var = eval('hou.'+variable)
                if variable in ['sh_day','sh_bath','sh_night'] and self.sh_K: # if space heating setting and Kelvin required
                    variables[variable]=variables[variable].replace("Celsius", "Kelvin") # change variable explanation
                    var=var+273.15 # make it in Kelvin
                if len(dat[variable]) != 0: 
                    dat[variable] = np.vstack((dat[variable],var)) # add new column
                else: # if firts household (dat[variable] was empty)
                    dat[variable] = var # set equal to var
        
        
        #######################################################################
        # and output the array to txt
        print ('writing')
        for variable in variables.keys():
            print (variable)
            tim = np.linspace(0,31536000,dat[variable].shape[1]) # create time column (always annual simulation=default)
            data = np.vstack((tim,dat[variable]))
            # print as header the necessary for IDEAS, plus explanation for each variable
            hea ='#1 \ndouble data('+str(int(data.shape[1]))+','+str(int(data.shape[0]))+') \n#' + variables[variable]
            np.savetxt(fname=variable+'.txt', X=data.T, header=hea,comments='', fmt='%.7g')


