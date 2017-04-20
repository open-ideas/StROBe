# -*- coding: utf-8 -*-
"""
Created on Thu Feb 06 09:48:07 2014

@author: Ruben Baetens
"""

import os
import numpy as np
import stats

def get_clusters(employment, **kwargs):
    '''
    Find the clusters for weekdays, saturday and sunday for a household member
    of the given eployment type based on the Crosstables given at
    # http://homepages.vub.ac.be/~daerts/Occupancy.html
    '''
    #first go the the correct location
    cdir = os.getcwd()
    PATH = '../Data/Aerts_Occupancy/Crosstables/'
    os.chdir(PATH)
    #create an empty dictionary
    keys = ['wkdy', 'sat', 'son']
    cluDict = dict()
    ##########################################################################
    # we find the cluster for each of the daytypes for the given employment
    # in 'Crosstable_employment.txt'
    for key in keys:
        order = ['U12','FTE','PTE','Unemployed','Retired','School']
        emp_i = order.index(employment)
        data = np.loadtxt('Crosstable_Employment_'+key+'.txt', float).T[emp_i]
        rnd = np.random.random()
        cluster = stats.get_probability(rnd, data[1:], p_type='prob')
        cluDict.update({key:cluster})
    ##########################################################################
    # and return the final cluster id's
    os.chdir(cdir)
    return cluDict

def get_occDict(cluster, **kwargs):
    '''
    Create the dictionary with occupancy data based on the files retrieved from
    Aerts et al. as given at http://homepages.vub.ac.be/~daerts/Occupancy.html
    and stored in 'StROBe/Data/Aerts_Occupancy'.
    '''
    #first go the the correct location
    cdir = os.getcwd()
    DATA_PATH = '../Data/Aerts_Occupancy'
    PATH = DATA_PATH + '/Pattern' + str(cluster)
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
    os.chdir(cdir)
    return occDict

def get_actDict(cluster, **kwargs):
    '''
    Create the dictionary with activity data based on the files retrieved from
    Aerts et al. as given at http://homepages.vub.ac.be/~daerts/Activity.html
    and stored in 'StROBe/Data/Aerts_activity'.
    '''
    #first go the the correct location
    cdir = os.getcwd()
    DATA_PATH = '../Data/Aerts_Activities'
    os.chdir(DATA_PATH)
    # create an empty dictionary
    actDict = dict()
    ##########################################################################
    # first we define the dictionary used as legend for the load file
    act = {0:'pc', 1:'food', 2:'vacuum', 3:'iron', 4:'tv', 5:'audio',
           6:'dishes', 7:'washing', 8:'drying', 9:'shower'}
    ##########################################################################
    # Second we load the activity proclivity functions 'agn'
    # from Patter*cluster*.txt
    FILNAM = 'Pattern'+str(cluster)+'.txt'
    data = np.loadtxt(FILNAM, float)
    for i in range(10):
        actDict.update({act[i]:data.T[i]})
    ##########################################################################
    # and return the final actDict
    actDict.update({'period':600, 'steps':144})
    os.chdir(cdir)
    return actDict
