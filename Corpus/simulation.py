#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Simulate demand scenarios at building level, for specific household."""

import numpy as np
from residential import Household


def convert_occupancy(occ):
    """Convert occupancy as number of inhabitants currently in house."""
    for i in xrange(len(occ)):
        arr = occ[i]
        arr[arr < 3] = 1 # active (1) or sleeping (2) are both present =1
        arr[arr == 3] = 0 # absent (3) =0
    return sum(occ)


def simulate_scenarios(n_scen, year, ndays, members):
    """Simulate scenarios of demands during ndays.

    Parameters
    ----------
    n_scen : int
        Number of scenarios to generate

    year : int
        Year to consider
        
    ndays : int
        Number of days to consider

    members : str
        Member list of household

    Returns
    -------
    elec : numpy array, shape (n_scen, nminutes)
        Electrical demands scenarios, sampled at
        minute time-step

    mDHW : numpy array, shape (n_scen, nminutes)
        DHW demands scenarios, sampled at
        minute time-step

    occupancy : numpy array, shape (n_scen, tenminutes)
        DHW demands scenarios, sampled at a
        10 minute time-step

    """

    nminutes = ndays * 1440 + 1
    ntenm = ndays * 144 + 1
       
    family = Household("ex", members=members)

    # define arrays storing the scenarios:
    elec = np.zeros((n_scen, nminutes))
    mDHW = np.zeros((n_scen, nminutes))
    occupancy = np.zeros((n_scen, ntenm))

    for i in xrange(n_scen):
        print "Generate scenario {}".format(i)
        family.simulate(year, ndays)

        # aggregate scenarios:
        elec[i, :] = family.P
        mDHW[i, :] = family.mDHW
        occupancy[i, :] = convert_occupancy(family.occ)
    
    result={'elec':elec, 'mDHW':mDHW, 'occupancy':occupancy}

    return result

result = simulate_scenarios(2, 2020, 366, members=['FTE', 'PTE', 'School'] )