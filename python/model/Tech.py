#!/usr/bin/env python

import math

class Base:
    vdd = 1
    vth = 0.45
    
    # Picked up from McPAT
    freq={'IO': 4.2, 'O3': 3.7}
    power={'IO': 6.14, 'O3': 19.83}
    pleak={'IO': 1.058, 'O3': 5.34}
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

    freq = {'ITRS': {45 : 1, 32 : 1.09,
                     22 : 2.38, 16 : 3.21,
                     11 : 4.17, 8  : 3.85},
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
    vth_itrs = {45: 0.33, 32: 0.297,
                22: 0.2673, 16: 0.2409,
                11: 0.2178, 8:0.198}    
    
    vth = dict([(tech, vth_itrs[tech]/vth_itrs[45]) for tech in sorted(vth_itrs.iterkeys())])



