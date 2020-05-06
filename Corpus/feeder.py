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
    
    def __init__(self, name, nBui, path, sh_K=True, save_indiv=True):
        '''
        Create the community based on number of households and simulate for
        output towards IDEAS model.
        Main functions are:
        - __init__(name, nBui, path, sh_K=True, save_indiv=True), which creates the feeder object with all necessary parameters.
        - self.simulate(), which creates and simulates all 'nBui' buildings, collects outputs and optionally saves individual results
        - self.output(), which saves all outputs as single files for reading in IDEAS.mo
        - self.load(), which loads previously simulated and saved individual household pickled results
        '''
        self.name = name
        self.nBui = nBui
        self.path = path
        self.sh_K = sh_K #defines whether space heating set-point temperature will be written in K (otherwise deg Celsius)   
        self.save_indiv= save_indiv #defines whether individual household results will be saved as pickled files
        print '\n'
        print ' - Feeder %s created.' % str(self.name)

    def simulate(self):
        '''
        Simulate all households in the depicted feeder and collect results
        '''
        #######################################################################
        # we loop through all households for creation, simulation collection of outputs and optionally pickling.
        cwd = os.getcwd()
        for i in range(self.nBui):
            hou = residential.Household(str(self.name)+'_'+str(i))
            hou.simulate()           
            
            if i==0:# if first household, grab dictionary of variables and initiate dictionary for data collection
                variables=hou.variables # dictionary with explanation of main outputs
                dat=dict.fromkeys(variables.keys(),[]) # dictionary where outputs are stored
            for variable in variables.keys(): #loop over variables       
                var = eval('hou.'+variable)
                if variable in ['sh_day','sh_bath','sh_night'] and self.sh_K: # if space heating setting and Kelvin required
                    variables[variable]=variables[variable].replace("Celsius", "Kelvin") # change variable explanation
                    var=var+273.15 # make it in Kelvin
                if len(dat[variable]) != 0: 
                    dat[variable] = np.vstack((dat[variable],var)) # add new column
                else: # if firts household (dat[variable] was empty)
                    dat[variable] = var # set equal to var
            if self.save_indiv: # save pickled files of individual households if asked         
                os.chdir(self.path)
                hou.pickle()
                os.chdir(cwd)
            
        self.variables=variables # dictionary with explanation of main outputs
        self.dat=dat # dictionary where outputs are stored
        print '\n'
        print ' - Feeder %s simulated.' % str(self.name)
        
    def output(self):
        '''
        Output the variables for the dwellings in the feeder as a *.txt readable
        for Modelica.
        '''
        #######################################################################
        # write the data already collected to txt files
        print ('writing')
        os.chdir(self.path)
        for variable in self.variables.keys():
            print (variable)
            tim = np.linspace(0,31536000,self.dat[variable].shape[1]) # create time column (always annual simulation=default)
            data = np.vstack((tim,self.dat[variable]))
            # print as header the necessary for IDEAS, plus explanation for each variable
            hea ='#1 \ndouble data('+str(int(data.shape[1]))+','+str(int(data.shape[0]))+') \n#' + self.variables[variable]
            np.savetxt(fname=variable+'.txt', X=data.T, header=hea,comments='', fmt='%.7g')

        print '\n'
        print ' - Feeder %s outputted.' % str(self.name)
        
    def load(self):
        '''
        Load results from previously simulated feeder.
        This is useful only when individual household results are available and need to be reloaded and re-outputted.
        Initiation of a feeder object with the correct parameters (name, path, nBui, sh_K) is necessary. 
        The output() function can be called afterwards to save .txt files for IDEAS. 
        '''
        #######################################################################      
        # loop through all households for loading all variables 
        # which are stored in the object pickle.
        print ('loading pickled household objects')
        os.chdir(self.path)
        # first load one house and grab dictionary of variables: 
        hou = cPickle.load(open(str(self.name)+'_0.p','rb'))
        variables=hou.variables # dictionary with explanation of main outputs
        dat=dict.fromkeys(variables.keys(),[]) 
        for i in range(self.nBui): # loop over all households
            print(i)
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
        
        self.variables=variables # dictionary with explanation of main outputs
        self.dat=dat # dictionary where outputs are stored
        print '\n'
        print ' - Feeder %s loaded.' % str(self.name)