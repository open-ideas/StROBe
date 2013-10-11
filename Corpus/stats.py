# -*- coding: utf-8 -*-
"""
Created on Wed Oct 09 11:57:02 2013

@author: Ruben
"""

import numpy as np
import random

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

def startstate(daytype, name='OSS'):
    '''
    Get the startstate for the first simulation day at 4:00 AM
    '''
    probs = [daytype[name]['1'], daytype[name]['2'], daytype[name]['3']]
    state = get_probability(random.random(), probs)
    return int(state)

def transition(daytype, state, time, name='OPM_'):
    '''
    Get next occupancy state in transition from 'state' ending at 'time'.
    '''
    probs = daytype[name+str(state)]
    newoc =get_probability(random.random(), probs[str(time)])
    return int(newoc)

def duration(daytype, state, time, name='ODM_'):
    '''
    Get the duration of current 'state' started at 'time'.
    '''
    probs = daytype[name+str(state)]
    durat = get_probability(random.random(), probs[str(time)])
    return durat

class MCSA(object):
    '''
    Monte Carlo Survival Analysis
    '''
    # All object parameters are given in kwargs
    def __init__(self, **kwargs):
        # copy kwargs to object parameters 
        for (key, value) in kwargs.items():
            setattr(self, key, value)        



class MCdtMc(object):
    '''
    Monte Carlo discrete-time Markov chain
    '''
    # All object parameters are given in kwargs
    def __init__(self, **kwargs):
        # copy kwargs to object parameters 
        for (key, value) in kwargs.items():
            setattr(self, key, value)        




















