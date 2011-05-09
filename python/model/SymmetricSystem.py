#!/usr/bin/env python

import math
from Core import IOCore
from System import System

class SymmetricSystem(System):
    def __init__(self, core=IOCore(), 
                 budget={'area':500, 'power':200}):
        System.__init__(self)
        
        self.set_core_budget(core, budget)

    
    def set_util_ratio(self, ratio):
        if ratio > self._util_ratio_max:
            self._util_ratio = self._util_ratio_max
        elif ratio < self._util_ratio_min:
            self._util_ratio = self._util_ratio_min
        else:
            self._util_ratio = ratio

    def set_core(self, core):
        self._core = core
        self._cnum = self._area / core.get_area()

        self.__update_util_boundary()

    def set_budget(self, budget):
        self._power = budget['power']
        self._area = budget['area']
        
        self.__update_util_boundary()
        
    def set_core_budget(self, core, budget):
        self._power = budget['power']
        self._area = budget['area']
        
        self._core = core
        self._cnum = self._area / core.get_area()

        self.__update_util_boundary()
        
    def __update_util_boundary(self):
        core = self._core

        core.dvfs_min()
        self._util_ratio_max = min( (self._power/core.get_power())/(self._area/core.get_area()), 1)

        core.dvfs_max()
        self._util_ratio_min = (self._power/core.get_power())/(self._area/core.get_area())
        

    def __serial_perf(self, app):
        core = self._core
        core.dvfs_max()
        perf0 = core.get_perf0()
        freq = core.get_freq()
        return perf0* freq**(1-app.m)

    def __parallel_perf(self, app):
        core = self._core
        a0 = core.get_area()
        p0 = core.get_p0()
        v_factor = math.pow( (self._power*a0)/(self._util_ratio*p0*self._area), 0.333)

        core.dvfs(v_factor)

        perf0 = core.get_perf0()
        freq = core.get_freq()
        return perf0* freq**(1-app.m)

    def speedup(self, app):
        f = app.f

        sperf = self.__serial_perf(app)
        pperf = self.__parallel_perf(app)

        #return 1/((1-f)/sperf + f/(pperf*self._cnum*self._util_ratio))
        return 1/((1-f)/sperf + f/(pperf*self._util_ratio*self._area/self._core.get_area()))

    def get_util_max(self):
        return self._util_ratio_max

    def get_util_min(self):
        return self._util_ratio_min
    
    def get_core_num(self):
        return self._cnum
