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
    The Household class is the main class of StROBe, defining the
    household composition as input or randomized based on statistics and
    allowing simulation of the household for building energy simulations.

    Main functions are:
        - __init__(), which creates and parameterizes a new household, defining the members and appliances of the household.
        - self.simulate(), which runs a simulation of occupancy, plug loads, lighting loads, hot water tappings and space heating settings for the specified year.
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
        self.variables=dict() # dictionary with explanation of main outputs, filled in in submodules

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
            #changes for new cold-appliance fix #######################################
            
            # Based on 10000 runs, these new values combined with rule-based fix below
            # lead to the same overall ownership as the original values.
            # We change it here so that the original remain in the Appliances file.
            set_appliances['Refrigerator']['owner']=0.27     # original:  0.430
            set_appliances['FridgeFreezer']['owner']=0.40    # original:  0.651
            set_appliances['ChestFreezer']['owner']=0.19     # original:  0.163
            set_appliances['UprightFreezer']['owner']=0.31   # original:  0.291
            
            app_n = []
            for app in set_appliances:
                if set_appliances[app]['type'] == 'appliance':
                    obj = Equipment(**set_appliances[app])
                    owner = obj.owner >= random.random()
                    app_n.append(app) if owner else None
                    
            # Cold appliances fix:   ###############################################        
            if not ('FridgeFreezer' in app_n) and not ('Refrigerator' in app_n): # if there was none of the two-> add one of the two.
                #  Find probability of household to own FF instead of R: (FF ownership over sum of two ownerships-> scale to 0-1 interval)
                prob=set_appliances['FridgeFreezer']['owner']/(set_appliances['FridgeFreezer']['owner']+set_appliances['Refrigerator']['owner'])
                # if random number is below prob, then the household will own a FF, otherwise a R -> add it
                app_n.append('FridgeFreezer') if prob >= random.random()  else app_n.append('Refrigerator') 
            
            if 'FridgeFreezer' in app_n and 'ChestFreezer' in app_n and 'UprightFreezer' in app_n:  #if there were 3 freezers-> remove a freezer-only
                #find probability of household to own CF instead of UF:  (CF ownership over sum of two ownerships-> scale to 0-1 interval)
                prob=set_appliances['ChestFreezer']['owner']/(set_appliances['ChestFreezer']['owner']+set_appliances['UprightFreezer']['owner'])
                # if random number is below prob, then the household will own a CF, otherwise an UF-> remove the other
                app_n.remove('UprightFreezer') if prob >= random.random()  else app_n.remove('ChestFreezer') #remove the one you don't own
                
            #########################################################################
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
            clustersList = []
            # loop for every individual in the household
            for ind in members:
                if ind != 'U12':
                    clu_i = data.get_clusters(ind)
                    clustersList.append(clu_i)
            # and return the list of clusters
            return clustersList
        # and run all
        self.members = members(**kwargs)
        self.apps = appliances()
        self.taps = tappings()
        self.clustersList = clusters(self.members)
        # and return
        print ('Household-object created and parameterized.')
        print (' - Employment types are %s' % str(self.members))
        summary = [] #loop dics and remove doubles
        for member in self.clustersList:
            summary += member.values()
        print (' - Set of clusters is %s' % str(list(set(summary))))

        return None

    def simulate(self, year=2013, ndays=365):
        '''
        The simulate function includes the simulation of the household
        occupancies, plug loads, lighting loads, hot water tappings and space heating settings.
        '''

        self.year = year
        self.__chronology__(year, ndays)
        self.__occupancy__()
        self.__plugload__()
        self.__dhwload__()
        self.__shsetting__()
        self.roundUp()

    def __chronology__(self, year, ndays=None):
        '''
        A basic internal calendar is made, storing the days and months of the
        depicted simulating year.
        - Monday == 0 ... Sunday == 6
        '''
        # determine number of days. +1 for the extra simulated day to cover the first 4h (later removed)
        if ndays:
            nday = ndays +1
        else:
            nday = 366+1 if calendar.isleap(year) else 365+1
        
        # first we determine the first week of the depicted year (one day earlier)
        fdoy = datetime.datetime(year-1,12,31).weekday()
        fweek = range(7)[fdoy:]
        # whereafter we fill the complete year
        day_of_week = (fweek+53*range(7))[:nday]
        # and return the day_of_week for the entire year
        self.dow = day_of_week
        self.nday = nday
        return None

    def __occupancy__(self, min_form = True, min_time = False):
        '''
        Simulation of occupancy profiles for each occupant based on their clusters.
        - A weekday, saturday and sunday are simulated, after which a typical week is created and repeated for the entire simulation period.
        - The starting day of the year is taken into account. 
        - The occupancy profiles start at 4:00 AM, in accordance with the used survey data. (later shifted, see roundUp())
        '''
        def check(occday, min_form = True, min_time = False): # -->> this check is not effective !!!
            '''
            We set a check which becomes True if the simulated day behaves
            according to the cluster, as a safety measure for impossible
            solutions. 
            ---->>> This check is not effectively implemented for the moment !!!
            '''

            # script 1 ########################################################
            # First we check if the simulated occ-chain has the same shape
            shape = True #  --->>> Check not effective, shape=True always !!!!!!!!!!!
            if min_form:
                location = np.zeros(1, dtype=int)
                reduction = occday[0]*np.ones(1, dtype=int)
                for i in range(len(occday)-1):
                    if occday[i+1] != occday[i]:
                        location = np.append(location, i+1)
                        reduction = np.append(reduction,occday[i+1])
