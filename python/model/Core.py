#!/usr/bin/env python

import math

from Technology import Base as techbase
from Technology import Scale as techscl

class Core:
    def __init__ (self, type='io',
                 mech='itrs', tech=45):
        self._tech = tech
        self._mech = mech
        self._type = type
        self.__update_base()

        self.ag_dvfs = False

        self._f_factor = 1
        self._v_factor = 1


    def __update_base(self):
        # default frequency
        self._f0=techbase.freq[self._type]* techscl.freq[self._mech][self._tech]

        # Power at norminal frequency
        self._p0=techbase.power[self._type]* techscl.power[self._mech][self._tech]

        # Norminal power at norminal frequency
        self._v0=techbase.vdd * techscl.vdd[self._mech][self._tech]

        # Perforamnce base factor (Pollack's Rule)
        self._perf0 = math.sqrt(techbase.area[self._type])

        # Area 
        self._area=techbase.area[self._type]* techscl.area[self._tech]

    def set_tech(self, tech):
        self._tech=tech

        self.__update_base()

    def set_mech(self, mech):
        self._mech = mech
        self.__update_base()

    def set_type(self, type):
        self._type = type
        self.__update_base()

    def get_dvfs_lb(self):
        if self.ag_dvfs : 
            vth = techbase.vth[self._tech]
            return vth/self._v0
        else:
            return 0.7

    def get_dvfs_ub(self):
        return 1.3

    def get_freq(self):
        return self._f0 * self._f_factor

    def get_power(self):
        return self._p0 * self._f_factor * self._v_factor**2

    def get_area(self):
        return self._area

    def get_perf0(self):
        return self._perf0

    def dvfs(self, v_factor):
        """ When tuning up/down the voltage, how would frequency changes
        
        ratio -- scaling factor for voltage
        
        """
        dvfs_ub = self.get_dvfs_ub()
        if v_factor > dvfs_ub:
            self._v_factor = dvfs_ub

        dvfs_lb = self.get_dvfs_lb()
        if v_factor < dvfs_lb:
            self._v_factor = dvfs_lb

        self._f_factor =  self.__v2f_simple(self._v_factor)

    def dvfs_max(self):
        """ Scale to the maximum voltage """
        self._v_factor = self.get_dvfs_ub()
        self._f_factor = self.__v2f_simple(self._v_factor)

    def dvfs_min(self):
        """ Scale to the minimum voltage """
        self._v_factor = self.get_dvfs_lb()
        self._f_factor = self.__v2f_simple(self._v_factor)

    def __v2f_simple(self, v_factor):
        return v_factor

    def __v2f_near_threshold(self, v_factor):
        """ More realistic scaling """
        #v = self._v0 * self._v_factor
        #vth = techbase.vth[self._tech]
        #vmin = v - vth
        #vmin0 = self._v0 - vth

        #freq_factor = ((v * vmin - vmin**2 / 2) / (self.v0 * vmin0 - vmin0**2 / 2)) / v_factor


class IOCore(Core):
    def __init__ (self, mech='itrs', tech=45):
        Core.__init__(self, type='io',
                     mech=mech, tech=tech)
        
        
class O3Core(Core):
    def __init__ (self, mech='itrs', tech=45):
        Core.__init__(self, type='o3',
                     mech=mech, tech=tech)

