# -*- coding: utf-8 -*-
"""
Created on Thu Feb 06 09:48:07 2014

@author: Ruben Baetens
"""

import os
import numpy as np

DATA_PATH = 'E:\\3_PhD\\6_Python\\StROBe\\Data\\Aerts_Occupancy'

def get_occDict(cluster, **kwargs):
    """
    Create the dictioarry with occupancy data based on the files retrieved from
    Aerts et al. as given at http://homepages.vub.ac.be/~daerts/Occupancy.html
    and stored in 'StROBe/Data/Occupancy'.
    """
    #first go the the correct location
    PATH = DATA_PATH + '\\Pattern' + str(cluster)
    os.chdir(PATH)
    # create an empty dictionary
    occDict = dict()
    ##########################################################################
    # first we load the occupancy start states 'oss' from StartStates.txt
    oss = dict()    
    data = np.loadtxt('StartStates.txt', float)
    for i in range(len(data)):
        oss.update({str(i+1):data[i]})
    # and add the 'oss' data to the occupancy dictionary
    occDict.update({'oss':oss})
    ##########################################################################
    # Second we load the occupancy transitions state probabilities 'osn' 
    # from TransitionProbability.txt
    data = np.loadtxt('TransitionProbability.txt', float)
    for i in range(3):
        osn_i = dict()
        for j in range(48):
            osn_i.update({str(j+1):data[i*48+j]})
        # and add the 'osn_i' data to the occupancy dictionary
        occDict.update({'osn_'+str(i+1):osn_i})
    ##########################################################################
    # Third we load the occupancy transitions state probabilities 'osn' 
    # from DurationProbability.txt
    data = np.loadtxt('DurationProbability.txt', float)
    for i in range(3):
        oln_i = dict()
        for j in range(48):
            oln_i.update({str(j+1):data[i*48+j]})
        # and add the 'osn_i' data to the occupancy dictionary
        occDict.update({'oln_'+str(i+1):oln_i})
    ##########################################################################
    # and return the final occDict
    return occDict

a = get_occDict(1)

print type(a)