#                shape = np.array_equal(reduction, RED) --->>> RED not available any more!!

            # script 2 ########################################################
            # And second we see if the chain has no sub-30 min differences
            length = True #  --->>> Check not effective, length=True always !!!!!!!!!!!
            if min_time:  # ------>>> min_time=False by default !!
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
            return shape and length # --->>> Check not effective, always True  !!!!!!!!!!!

        def dayrun(start, cluster):
            '''
            Simulation of a single day according to start state 'start'
            and the stochastics associated with 'cluster'.
            '''

            # script ##########################################################
            # we set the default daycheck at False for the first run and loop
            # creating days while False, meaning while the simulated day does
            # not correspond to the agreed-on rules in check().
            # ----->>> The check is currently not effectively implemented.
            daycheck = False
            end = datetime.datetime.utcnow() + datetime.timedelta(seconds = 10)
            # define the corresponding MCSA object from stats.py depicting a
            # Monte Carlo Survival Analysis object.
            SA = stats.MCSA(cluster)
            # and then keep simulating a day until True
            while daycheck == False:
                # set start state conditions
                tbin = 0
                occs = np.zeros(144, dtype=int)
                occs[0] = start
                # occupancy data from survey are given per 30 min, so we need to know in which of 48 bins to look for data:
                t48 = np.array(sorted(list(range(1, 49)) * 3))
                dt = SA.duration(start, t48[0]) # get duration of current state at start time (4am)
                # and loop sequentially transition and duration functions
                while tbin < 143:
                    tbin += 1
                    if dt == 0: # previous state duration has ended
                        occs[tbin] = SA.transition(occs[tbin-1], t48[tbin]) # find most probable next state
                        dt = SA.duration(occs[tbin], t48[tbin]) - 1 # restart duration counter for new state
                        # -1 is necessary, as the occupancy state already started
                    else:
                        occs[tbin] = occs[tbin - 1] # maintain current state
                        dt += -1 # count down duration of current state
                # whereafer we control if this day is ok
                daycheck = check(occs) # ----->>> The check is currently not effectively implemented, always TRUE! 
                # and we include a break if the while-loop takes to long until
                # check()-conditions are fulfilled.
                if datetime.datetime.utcnow() > end:
                    break

            # ouput ###########################################################
            # return occupants array if daycheck is ok
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
        # and create a typical week.
        cdir = os.getcwd()
        occ_week = [] #typical week
        for member in self.clustersList:
            week=[] # initiate empty week
            SA = stats.MCSA(member['wkdy'])
            startstate=SA.startstate() # random starting state of week, depending on cluster 
            for i in range(5):
                week = np.append(week, dayrun(startstate, member['wkdy']))
                startstate=week[-1]
            week = np.append(week, dayrun(week[-1], member['sat']))
            week = np.append(week, dayrun(week[-1], member['son']))
            occ_week.append(week)
        # A merge occupancy is created depicted the most active state of all
        # household members, later-on used for set-point temperatures and hot water tappings.
        occ_merg = merge(occ_week)
        # and combine the weekly occupancy states for the entire year by
        # repeating them every week and correcting for the first day of year and stop time,
        # including for the merged occupancy.
        bins = 144 # number of datapoints in one day
        tstart = bins*(self.dow[0]) # need to sart on correct day of week
        tstop = tstart + bins*(self.nday)+1 # need nday in total, plus one step (for IDEAS simulations)
        occ_year = []
        for line in range(len(occ_week)):# per separate member
            #repeat week more than enough times (54), take days needed to have correct nday and start day
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
        print (' - Total presence time is {0:.1f} out of {1} hours'.format(hours, self.nday*24))
        print ('\tbeing {:.1f} percent)'.format(hours*100/(self.nday*24)))
        return None

    def __plugload__(self):
        '''
        Simulation of the electric load based on the occupancy profile, 
        the clusters that determine the activity probabilities,
        and the present appliances.
        - Weekdays, Saturday and Sunday differ.
        - The simulation starts at 4:00 AM.
        '''

        def receptacles(self):
            '''
            Simulation of the receptacle loads.
            '''
            nday = self.nday
            dow = self.dow
            nmin = nmin = nday * 24 * 60 # number of minutes in total number of days
            power = np.zeros(nmin+1)
            react = np.zeros(nmin+1)
            radi = np.zeros(nmin+1)
            conv = np.zeros(nmin+1)
            result_n = dict()
            for app in self.apps:
                # create the equipment object with data from Appliances.py
                eq = Equipment(**set_appliances[app])
                # simulate what the load will be
                r_app, n_app = eq.simulate(nday, dow, self.clustersList, self.occ)
                # and add to total load
                result_n.update({app:n_app})
                power += r_app['P']
                react += r_app['Q']
                
                radi += r_app['QRad']
                conv += r_app['QCon']
            # a new time axis for power output is to be created 
            # since a different time step is used in comparison to occupancy
            time = 4*60*60 + np.arange(0, (nmin+1)*60, 60) # in seconds, starts at 4:00 AM

            result = {'time':time, 'P':power, 'Q':react, 'QRad':radi, 'QCon':conv }

            self.r_receptacles = result
            self.n_receptacles = result_n

            # output ##########################################################
            # only the power load is returned
            load = int(np.sum(result['P'])/60/1000)
            print (' - Receptacle load is %s kWh' % str(load))

            return None

        def lightingload(self):
            '''
            Simulate use of lighting for residential buildings based on the
            model of J. Widén et al (2009)
            The model computes an ideal power level pow_id depending on the irradiance level 
            and occupancy (but not on light switching behavior of occupants itself). 
            The power is then adjusted in steps, assuming occupants will not react smoothly to irradiation changes.
            '''

            # parameters ######################################################
            # Simulation of lighting load requires information on irradiance
            # levels which determine the need for lighting if occupant.
            # The loaded solar data represent the global horizontal radiation
            # at a time-step of 1-minute for Uccle, Belgium
            # Since the data includes only 365 days, we add one days at the beginning to match the extra initiation day
            # and one at the end in case of a leap year.
            # Furthermore, the data starts at midnight, so a shift to 4am is necessary
            # so that it coincides with the occupancy data!!! (the first 4 h are moved to the end) 
            os.chdir(r'../Data')
            file = open('Climate/irradiance.txt','r')
            data_pickle = file.read()
            file.close()
            irr = cPickle.loads(data_pickle)
            irr=np.insert(irr,1,irr[-24*60:]) # add december 31 to start of year (for extra day used to fill first 4h)
            irr=np.append(irr,irr[-24*60:]) # add december 31 to end of year in case of leap year
            irr = np.roll(irr,-240) # brings first 4h to end, to match start of occupancy at 4 AM instead of midnight
            # script ##########################################################
            # a yearly simulation is basic, also in a unittest
            nday = self.nday
            nbin = 144 # steps in occupancy data per day (10min steps)
            nmin = nday * 24 * 60 # number of minutes in total number of days
            occ_m = self.occ_m[0]
            to = -1 # time counter for occupancy
            tl = -1 # time counter for minutes in lighting load
            power_max = 200 # lighting power used when there is 0 irradiance (maximum)
            irr_max = 200 # irradiance threshhold above which no lighting is used
            pow_id = np.zeros(nmin+1) # initialize zero ideal lighing load
            prob_adj = 0.1 # probability to adjust lighting
            pow_adj = 40 # step by which power is adjusted
            P = np.zeros(nmin+1)
            Q = np.zeros(nmin+1)
            for doy, step in itertools.product(range(nday), range(nbin)): #loop over simulation period, per 10min steps
                to += 1
                for run in range(0, 10): #for each minute in the step
                    tl += 1
                    if occ_m[to] > int(1) or (irr[tl] >= irr_max): #if occupants not active (occ_m>1) OR irradiance more than threshhold
                        pow_id[tl] = 0 # lights will be off
                    else:
                        pow_id[tl] = power_max*(1 - irr[tl]/irr_max) # lights ON, power depends on level of irradiance compared to irr_max
                  
                    # determine final power usage after stepwise adjustments
                    if occ_m[to] > int(1): # if OFF, it stays that way
                        P[tl] = pow_id[tl]
                    elif random.random() <= prob_adj: # if ON, check if adjustment happens (random number< prob_adj)
                        delta = P[tl-1] - pow_id[tl] # difference between previous step and "ideal" current step 
                        if delta > 0 and pow_adj/2 < np.abs(delta) : # if absolute difference is larger than half of the adjustment step
                            P[tl] = P[tl-1]-pow_adj  # the new power is the previous one, decreased by the adjustment step
                        elif delta < 0 and pow_adj/2 < np.abs(delta):
                            P[tl] = P[tl-1]+pow_adj  # the new power is the previous one, increased by the adjustment step
                        else: #otherwise, keep previous level
                            P[tl] = P[tl-1]
                    else: #otherwise, keep previous level
                        P[tl] = P[tl-1]

            radi = P*0.55 # fixed radiative part 55% for heat dissipation
            conv = P*0.45 # fixed convective part 45% for heat dissipation

            result = {'P':P, 'Q':Q, 'QRad':radi, 'QCon':conv}

            self.r_lighting = result

            load = int(np.sum(result['P'])/60/1000)
            print (' - Lighting load is %s kWh' % str(load))
            
            return None

        receptacles(self)
        lightingload(self)
 
        self.variables.update({'P': 'Active power demand for appliances and lighting in W.',
                               'Q':'Reactive power demand for appliances and lighting in W.',
                               'QRad': 'Radiative internal heat gains from appliances and lighting in W.',
                               'QCon': 'Convective internal heat gains from appliances and lighting in W.'})

        return None

    def __dhwload__(self):
        '''
        Simulate use of domestic hot water based on Jordan & Vajen (2001) and
        and the Markov state-space model of Richardson et al.
        '''
        nday = self.nday
        dow = self.dow
        occ_m = self.occ_m[0] # use merged occupancy -> simulate once
        cluster= [self.clustersList[0]] # use only clusterDict from 1st occupant (still a list since in [])
        nmin = nday * 24 * 60 # number of minutes in total number of days
        flow = np.zeros(nmin+1)
        result_n = dict()
        for tap in self.taps:
            # create the tapping object with data from Appliances.py
            eq = Equipment(**set_appliances[tap])
            # simulate the DHW demand
            r_tap, n_tap = eq.simulate(nday, dow, cluster, occ_m)
            result_n.update({tap:n_tap})
            flow += r_tap['mDHW']
    
        result = {'mDHW':flow}
    
        self.r_flows = result
        self.n_flows = result_n
        self.variables.update({'mDHW': 'Domestic hot water demand at the tap points in l/min.'})

        load = np.sum(result['mDHW'])
        loadpppd = int(load/self.nday/len(self.clustersList))
        print (' - Draw-off is %s l/pp.day' % str(loadpppd))
 
        return None

    def __shsetting__(self):
        '''
        Simulation of the space heating setting points.
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
        # and given the type, denote which rooms are heated (more than one possibility)
        shr = dict()
        shr.update({'2' : [['dayzone','bathroom']]})
        shr.update({'3' : [['dayzone'],['dayzone','bathroom'],['dayzone','nightzone']]})
        shr.update({'4' : [['dayzone'],['dayzone','nightzone']]})
        shr.update({'5' : [['dayzone']]})
        shr.update({'6' : [['dayzone','bathroom','nightzone']]})
        shr.update({'7' : [['dayzone','bathroom']]})
    
        #######################################################################
        # select a type based on random number and probabilities associated to types
        rnd = np.random.random()
        shtype = str(1 + stats.get_probability(rnd, types['prob'], 'prob'))
        #define which rooms will be heated
        if len(shr[shtype]) != 1: # if there are more possibilities, choose one randomly
            nr = np.random.randint(np.shape(shr[shtype])[0])
            shrooms = shr[shtype][nr]
        else:
            shrooms = shr[shtype][0]
    
        #######################################################################
        # create a profile for the heated rooms
        shnon = 12*np.ones(len(self.occ_m[0])) #non-heated rooms : 12 degC
        shset = 12*np.ones(len(self.occ_m[0]))  #initiate space heating settings also as non-heated
        occu = self.occ_m[0] # get merged occupancy 
        for key in types[shtype].keys(): # for each occupancy state
            shset[occu == key] = types[shtype][key]  # use appropriate temperature setting given in "types"   

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
        print (' - Average comfort setting is %s Celsius' % str(round(np.average(sh_settings['dayzone']),2)))
        
        self.variables.update({'sh_day': 'Space heating set-point temperature for day-zone in degrees Celsius.',
                                'sh_bath': 'Space heating set-point temperature for bathroom in degrees Celsius.',
                                'sh_night': 'Space heating set-point temperature for night-zone in degrees Celsius.'})
     
        return None

    def roundUp(self):
        '''
        Round the simulation by wrapping all data and reduce storage size.
        Also shift the data to start at Midnight instead of 4 AM (last 4h brought to the front)
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
        self.dow = self.dow[1] # only first day of year is interensting to keep (skip initiation day(index=0))
        
        #######################################################################        
        # delete first 20h and last 4 h  so that data starts and ends at midnight
        # keep an extra time step for IDEAS simulations 
        # (we assume first value indicates average occupancy, P, etc from time 0 to time 0+time step)
        self.nday=self.nday-1 # change back to originally asked number (remove extra initiation day)
        start=20*60 # start minute, after 20h -> midnight of initiation day
        stop=start + self.nday*24*60 # end minute, 4h before end of last day -> midnight 
        
        self.occ_m = self.occ_m[0][start/10:stop/10+1] # 10-min resolution, so for indeces: devide start & stop by 10.
        self.occ=[i[start/10:stop/10+1] for i in self.occ] 
    
        self.sh_day = self.sh_day[start/10:stop/10+1]
        self.sh_night = self.sh_night[start/10:stop/10+1]
        self.sh_bath = self.sh_bath[start/10:stop/10+1]
        self.P = self.P[start:stop+1] #1-min data, and one extra step
        self.Q = self.Q[start:stop+1]
        self.QRad = self.QRad[start:stop+1]
        self.QCon = self.QCon[start:stop+1]
        self.mDHW = self.mDHW[start:stop+1]
    
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

    def simulate(self, nday, dow, clustersList, occ):

        def stochastic_flow(self, nday, dow, clusterList, occ):
            '''
            Simulate hot water tappings based on occupancy and the 
            Markov state-space model of Richardson et al.
            Tapping characteristics are taken from Jordan & Vajen (2001). 
            "Realistic Domestic Hot-water Profiles in Different Time Scales"
            '''
            # parameters ######################################################
            # First we check the required activity and load the respective
            # stats.DTMC file with its data for the "main" occupant, since the merged occupancy is used.
            clusterDict=clusterList[0] # take Dictionary in first element of list (i.e. "main" occupant)
            len_cycle = self.cycle_length
            act = self.activity
            if self.activity not in ('None','Presence'): # get activity probabilities from stats.DTMC file
                actdata = stats.DTMC(clusterDict=clusterDict)
            else:
                actdata = None

            # script ##########################################################
            # a yearly simulation is basic, also in a unittest
            nbin = 144 # steps in occupancy data per day (10min steps)
            nmin = nday * 24 * 60 # number of minutes in total number of days
            to = -1 # time counter for occupancy
            tl = -1 # time counter for flow
            left = -1 # time counter for tapping duration
            n_fl = 0
            flow = np.zeros(nmin+1)
            for doy, step in itertools.product(range(nday), range(nbin)):
                dow_i = dow[doy]
                to += 1
                for run in range(0, 10):
                    tl += 1
                    # check if this tap is already open
                    if left <= 0:
                        # determine possibilities
                        if self.activity == 'None':
                            prob = 1
                        elif self.activity == 'Presence':
                            prob = 1 if occ[to] == 1 else 0
                        else:
                            occs = 1 if occ[to] == 1 else 0
                            prob = occs * actdata.get_var(dow_i, act, step)
                        # check if there is a statechange in the tap
                        if random.random() < prob * self.cal:
                            n_fl += 1
                            left = random.gauss(len_cycle, len_cycle/10)
                        flow[tl] += self.standby_flow
                    else:
                        left += -1
                        flow[tl] += self.cycle_flow

            r_fl = {'mDHW':flow}

            return r_fl, n_fl

        def stochastic_load(self, nday, dow, clustersList, occ):
            '''
            Simulate non-cycling appliances based on occupancy and the 
            Markov state-space model of Richardson et al.
            '''
            # parameters ######################################################

            len_cycle = self.cycle_length # cycle length for this appliance
            act = self.activity  # activity linked to the use of this appliance
            numOcc=len(clustersList) # number of differenc active occupants >12y

            # script ##########################################################
            # a yearly simulation is basic, also in a unittest
            nbin = 144 # steps in occupancy data per day (10min steps)
            nmin = nday * 24 * 60 # number of minutes in total number of days
            n_eq_dur = 0 # number of minutes that the appliance is used
            P = np.zeros(nmin+1)
            Q = np.zeros(nmin+1)    
             
            # prefill probabilities for each occupant to perform the activity linked to appliance for entire year          
            # make occupancy vector per time step (10-min): if ANY occupant is active (state=1), make aggregate occy=1
            occy =[[1 if occ[i][x] == 1 else 0 for x in range(nday*nbin)] for i in range(numOcc)] # size numOcc x timesteps in year            
            if act == 'None': # if appliance is linked  to no specific activity (e.g. fridge)
                prob = [[1 for x in range(nday*nbin)] for i in range(numOcc)] # activity 'None' always probability=1 
            elif act == 'Presence': # if appliance linked to presence (active occupants): probability =1 when ANYONE is present
                prob = occy
            else: # appliance linked to specific activity (e.g. "food")  
                # get activity probabilities for all occupants from stats.DTMC file
                actdata= [stats.DTMC(clusterDict=clustersList[i]) for i in range(numOcc)] 
                prob = occy   # just initiate correct size    
                to = -1 # time counter for occupancy
                for doy, step in itertools.product(range(nday), range(nbin)): #loop over year
                    dow_i = dow[doy] # day of week (Monday=0)
                    to += 1
                    for i in range(numOcc): # get probability each occupant is performing the activity related to the appliance
                        prob[i][to] = occy[i][to] * actdata[i].get_var(dow_i, act, step)

            ######################### SIMULATE appliance use
            to = -1 # time counter for occupancy (10min)
            tl = -1 # time counter for load (1min)
            left = [-1 for i in range(numOcc)] # time counter for appliance duration per occupant -> start as not used: -1
            
            for doy, step in itertools.product(range(nday), range(nbin)): # loop over 10min steps in year
                dow_i = dow[doy] # day of week
                to += 1
                # occupancy in 10 min, but for each occupancy step simulate 10 individual minutes for the loads.
                for run in range(10):
                    tl += 1
                    if any(l > 0 for l in left): # if any occupant was using the appliance (there was time left[i]>0)
                        P[tl] += self.cycle_power  # assign power used when appliance is working
                        n_eq_dur += 1 # add to counter for number of minutes used in year
                    else: # if nobody was using it
                        P[tl] += self.standby_power # assign stand-by power
                        
                    # per occupant, check if they will want to change the state of the appliance
                    for i in range(numOcc): 
                        # check if this appliance is being used by occupant i: time left[i]>0
                        if left[i] > 0:
                            left[i] += -1   # count time down until cycle passed (for this occupant)          
                        else: # if it was not used by this occupant: left[i] <= 0 
                            # check if there is a state change in the appliance for this occupant
                            if random.random() < prob[i][to] * self.cal: # if random number below calibration factor cal* probability of activity: start appliance
                                left[i] = random.gauss(len_cycle, len_cycle/10) # start a cycle of random  duration for this occupant

                            
            r_eq = {'P':P, 'Q':Q, 'QRad':P*self.frad, 'QCon':P*self.fconv,}
            
           # n_eq is used in calibration process for value of 'cal'
            if len_cycle != 0: 
                n_eq=n_eq_dur/len_cycle # approximate number of cycles/year (assuming average length: mean of gauss distribution)                
            else:
                 n_eq=1e-05 # some appliances don't have number of cycles if they are continuously working (then n_eq is not used)
            return r_eq, n_eq

        def cycle_load(self, nday):
            '''
            Simulate cycling appliances, eg. fridges and freezers based on
            average clycle length and delay between cycles
            '''

            nmin = nday * 24 * 60 # number of minutes in total number of days
            P = np.zeros(nmin+1)
            Q = np.zeros(nmin+1) #currently no data included (remains zero)
            n_eq = 0 # number of cycles for calibration of `cal` parameter of appliance
            
            # define length of cycles (same for entire year, assumed to depend on appliance)
            len_cycle=random.gauss(self.cycle_length, self.cycle_length/10)
            # define duration of break between cycles (same for entire year)
            delay=random.gauss(self.delay, self.delay/10)
            
            # start as OFF (assumption)
            on=False #is it ON? 
            left = random.gauss(delay/2, delay/4) # time left until change of state (initiate random)
                       
            for tl in range(nmin+1): # loop over every minute of the year
                # if there is time LEFT until change of state, remain as is
                # if time is up, change state:  
                if left <= 0:  
                    on=not on # switch to opposite state ON/OFF
                    if on: # if switched ON
                        n_eq += 1 # add one to cycle counter
                        left = len_cycle #start counting 1 cycle length          
                    else: # if switched OFF
                        left = delay #start counting time until next cycle
                # either way, count downt the time until next change of state    
                left += -1  
                # allocate correct power, depending on current state ON/OFF       
                if on: 
                    P[tl] = self.cycle_power # instead of the average consumption, could be sampled from normal distribution as well
                else: 
                    P[tl] = self.standby_power 

            r_eq = {'P':P, 'Q':Q, 'QRad':P*self.frad,'QCon':P*self.fconv}

            return r_eq, n_eq

        # when simulating an equipment object, choose which of following happens:             
        if self.type == 'appliance': #check if the equipment is an appliance instead of tapping point        
            if self.activity == 'None': #cycling loads -> don't depend on occupants
                r_app, n_app = cycle_load(self, nday) 
            elif self.name in ('placeholder'): # For future: if each occupant has her/his own appliance
                # For the moment appliances are assigned to the household such that there is one of each type 
                # -> no way many people use their own (That's why there are 3 different TVs)
                r_app = dict()
                n_app = 0
                for i in range(len(clustersList)): # loop active occupants >12y
                    r_appi, n_appi = stochastic_load(self, nday, dow, [clustersList[i]], [occ[i]])# we pass a list with one clusterDict
                    r_app = stats.sum_dict(r_app, r_appi)
                    n_app += n_appi                
            else: # other appliances (shared)               
                r_app, n_app = stochastic_load(self, nday, dow, clustersList, occ)# we pass a list with all available clusterDicts, as given from plugloads
        else: # flow-> model is based on total presence: do only once.
            r_app, n_app = stochastic_flow(self, nday, dow, clustersList, occ) # we pass a list with one clusterDict, as given from DHW model


        return r_app, n_app