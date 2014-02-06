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
    ss = dict()    
    data = np.loadtxt('StartStates.txt', float)
    for i in range(len(data)):
        ss.update({str(i+1):data[i]})
    # and add the 'oss' data to the occupancy dictionary
    occDict.update({'ss':ss})
    ##########################################################################
    # Second we load the occupancy transitions state probabilities 'osn' 
    # from TransitionProbability.txt
    data = np.loadtxt('TransitionProbability.txt', float)
    for i in range(3):
        os_i = dict()
        for j in range(48):
            os_i.update({str(j+1):data[i*48+j]})
        # and add the 'osn_i' data to the occupancy dictionary
        occDict.update({'os_'+str(i+1):os_i})
    ##########################################################################
    # Third we load the Markov time density 'ol' from DurationProbability.txt
    data = np.loadtxt('DurationProbability.txt', float)
    for i in range(3):
        ol_i = dict()
        for j in range(48):
            ol_i.update({str(j+1):data[i*48+j]})
        # and add the 'osn_i' data to the occupancy dictionary
        occDict.update({'ol_'+str(i+1):ol_i})
    ##########################################################################
    # and return the final occDict
    return occDict

a = get_occDict(1)

print type(a)


