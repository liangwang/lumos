#!/usr/bin/env python

import math
from Core import IOCore
from System import System

class UnlimitedPowerSystem(System):
    def __init__(self, core=IOCore(), area=500):
        System.__init__(self)
        
        self.power = 0
        self.area = area
        

        self.set_core(core)

    
    def set_core(self, core):
        self.core = core

        #mech = core.mech
        #tech = core.tech

        self.cnum = self.area / core.area

        #dvfs_lb = core.get_dvfs_lb() 
        #freq_factor, perf, power = core.dvfs(dvfs_lb)

        dvfs_ub = core.get_dvfs_ub() 
        freq_factor, perf, power = core.dvfs(dvfs_ub)

        self.power = self.cnum * power



