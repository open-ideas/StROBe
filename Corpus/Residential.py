# -*- coding: utf-8 -*-
"""
Created on Mon October 07 16:16:10 2013

@author: Ruben Baetens
"""

import random
import numpy as np
import os
import json
import cPickle
import time

from datetime import timedelta, datetime
import ast

def get_probability(rnd, prob, p_type='cum'):
    '''
    Find the x-value in a given comulative probability 'prob_cum' based on a 
    given random y-value 'rnd'.
    '''
    if p_type != 'cum':
        prob = np.cumsum(prob)
        prob /= max(prob)
    idx = 1
    while rnd >= prob[idx-1]:
        idx += 1
    return idx

class Household(object):
    '''
    The Household class is the main class of ProclivityPy, defining the
    household composition as input or randomized based on statistics and
    allowing simulation of the household for building energy simulations.
    
    Main functions are:
        - __init__(), which ...
        - self.parameterize(), which ...
        - self.simulate(), which ...
    '''
    
    def __init__(self, name, **kwargs):
        '''
        Initiation of Househod object.
        '''
        # check on correct parameter input for use of functions as name should
        # be a string.
        try:
            if not isinstance(name, str):
                raise ValueError('Given name %d is not a string' % str(name))
        except:
            raise TypeError('give another name')
        # first define the name of the household object
        self.creation = time.asctime()
        self.name = name
        self.parameterize()

    def parameterize(self, **kwargs):
        '''
        Get a household definition for occupants and present appliances based
        on average statistics or the given kwargs.
        '''
        # get the occupant types
        def members(**kwargs):
            '''
            Define the employment type of all household members based on time
            use survey statistics or the given kwargs.
            '''
            members = []
            # First we check if membertypes are given as **kwargs
            if kwargs.has_key('members'):
                if isinstance(kwargs['members'], list):
                    members = kwargs['members']
                else:
                    raise TypeError('Given membertypes is no List of strings.')
            # If no types are given, random statististics are applied
            else:
                dataset = ast.literal_eval(open('Households.py').read())
                key = random.randint(0,len(dataset))
                members = dataset[key]
                print 'Household members employment are %s' % str(members)
            # And return the members as list fo strings
            return members
        # get the available appliances
        def appliances():
            '''
            Define the pressent household appliances based on average national
            statistics independent of household member composition.
            '''
            # Loop through all appliances and pick randomly based on the 
            # rate of ownership.
            dataset = ast.literal_eval(open('Appliances.py').read())
            app_n = []
            for app in dataset:
                obj = Appliance(**dataset[app])
                owner = obj.owner <= random.random()
                app_n.append(app) if owner else None
            return app_n            
        # and allocate the householdmembers to clusters
        def clusters(members):
            '''
            Allocate each household member to the correct cluster based on the 
            members occupation in time use survey data.
            '''
            clusters = []
            # loop for every individual in the household
            dataset = ast.literal_eval(open('Clusters.py').read())
            for ind in members:
                if ind != 'U12':
                    C = {}
                    # and loop for every type of day
                    for day in ['wkdy', 'sat', 'son']:
                        prob = dataset[day][ind]
                        cons = get_probability(rand(), prob, p_type='prob')+3
                        C.update({day : 'C'+str(cons)})
                    clusters.append(C)
            # and return the list of clusters
            return clusters
        # and run both
        self.members = members()
        self.apps = appliances()
        self.clusters = clusters(self.members)
        # and return
        return None
        
class Appliance(object):
    """
    Data records for appliance simulation based on generated activity and
    occupancy profiles
    """
    # All object parameters are given in kwargs
    def __init__(self, **kwargs):
        # copy kwargs to object parameters 
        for (key, value) in kwargs.items():
            setattr(self, key, value)
            
