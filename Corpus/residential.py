# -*- coding: utf-8 -*-
"""
Created on Mon October 07 16:16:10 2013

@author: Ruben Baetens
"""

import sys
import random
import numpy as np
import time
import datetime
import calendar
import ast
import os
import cPickle
import itertools

import stats
import data

sys.path.append("..")
from Data.Households import households
from Data.Appliances import set_appliances

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
        self.parameterize(**kwargs)

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
                key = random.randint(1, len(households))
                members = households[key]
            # And return the members as list fo strings
            return members

        def appliances():
            '''
            Define the pressent household appliances based on average national
            statistics independent of household member composition.
            '''
            # Loop through all appliances and pick randomly based on the
            # rate of ownership.
            app_n = []
            for app in set_appliances:
                if set_appliances[app]['type'] == 'appliance':
                    obj = Equipment(**set_appliances[app])
                    owner = obj.owner >= random.random()
                    app_n.append(app) if owner else None
            return app_n

        def tappings():
            '''
            Define the present household tapping types.
            '''
            tap_n = ['shortFlow', 'mediumFlow', 'bathFlow', 'showerFlow']
            return tap_n

        def clusters(members):
            '''
            Allocate each household member to the correct cluster based on the
            members occupation in time use survey data.
            '''
            clusters = []
            # loop for every individual in the household
            for ind in members:
                if ind != 'U12':
                    clu_i = data.get_clusters(ind)
                    clusters.append(clu_i)
            # and return the list of clusters
            return clusters
        # and run all
        self.members = members(**kwargs)
        self.apps = appliances()
        self.taps = tappings()
        self.clusters = clusters(self.members)
        # and return
        print 'Household-object created and parameterized.'
        print ' - Employment types are %s' % str(self.members)
        summary = [] #loop dics and remove dubbles
        for member in self.clusters:
            summary += member.values()
        print ' - Set of clusters is %s' % str(list(set(summary)))

        return None

    def simulate(self, year=2013, ndays=365):
        '''
        The simulate function includes the simulation of the household
        occupancies, plug loads, lighting loads and hot water tappings.
        '''

        self.year = year
        self.__chronology__(year, ndays)
        self.__occupancy__()
        self.__plugload__()
        self.__dhwload__()
        self.__shsetting__()

    def __chronology__(self, year, ndays=None):
        '''
        A basic internal calendar is made, storing the days and months of the
        depicted simulating year.
        - Monday == 0 ... Sunday == 6
        '''
        # first we determine the first week of the depicted year
        fdoy = datetime.datetime(year,1,1).weekday()
        fweek = range(7)[fdoy:]
        # whereafter we fill the complete year
        if ndays:
            nday = ndays
        else:
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
        def check(occday, min_form = True, min_time = False):
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
#                shape = np.array_equal(reduction, RED)

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
                daycheck = check(occs)
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
        hours = len(presence)/6.
        print ' - Total presence time is {0:.1f} out of {1} hours'.format(hours, self.nday*24)
        print '\tbeing {:.1f} percent)'.format(hours*100/(self.nday*24))
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

            # define number of minutes
            nmin = self.nday * 1440
            # determine all transitions of the appliances depending on the appliance
            # basic properties, ie. stochastic versus cycling power profile
            power = np.zeros(nmin+1)
            radi = np.zeros(nmin+1)
            conv = np.zeros(nmin+1)
            nday = self.nday
            dow = self.dow
            result_n = dict()
            counter = range(len(self.clusters))
            for app in self.apps:
                # create the equipment object with data from dataset.py
                eq = Equipment(**set_appliances[app])
                r_app = dict()
                n_app = 0
                # loop for all household mmembers
                for i in counter:
                    r_appi, n_appi = eq.simulate(nday, dow, self.clusters[i], self.occ[i])
                    r_app = stats.sum_dict(r_app, r_appi)
                    n_app += n_appi
                # and sum
                result_n.update({app:n_app})
                power += r_app['P']
                radi += r_app['QRad']
                conv += r_app['QCon']
            # a new time axis for power output is to be created as a different
            # time step is used in comparison to occupancy
            time = 4*60*60 + np.arange(0, (nmin+1)*60, 60)

            react = np.zeros(nmin+1)

            result = {'time':time, 'occ':None, 'P':power, 'Q':react,
                      'QRad':radi, 'QCon':conv, 'Wknds':None, 'mDHW':None}

            self.r_receptacles = result
            self.n_receptacles = result_n

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
            # Since the data starts at midnight, a shift to 4am is necessary
            # so that it coincides with the occupancy data!!!
            # the first 4 h are moved to the end. 
            os.chdir(r'../Data')
            file = open('Climate/irradiance.txt','r')
            data_pickle = file.read()
            file.close()
            irr = cPickle.loads(data_pickle)
            irr = np.roll(irr,-240) # brings first 4h to end
            # script ##########################################################
            # a yearly simulation is basic, also in a unittest
            nday = self.nday
            nbin = 144
            minutes = self.nday * 1440
            occ_m = self.occ_m[0]
            # the model is found on an ideal power level power_id depending on
            # irradiance level and occupancy (but not on light switching
            # behavior of occupants itself)
            time = 4*60*60 + np.arange(0, (minutes+1)*60, 60)
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
                    if occ_m[to] > int(1) or (irr[tl] >= irr_max):
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
        Simulate use of domestic hot water based on Jordan & Vajen (2001) and
        J.Widen (2009).
        '''

        # define number of minutes
        nmin = self.nday * 1440
        # determine all transitions of the appliances depending on the appliance
        # basic properties, ie. stochastic versus cycling power profile
        flow = np.zeros(nmin+1)
        clusterDict = self.clusters[0]
        nday = self.nday
        dow = self.dow
        occ_m = self.occ_m[0]
        result_n = dict()
        for tap in self.taps:
            # create the equipment object with data from dataset.py
            eq = Equipment(**set_appliances[tap])
            r_tap, n_tap = eq.simulate(nday, dow, clusterDict, occ_m)
            result_n.update({tap:n_tap})
            flow += r_tap['mDHW']
        # a new time axis for power output is to be created as a different
        # time step is used in comparison to occupancy
        time = 4*60*60 + np.arange(0, (nmin+1)*60, 60)

        result = {'time':time, 'occ':None, 'P':None, 'Q':None,
                  'QRad':None, 'QCon':None, 'Wknds':None, 'mDHW':flow}

        self.r_flows = result
        self.n_flows = result_n


        # output ##########################################################
        # only the power load is returned
        load = np.sum(result['mDHW'])
        loadpppd = int(load/self.nday/len(self.clusters))
        print ' - Draw-off is %s l/pp.day' % str(loadpppd)

        return None

    def __shsetting__(self):
        '''
        Simulation of the space heating setting points.
        - Including weekend days,
        - starting from a regular monday at 4:00 AM.
        '''

        #######################################################################
        # we define setting types based on their setpoint temperatures 
        # when being active (1), sleeping (2) or absent (3).
        types = dict()
        types.update({'2' : {1:18.5, 2:15.0, 3:18.5}})
        types.update({'3' : {1:20.0, 2:15.0, 3:19.5}})
        types.update({'4' : {1:20.0, 2:11.0, 3:19.5}})
        types.update({'5' : {1:20.0, 2:14.5, 3:15.0}})
        types.update({'6' : {1:21.0, 2:20.5, 3:21.0}})
        types.update({'7' : {1:21.5, 2:15.5, 3:21.5}})
        # and the probabilities these types occur based on Dutch research,
        # i.e. Leidelmeijer and van Grieken (2005).
        types.update({'prob' : [0.16, 0.35, 0.08, 0.11, 0.05, 0.20]})
        # and given a type, denote which rooms are heated
        given = dict()
        given.update({'2' : [['dayzone','bathroom']]})
        given.update({'3' : [['dayzone'],['dayzone','bathroom'],['dayzone','nightzone']]})
        given.update({'4' : [['dayzone'],['dayzone','nightzone']]})
        given.update({'5' : [['dayzone']]})
        given.update({'6' : [['dayzone','bathroom','nightzone']]})
        given.update({'7' : [['dayzone','bathroom']]})

        #######################################################################
        # select a type from the given types and probabilities
        rnd = np.random.random()
        shtype = str(1 + stats.get_probability(rnd, types['prob'], 'prob'))
        if len(given[shtype]) != 1:
            nr = np.random.randint(np.shape(given[shtype])[0])
            shrooms = given[shtype][nr]
        else:
            shrooms = given[shtype][0]

        #######################################################################
        # create a profile for the heated rooms
        shnon = 12*np.ones(len(self.occ_m[0])+1)
        shset = np.hstack((self.occ_m[0],self.occ_m[0][-1]))
        for key in types[shtype].keys():
            for i in range(len(shset)):
                if int(shset[i]) == key:
                    shset[i] = types[shtype][key]

        #######################################################################
        # and couple to the heated rooms
        sh_settings = dict()
        for room in ['dayzone', 'nightzone', 'bathroom']:
            if room in shrooms:
                sh_settings.update({room:shset})
            else:
                sh_settings.update({room:shnon})
        # and store
        self.sh_settings = sh_settings
        print ' - Average comfort setting is %s Celsius' % str(round(np.average(sh_settings['dayzone']),2))
        return None

    def roundUp(self):
        '''
        Round the simulation by wrapping all data and reduce storage size.
        '''

        #######################################################################
        # first we move and sumarize data to the most upper level.
        self.sh_day = self.sh_settings['dayzone']
        self.sh_night = self.sh_settings['nightzone']
        self.sh_bath = self.sh_settings['bathroom']
        self.P = self.r_receptacles['P'] + self.r_lighting['P']
        self.Q = self.r_receptacles['Q'] + self.r_lighting['Q']
        self.QRad = self.r_receptacles['QRad'] + self.r_lighting['QRad']
        self.QCon = self.r_receptacles['QCon'] + self.r_lighting['QCon']
        self.mDHW = self.r_flows['mDHW']

        #######################################################################        
        # bring last 4 h to the front so that data starts at midnight
        self.sh_day = np.roll(self.sh_day,24)
        self.sh_night = np.roll(self.sh_night,24)
        self.sh_bath = np.roll(self.sh_bath,24)
        self.P = np.roll(self.P,240)
        self.Q = np.roll(self.Q,240)
        self.QRad = np.roll(self.QRad,240)
        self.QCon = np.roll(self.QCon,240)
        self.mDHW = np.roll(self.mDHW,240)

        #######################################################################
        # then we delete the old data structure to save space
        del self.sh_settings
        del self.r_receptacles
        del self.r_lighting
        del self.r_flows

        #######################################################################
        # and end
        return None

    def pickle(self):
        '''
        Pickle the generated profile and its results for storing later.
        '''
        cPickle.dump(self, open(self.name+'.p','wb'))
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

        def stochastic_flow(self, nday, dow, clusterDict, occ):
            '''
            Simulate non-cycling appliances based on occupancy and the model
            and Markov state-space of Richardson et al.
            '''
            # parameters ######################################################
            # First we check the required activity and load the respective
            # stats.DTMC file with its data.
            len_cycle = self.cycle_length
            act = self.activity
            if self.activity not in ('None','Presence'):
                actdata = stats.DTMC(clusterDict=clusterDict)
            else:
                actdata = None

            # script ##########################################################
            # a yearly simulation is basic, also in a unittest
            nbin = 144
            minutes = nday * 1440
            to = -1 # time counter for occupancy
            tl = -1 # time counter for load
            left = -1 # time counter for appliance duration
            n_fl = 0
            flow = np.zeros(minutes+1)
            for doy, step in itertools.product(range(nday), range(nbin)):
                dow_i = dow[doy]
                to += 1
                for run in range(0, 10):
                    tl += 1
                    # check if this appliance is already on
                    if left <= 0:
                        # determine possibilities
                        if self.activity == 'None':
                            prob = 1
                        elif self.activity == 'Presence':
                            prob = 1 if occ[to] == 1 else 0
                        else:
                            occs = 1 if occ[to] == 1 else 0
                            prob = occs * actdata.get_var(dow_i, act, step)
                        # check if there is a statechange in the appliance
                        if random.random() < prob * self.cal:
                            n_fl += 1
                            left = random.gauss(len_cycle, len_cycle/10)
                            flow[tl] += self.standby_flow
                    else:
                        left += -1
                        flow[tl] += self.cycle_flow

            r_fl = {'time':time, 'occ':None, 'P':None, 'Q':None, 'QRad':None,
                      'QCon':None, 'Wknds':None, 'mDHW':flow}

            return r_fl, n_fl

        def stochastic_load(self, nday, dow, clusterDict, occ):
            '''
            Simulate non-cycling appliances based on occupancy and the model
            and Markov state-space of Richardson et al.
            '''

            # parameters ######################################################
            # First we check the required activity and load the respective
            # stats.DTMC file with its data.
            len_cycle = self.cycle_length
            act = self.activity
            if self.activity not in ('None','Presence'):
                actdata = stats.DTMC(clusterDict=clusterDict)
            else:
                actdata = None

            # script ##########################################################
            # a yearly simulation is basic, also in a unittest
            nbin = 144
            minutes = nday * 1440
            to = -1 # time counter for occupancy
            tl = -1 # time counter for load
            left = -1 # time counter for appliance duration
            n_eq = 0
            P = np.zeros(minutes+1)
            Q = np.zeros(minutes+1)
            for doy, step in itertools.product(range(nday), range(nbin)):
                dow_i = dow[doy]
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
                        else:
                            occs = 1 if occ[to] == 1 else 0
                            prob = occs * actdata.get_var(dow_i, act, step)
                        # check if there is a statechange in the appliance
                        if random.random() < prob * self.cal:
                            n_eq += 1
                            left = random.gauss(len_cycle, len_cycle/10)
                            P[tl] += self.standby_power
                    else:
                        left += -1
                        P[tl] += self.cycle_power

            r_eq = {'time':time, 'occ':None, 'P':P, 'Q':Q, 'QRad':P*self.frad,
                      'QCon':P*self.fconv, 'Wknds':None, 'mDHW':None}

            return r_eq, n_eq

        def cycle_load(self, nday):
            '''
            Simulate cycling appliances, eg. fridges and freezers based on
            average clycle length
            '''

            nbin = nday*24*60
            P = np.zeros(nbin+1)
            Q = np.zeros(nbin+1)
            n_eq = 0
            left = random.gauss(self.delay, self.delay/4)
            for tl in range(nbin+1):
                if left <= 0:
                    n_eq += 1
                    left += self.cycle_length
                    P[tl] = self.cycle_power
                else:
                    left += -1
                    P[tl] = self.standby_power

            r_eq = {'time':time, 'occ':None, 'P':P, 'Q':Q, 'QRad':P*self.frad,
                      'QCon':P*self.fconv, 'Wknds':None, 'mDHW':None}

            return r_eq, n_eq

        if self.type == 'appliance':
            #check if the equipment is an appliance instead of tapping point
            if self.delay == 0:
                r_app, n_app = stochastic_load(self, nday, dow, cluster, occ)
            else:
                r_app, n_app = cycle_load(self, nday)
        else:
            r_app, n_app = stochastic_flow(self, nday, dow, cluster, occ)

        return r_app, n_app
