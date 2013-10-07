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

