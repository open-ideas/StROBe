# -*- coding: utf-8 -*-
"""
Created on Mon October 07 16:16:10 2013

@author: Ruben Baetens
"""

import random
import numpy as np
import time

import stats

from datetime import timedelta, datetime
import ast

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
                        cons = stats.get_probability(random.random(), prob, p_type='prob')+3
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

    def simulate(self):
        '''
        The simulate function includes the simulation of the household 
        occupancies, plug loads, lightinh loads and hot water tappings.
        '''
        def __occupancy__(self):
            '''
            Simulation of a number of 'nDay' days based on cluster 'BxDict'.
            - Including weekend days,
            - starting from a regular monday at 4:00 AM.
            '''
            def check(occday, daydict):
                '''
                We set a check which becomes True if the simulated day behaves 
                according to the cluster, as a safety measure for impossible
                solutions.
                '''
                # First we check if the simulated occ-chain has the same shape
                location = np.zeros(1, dtype=int)
                reduction = occday[0]*np.ones(1, dtype=int)
                for i in range(len(occday)-1):
                    if occday[i+1] != occday[i]:
                        location = np.append(location, i+1)
                        reduction = np.append(reduction,occday[i+1])
                shape = np.array_equal(reduction, daydict['RED'])
                # And second we see if the chain has nu sub-30 min differences
                minlength = 99
                for i in location:
                    j = 0
                    while occday[i+j] == occday[i] and i+j < len(occday)-1:
                        j = j+1
                    if j < minlength:
                        minlength = j
                # and we neglect the very short presences of 20 min or less
                length = not minlength < 3
                # both have to be true to allow continuation
                return shape and length
        
            def dayrun(start, daydict):
                '''
                Simulation of a single day according to start state 'start'
                and the stochastics stored in cluster 'BxDict'and daytype 'Bx'.
                '''
                # set the default dayCheck at False
                daycheck = False
                endtime = datetime.utcnow() + timedelta(seconds = 10)
                # and then keep simulating a day until True
                while daycheck == False:
                    # set start state conditions
                    tbin = 0
                    occs = np.zeros(144, dtype=int)
                    occs[0] = start
                    t48 = np.array(sorted(list(range(1, 49)) * 3))
                    dt = stats.duration(daydict, start, t48[0])
                    # and loop sequentially transition and duration functions
                    while tbin < 143:
                        tbin += 1
                        if dt == 0:
                            occs[tbin] = stats.transition(daydict, occs[tbin-1], t48[tbin])
                            dt = stats.duration(daydict, occs[tbin], t48[tbin]) - 1
                            # -1 is necessary, as the occupancy state already started
                        else:
                            occs[tbin] = occs[tbin - 1]
                            dt += -1
                    # whereafer we control if this day is ok
                    daycheck = check(occs, daydict)
                    # and we include a break if the while takes to long 
                    if datetime.utcnow() > endtime:
                        break
                # and return occs-array if daycheck is ok according to Bx
                return occs
    
            # first we read the stored cluster data for occupancy
            occ_week = []
            for member in self.clusters:
                dataset = dict()
                for day in ['wkdy','sat','son']:
                    filnam = 'Occupancies\\'+member[day]+'.py'
                    dataset[day] = ast.literal_eval(open(filnam).read())
                # get the first duration of the start state
                start = stats.startstate(dataset['wkdy'])
                # and run all three type of days
                wkdy = dayrun(start, dataset['wkdy'])
                sat = dayrun(wkdy[-1], dataset['sat'])
                son = dayrun(sat[-1], dataset['son'])
                # and concatenate 
                week = np.concatenate((np.tile(wkdy, 5), sat, son))
                occ_week.append(week)
            # go back and store the occupancy states
            self.occ = occ_week
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
            
