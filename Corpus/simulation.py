#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Simulate demand scenarios at buildings level."""

import numpy as np
from residential import Household


def convert_occupancy(occ):
    """Convert occupancy as number of inhabitants currently in house."""
    for i in xrange(len(occ)):
        arr = occ[i]
        arr[arr < 3] = 1
        arr[arr == 3] = 0
    return sum(occ)


def simulate_scenarios(n_scen, ndays):
    """Simulate scenarios of demands during ndays.

    Parameters
    ----------
    n_scen : int
        Number of scenarios to generate

    ndays : int
        Number of days to consider


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
    ntenm = ndays * 144
    family = Household("ex", members=["FTE"])

    # define arrays storing the scenarios:
    elec = np.zeros((n_scen, nminutes))
    mDHW = np.zeros((n_scen, nminutes))
    occupancy = np.zeros((n_scen, ntenm))

    for i in xrange(n_scen):
        print "Generate scenario {}".format(i)
        family.simulate(2013, ndays)

        # aggregate scenarios:
        family.roundUp()
        elec[i, :] = family.P
        mDHW[i, :] = family.mDHW

    return elec, mDHW, occupancy

