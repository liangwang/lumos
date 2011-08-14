#!/usr/bin/env python

import math
from Core import Core
from System import System

class AsymmetricSystem(System):
    def __init__(self, core=Core(), 
                 budget={'area':500, 'power':200}):
        System.__init__(self)
        
        self.set_core_budget(core, budget)

        self._util_ratio = self._util_min

    
    def util_ratio():
        """ @property: util_ratio """
        doc = "util_ratio: utilizaton ratio of the system"
        def fget(self):
            return self._util_ratio
        def fset(self, value):
            self._util_ratio = value
        return locals()
    util_ratio = property(**util_ratio())
    
    def core():
        """ @property: core """
        doc = "core: base core for the system"
        def fget(self):
            return self._core
        #def fset(self, value):
            #self._core = value
            #self._core_num = self._area / self._core.area
            #self.__update_util_boundary()
        return locals()
    core = property(**core())
    
    def core_num():
        """ @property: core_num """
        doc = "core_num: the number of available cores in system"
        def fget(self):
            return self._core_num
        return locals()
    core_num = property(**core_num())

    def power():
        """ @property: power """
        doc = "power: power budget for the system"
        def fget(self):
            return self._power
        def fset(self, value):
            self._power = value
            self.__update_util_boundary()
        return locals()
    power = property(**power())
    
    def area():
        """ @property: area """
        doc = "area: area budget for the system"
        def fget(self):
            return self._area
        def fset(self, value):
            self._area = value
            self.__update_util_boundary()
        return locals()
    area = property(**area())
    
    def util_max():
        """ @property: util_max """
        doc = "util_max: maximum utilization ratio of the system"
        def fget(self):
            return self._util_max
        return locals()
    util_max = property(**util_max())
    
    def util_min():
        """ @property: util_min """
        doc = "util_min: minimum utilization ratio of the system"
        def fget(self):
            return self._util_min
        return locals()
    util_min = property(**util_min())
    
    
    
    def set_budget(self, budget):
        self._power = budget['power']
        self._area = budget['area']
        
        self.__update_util_boundary()
        
    def set_core_budget(self, core, budget):
        self._power = budget['power']
        self._area = budget['area']
        
        self._core = core
        self._core_num = self._area / core.area

        self.__update_util_boundary()
        
    def __update_util_boundary(self):
        core = self._core

        core.dvfs(core.vsf_min)
        self._util_max = min( (self._power/core.power)/(self._area/core.area), 1)

        core.dvfs(core.vsf_max)
        self._util_min = (self._power/core.power)/(self._area/core.area)
        

    def __serial_perf(self, app):
        core = self._core
        core.dvfs(core.vsf_max)
        perf0 = core.perf0
        freq = core.freq
        return perf0* freq**(1-app.m)

    def __parallel_perf(self, app):
        core = self._core
        a0 = core.area
        p0 = core.p0
        v_factor = math.pow( (self._power*a0)/(self._util_ratio*p0*self._area), 0.333)

        core.dvfs(v_factor)

        perf0 = core.perf0
        freq = core.freq
        return perf0* freq**(1-app.m)

    def speedup(self, app):
        f = app.f

        sperf = self.__serial_perf(app)
        pperf = self.__parallel_perf(app)

        #return 1/((1-f)/sperf + f/(pperf*self._core_num*self._util_ratio))
        speedup = 1/((1-f)/sperf + f/(pperf*self._util_ratio*self._area/self._core.area))
        return speedup

    
    def set_core_prop(self, **kwargs):
        for k,v in kwargs.items():
            k=k.lower()
            setattr(self._core, k, v)

        self.__update_util_boundary()

