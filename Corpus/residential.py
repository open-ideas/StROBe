# -*- coding: utf-8 -*-
"""
Created on Mon October 07 16:16:10 2013

@author: Ruben Baetens
"""

import random
import numpy as np
import time
import stats
import datetime
import calendar
import ast
import os
import cPickle
import itertools


class Community(object):
    '''
    The Community class defines a set of hosueholds.
    '''
    
    def __init__(self, name, **kwargs):
        '''
        Initiation of Community object.
        '''
        
        return None

    def simulate(self):
        '''
        Simulation of the Community object.
        '''
        
        return None
        
    def output(self):
        '''
        Output of the simulation results for IDEAS.mo-simulation.
        '''
        
        return None


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
        Initiation of Household object.
        '''
        # input ###############################################################
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
            # And return the members as list fo strings
            return members

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
                obj = Equipment(**dataset[app])
                owner = obj.owner <= random.random()
                app_n.append(app) if owner else None
            return app_n            

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
                        cons = stats.get_probability(random.random(), 
                                                     prob, p_type='prob')+3
                        C.update({day : 'C'+str(cons)})
                    clusters.append(C)
            # and return the list of clusters
            return clusters
        # and run both
        self.members = members()
        self.apps = appliances()
        self.clusters = clusters(self.members)
        # and return
        print 'Household-object created and parameterized.'
        print ' - Employment types are %s' % str(self.members)
        summary = [] #loop dics and remove dubbles
        for member in self.clusters:
            summary += member.values()
        print ' - Set of clusters is %s' % str(list(set(summary)))

        return None

    def simulate(self, year=2013):
        '''
        The simulate function includes the simulation of the household 
        occupancies, plug loads, lighting loads and hot water tappings.
        '''

        self.year = year
        self.__chronology__(year)
        self.__occupancy__()
        self.__plugload__()

    def __chronology__(self, year):
        '''
        A basic internal calendar is made, storing the days and months of the
        depicted simulating year.
        - Monday == 0 ... Sunday == 6
        '''
        # first we determine the first week of the depicted year
        fdoy = datetime.datetime(year,1,1).weekday()
        fweek = range(7)[fdoy:]
        # whereafter we fill the complete year
        nday = 366 if calendar.isleap(year) else 365
        day_of_week = (fweek+53*range(7))[:nday]
        # and return the day_of_week for the entire year
        self.dow = day_of_week
        self.nday = nday
        return None

    def __occupancy__(self, min_form = True, min_time = False):
        '''
        Simulation of a number of days based on cluster 'BxDict'.
        - Including weekend days,
        - starting from a regular monday at 4:00 AM.
        '''
        def check(occday, RED, min_form = True, min_time = False):
            '''
            We set a check which becomes True if the simulated day behaves 
            according to the cluster, as a safety measure for impossible
            solutions.
            '''

            # script 1 ########################################################
            # First we check if the simulated occ-chain has the same shape
            shape = True
            if min_form:
                location = np.zeros(1, dtype=int)
                reduction = occday[0]*np.ones(1, dtype=int)
                for i in range(len(occday)-1):
                    if occday[i+1] != occday[i]:
                        location = np.append(location, i+1)
                        reduction = np.append(reduction,occday[i+1])
                shape = np.array_equal(reduction, RED)

            # script 2 ########################################################
            # And second we see if the chain has nu sub-30 min differences
            length = True
            if min_time:
                minlength = 99
                for i in location:
                    j = 0
                    while occday[i+j] == occday[i] and i+j < len(occday)-1:
                        j = j+1
                    if j < minlength:
                        minlength = j
                # and we neglect the very short presences of 20 min or less
                length = not minlength < 3

            # output ##########################################################
            # both have to be true to allow continuation, and we return boolean
            return shape and length

        def dayrun(start, cluster):
            '''
            Simulation of a single day according to start state 'start'
            and the stochastics stored in cluster 'BxDict'and daytype 'Bx'.
            '''

            # script ##########################################################
            # we set the default daycheck at False for the first run and loop
            # creating days while False, meaning while the simulated day does
            # not correspond to the agreed-on rules in check().
            daycheck = False
            end = datetime.datetime.utcnow() + datetime.timedelta(seconds = 10)
            # defin the corresponding MCSA object from stats.py depicting a 
            # Monte Carlo Survival Analysis object.
            SA = stats.MCSA(cluster)
            # and then keep simulating a day until True
            while daycheck == False:
                # set start state conditions
                tbin = 0
                occs = np.zeros(144, dtype=int)
                occs[0] = start
                t48 = np.array(sorted(list(range(1, 49)) * 3))
                dt = SA.duration(start, t48[0])
                # and loop sequentially transition and duration functions
                while tbin < 143:
                    tbin += 1
                    if dt == 0:
                        occs[tbin] = SA.transition(occs[tbin-1], t48[tbin])
                        dt = SA.duration(occs[tbin], t48[tbin]) - 1
                        # -1 is necessary, as the occupancy state already started
                    else:
                        occs[tbin] = occs[tbin - 1]
                        dt += -1
                # whereafer we control if this day is ok
                daycheck = check(occs, SA.RED)
                # and we include a break if the while-loop takes to long until
                # check()-conditions are fulfilled.
                if datetime.datetime.utcnow() > end:
                    break

            # ouput ###########################################################
            # return occupants array if daycheck is ok according to Bx
            return occs

        def merge(occ):
            '''
            Merge the occupancy profiles of all household members to a single
            profile denoting the most active state of all members.
            '''
            # scirpt ##########################################################
            # We start defining an array of correct length filled with the 
            # least active state and loop to see if more-active people are
            # present at the depicted moment.
            occs = int(3)*np.ones(len(occ[0]))
            for member in occ:
                for to in range(len(member)):
                    if member[to] < occs[to]:
                        occs[to] = member[to] 

            # ouput ###########################################################
            # return the merge occupancy states
            return occs

        # script ##############################################################
        # We change the directory to to location where the data is stored,
        # and run the three type of days, ie. wkdy, sat and son succesively
        # by which we can create a typical week.
        cdir = os.getcwd()
        os.chdir(cdir+'\\Occupancies')
        occ_week = []
        for member in self.clusters:
            startstate = 2 #4.00 AM
            wkdy = dayrun(startstate, member['wkdy'])
            sat = dayrun(wkdy[-1], member['sat'])
            son = dayrun(sat[-1], member['son'])
            # and concatenate 
            week = np.concatenate((np.tile(wkdy, 5), sat, son))
            occ_week.append(week)
        # A merge occupancy is created depicted the most active state of all
        # household members, later-on used for set-point temperatures.
        occ_merg = merge(occ_week)
        # and combine the weekly occupancy states for the entire year by 
        # repeating them every week and correcting for the first day of year,
        # including for the merged occupancy.
        bins = 144
        tstart = bins*self.dow[0]
        tstop = tstart + bins*self.nday
        occ_year = []
        for line in range(len(occ_week)):
            occ_year.append(np.tile(occ_week,54)[line][tstart:tstop])
        occ_merged = []
        occ_merged.append(np.tile(occ_merg,54)[tstart:tstop])

        # output ##############################################################
        # chdir back to original and return the occupancy states to the class
        # object.
        os.chdir(cdir)
        self.occ = occ_year
        self.occ_m = occ_merged
        # and print statements
        presence = [to for to in self.occ_m[0] if to < 2]
        hours = len(presence)/6
        print ' - Total presence time is %s out of 8760 hours' % str(hours)
        print '   (being %s percent)' % str(hours*100/8760)
        
        return None

    def __plugload__(self):
        '''
        Simulation of the electric load based on the occupancies, cluster 
        and the present appliances.
        - Including weekend days,
        - starting from a regular monday at 4:00 AM.
        '''

        def receptacles(self):
            '''
            Simulation of the receptacle loads.
            '''

            dataset = ast.literal_eval(open('Appliances.py').read())
            # define number of minutes
            nmin = self.nday * 1440
            # determine all transitions of the appliances depending on the appliance
            # basic properties, ie. stochastic versus cycling power profile
            cdir = os.getcwd()
            os.chdir(cdir+'\\Activities')

            power = np.zeros(nmin+1)
            radi = np.zeros(nmin+1)
            conv = np.zeros(nmin+1)
            cluster = self.clusters[0]['wkdy']
            nday = self.nday
            dow = self.dow
            occ_m = self.occ_m[0]
            for app in self.apps:
                # create the equipment object with data from dataset.py
                eq = Equipment(**dataset[app])
                r_app = eq.simulate(nday, dow, cluster, occ_m)
                power += r_app['P']
                radi += r_app['QRad']
                conv += r_app['QCon']
            # a new time axis for power output is to be created as a different
            # time step is used in comparison to occupancy
            time = 4*60*600 + np.arange(0, (nmin+1)*60, 60)
    
            react = np.zeros(nmin+1)
            os.chdir(cdir)

            result = {'time':time, 'occ':None, 'P':power, 'Q':react,
                      'QRad':radi, 'QCon':conv, 'Wknds':None, 'mDHW':None}

            self.r_receptacles = result

            # output ##########################################################
            # only the power load is returned
            load = int(np.sum(result['P'])/60/1000)
            print ' - Receptacle load is %s kWh' % str(load)

            return None
    
        def lightingload(self):
            '''
            Simulate use of lighting for residential buildings based on the 
            model of J. Widén et al (2009)
            '''
    
            # parameters ######################################################
            # Simulation of lighting load requires information on irradiance
            # levels which determine the need for lighting if occupant.
            # The loaded solar data represent the global horizontal radiation
            # at a time-step of 1-minute for Uccle, Belgium
            file = open('Climate//irradiance.txt','r')
            data_pickle = file.read()
            file.close()
            irr = cPickle.loads(data_pickle)
    
            # script ##########################################################
            # a yearly simulation is basic, also in a unittest
            nday = self.nday
            nbin = 144
            minutes = self.nday * 1440
            occ_m = self.occ_m[0]
            # the model is found on an ideal power level power_id depending on 
            # irradiance level and occupancy (but not on light switching 
            # behavior of occupants itself)
            time = np.arange(0, (minutes+1)*60, 60)
            to = -1 # time counter for occupancy
            tl = -1 # time counter for minutes in lighting load
            power_max = 200
            irr_max = 200
            pow_id = np.zeros(minutes+1)
            prob_adj = 0.1 # hourly probability to adjust
            pow_adj = 40 # power by which is adjusted
            P = np.zeros(minutes+1)
            Q = np.zeros(minutes+1)
            for doy, step in itertools.product(range(nday), range(nbin)):
                to += 1
                for run in range(0, 10):
                    tl += 1
                    if occ_m[to] == int(1) or (irr[tl] >= irr_max):
                        pow_id[tl] = 0
                    else:
                        pow_id[tl] = power_max*(1 - irr[tl]/irr_max)
                    # determine all transitions of appliances depending on 
                    # the appliance basic properties, ie. stochastic versus 
                    # cycling power profile
                    if occ_m[to] == 0:
                        P[tl] = pow_id[tl]
                    elif random.random() <= prob_adj:
                        delta = P[tl-1] - pow_id[tl]
                        delta_min = np.abs(delta - pow_adj)
                        delta_plus = np.abs(delta + pow_adj)
                        if delta > 0 and delta_min < np.abs(delta) :
                            P[tl] = P[tl-1]-pow_adj
                        elif delta < 0 and delta_plus < np.abs(delta):
                            P[tl] = P[tl-1]+pow_adj
                        else:
                            P[tl] = P[tl-1]
                    else:
                        P[tl] = P[tl-1]
    
            radi = P*0.55
            conv = P*0.45
    
            result = {'time':time, 'P':P, 'Q':Q, 'QRad':radi, 'QCon':conv}

            self.r_lighting = result    
            # output ##########################################################
            # only the power load is returned
            load = int(np.sum(result['P'])/60/1000)
            print ' - Lighting load is %s kWh' % str(load)

            return None

        receptacles(self)
        lightingload(self)


        return None

    def __dhwload__(self):
        '''
        Simulation of the domestic hot water tappings.
        - Including weekend days,
        - starting from a regular monday at 4:00 AM.
        '''

        load = []
        return load

    def __shsetting__(self):
        '''
        Simulation of the space heating setting points.
        - Including weekend days,
        - starting from a regular monday at 4:00 AM.
        '''

        setting = []
        return setting

    def summarize(self):
        '''
        Create proper summary for later-on creating IDEAS simulations input.
        '''
        
        return None

class Equipment(object):
    '''
    Data records for appliance simulation based on generated activity and
    occupancy profiles
    '''
    # All object parameters are given in kwargs
    def __init__(self, **kwargs):
        # copy kwargs to object parameters 
        for (key, value) in kwargs.items():
            setattr(self, key, value)

    def simulate(self, nday, dow, cluster, occ):

        def stochastic(self, nday, dow, cluster, occ):
            '''
            Simulate non-cycling appliances based on occupancy and the model 
            and Markov state-space of Richardson et al.
            '''

            # parameters ######################################################
            # First we check the required activity and load the respective
            # stats.DTMC file with its data.
            len_cycle = self.cycle_length
            if self.activity not in ('None','Presence'):
                actdata = stats.DTMC(cluster=cluster)
            else:
                actdata = None

            # script ##########################################################
            # a yearly simulation is basic, also in a unittest
            nbin = 144 
            minutes = nday * 1440
            to = -1 # time counter for occupancy
            tl = -1 # time counter for load
            left = -1 # time counter for appliance duration
            P = np.zeros(minutes+1)
            Q = np.zeros(minutes+1)
            for doy, step in itertools.product(range(nday), range(nbin)):
                to += 1
                for run in range(10):
                    tl += 1
                    # check if this appliance is already on
                    if left <= 0:
                        # determine possibilities
                        if self.activity == 'None':
                            prob = 1
                        elif self.activity == 'Presence':
                            prob = 1 if occ[to] == 1 else 0
                        elif dow[doy] > 4:
                            occs = 1 if occ[to] == 1 else 0
                            prob = occs * actdata.prob_we[self.activity][step]
                        else:
                            occs = 1 if occ[to] == 1 else 0
                            prob = occs * actdata.prob_wd[self.activity][step]
                        # check if there is a statechange in the appliance
                        if random.random() < prob * self.cal:
                            left = random.gauss(len_cycle, len_cycle/10)
                            P[tl] += self.standby_power
                    else:
                        left += -1
                        P[tl] += self.cycle_power

            r_eq = {'time':time, 'occ':None, 'P':P, 'Q':Q, 'QRad':P*self.frad, 
                      'QCon':P*self.fconv, 'Wknds':None, 'mDHW':None}
                            
            return r_eq

        def cycle(self, nday):
            '''
            Simulate cycling appliances, eg. fridges and freezers based on
            average clycle length
            '''
            
            nbin = nday*24*60
            P = np.zeros(nbin+1)
            Q = np.zeros(nbin+1)
            left = random.gauss(self.delay, self.delay/4)
            for minute in range(nbin+1):
                if left <= 0:
                    left += self.cycle_length
                    P[minute] = self.cycle_power
                else:
                    left += -1
                    P[minute] = self.standby_power

            r_eq = {'time':time, 'occ':None, 'P':P, 'Q':Q, 'QRad':P*self.frad, 
                      'QCon':P*self.fconv, 'Wknds':None, 'mDHW':None}
                            
            return r_eq

        if self.delay == 0:
            r_app = stochastic(self, nday, dow, cluster, occ)
        else:
            r_app = cycle(self, nday)
            
        return r_app
