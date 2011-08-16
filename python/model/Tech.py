#!/usr/bin/env python

import math

class Base:
    vdd = 1
    vth = 0.45
    
    # Picked up from McPAT
    freq={'IO': 4.2, 'O3': 3.7}
    dp={'IO': 6.14, 'O3': 19.83} # dynamic power
    sp={'IO': 1.058, 'O3': 5.34} # static(leakage) power
    area={'IO': 7.65, 'O3': 26.48}

class Scale:
    mech = ['ITRS','CONS']

    vdd = {'ITRS': {45 : 1, 32 : 0.93,
                    22 : 0.84, 16 : 0.75,
                    11 : 0.68, 8  : 0.62},
           'CONS': {45 : 1, 32 : 0.93,
                    22 : 0.88, 16 : 0.86,
                    11 : 0.84, 8  : 0.84}
          }

    """ ITRS 2009
            adopted from 2009Tables_FINAL_ORTC_v14.xls, sheet 2009_ORTC-4, frequency in MHz
            45: 5875, due 2010
            32: 6817, due 2012
            22: 8522, due 2015
            16:10652, due 2018
            11:13315, due 2021
             8:15451, due 2023
    """
    freq = {'ITRS': {45 : 1, 32 : 1.16,
                     22 : 1.45, 16 : 1.81,
                     11 : 2.26, 8  : 2.63},
            'CONS': {45 : 1, 32 : 1.10,
                     22 : 1.19, 16 : 1.25,
                     11 : 1.30, 8 : 1.34}
           }

    power = {'ITRS': {45 : 1, 32 : 0.66,
                      22 : 0.54, 16 : 0.38,
                      11 : 0.25, 8  : 0.12},
             'CONS': {45 : 1, 32 : 0.71,
                      22 : 0.52, 16 : 0.39,
                      11 : 0.29, 8  : 0.22}
            }

    area = {45 : 1, 32 : 0.5,
            22 : math.pow(0.5, 2),
            16 : math.pow(0.5, 3),
            11 : math.pow(0.5, 4),
            8  : math.pow(0.5, 5)}

    """ vth base values were adopted from 2010Tables_FEP_FOCUS_C_ITRS.xls, sheet 2009_FEP2-HPDevice
    """    
    _vth_itrs = {45: 0.33, 32: 0.297,
                22: 0.2673, 16: 0.2409,
                11: 0.2178, 8:0.198}    
    
    vth = dict([(tech, _vth_itrs[tech]/_vth_itrs[45]) for tech in sorted(_vth_itrs.iterkeys())])
    
    """ effective gate capacitance from 2010Tables_PIDS_FOCUS_C_ITRS.xls, sheet 2009_PIDS2
            45: 0.97
            32: 0.95
            22: 0.68
            16: 0.61
            11: 0.53
             8: 0.48
    """



