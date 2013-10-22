# -*- coding: utf-8 -*-
"""
Created on Wed Oct 09 11:57:02 2013

@author: Ruben Baetens
"""

import numpy as np
import random
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

class MCSA(object):
    '''
    The MCSA class defines a Monte Carlo Survival Analysis
    '''
    # All object parameters are given in kwargs
    def __init__(self, cluster, **kwargs):
        # load the dataset of the cluster into ds
        filnam = cluster+'.py'
        ds = ast.literal_eval(open(filnam).read())
        # and add them as class parameters
        self.OSS = ds['OSS']
        self.OPM = {1:ds['OPM_1'], 2:ds['OPM_2'], 3:ds['OPM_3']}
        self.ODM = {1:ds['ODM_1'], 2:ds['ODM_2'], 3:ds['ODM_3']}
        self.RED = ds['RED']

    def startstate(self):
        '''
        Get the startstate for first simulation day at 4:00 AM.
        '''
        # we define the startstate based on the given probability
        probs = [self.OSS['1'], self.OSS['2'], self.OSS['3']]
        state = get_probability(random.random(), probs)
        # and retrun the value
        return int(state)
    
    def transition(self, state, timebin):
        '''
        Get next occupancy state from current state ending at time.
        '''
        # we define the new state based on the given probability
        probs = self.OPM[state][str(timebin)]
        newoc = get_probability(random.random(), probs)
        # and retrun the value
        return int(newoc)
    
    def duration(self, state, timebin):
        '''
        Get the duration of current state started at time.
        '''
        # we define the new duration based on the given probability
        probs = self.ODM[state][str(timebin)]
        durat = get_probability(random.random(), probs)
        # and retrun the value
        return durat


class DTMC(object):
    '''
    The DTMC class defines a Discrete-Time Markov Chain
    '''
    # All object parameters are given in kwargs
    def __init__(self, cluster, **kwargs):
        # load the dataset of the cluster into ds
        filnam = cluster+'.py'
        ds = ast.literal_eval(open(filnam).read())
        # and add them as class parameters
        self.period = ds['period']
        self.steps = ds['steps']
        self.prob_wd = ds['prob_wd']
        self.prob_we = ds['prob_we']

