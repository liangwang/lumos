#!/usr/bin/env python

import math
from technology import Base as techbase
from technology import Scale as techscl

class Core:
    def __init__ (self):
        self.area = 0
        self.tech = 0
        self.mech = 'itrs'
        self.f0 = 0
        self.v0 = 0
        self.p0 = 0
        self.perf0 = 0
        self.ag_dvfs = False

        #self.freq = 0
        #self.v = 0
        #self.dvfsv = 0
        #self.dvfsf = 0

    def get_dvfs_lb(self):
        if self.ag_dvfs : 
            vth = techbase.vth[self.tech]
            vnorm = techbase.vdd * techscl.vdd[self.mech][self.tech]
            return vth/vnorm
        else:
            return 0.7

    def get_dvfs_ub(self):
        return 1.3

    def dvfs(self, v_factor):
        """ When tuning up/down the voltage, how would frequency changes
        
        ratio -- scaling factor for voltage
        
        """
        dvfs_lb = self.get_dvfs_lb()
        dvfs_ub = self.get_dvfs_ub()
        if v_factor > dvfs_ub:
            v_factor = dvfs_ub
        if v_factor < dvfs_lb:
            v_factor = dvfs_lb

        v = self.v0 * v_factor
        vth = techbase.vth[self.tech]
        vmin = v - vth
        vmin0 = self.v0 - vth

        #freq_factor = ((v * vmin - vmin**2 / 2) / (self.v0 * vmin0 - vmin0**2 / 2)) / v_factor
        freq_factor =  v_factor

        perf = self.perf0 * freq_factor * self.f0

        power = self.p0 * v_factor**2 * freq_factor

        return freq_factor, perf, power

class IOCore(Core):
    def __init__ (self, mech='itrs', tech=45, volt=1.0, freq=4.2):
        Core.__init__(self)
        self.f0=techbase.freq['io']* techscl.freq[mech][tech]
        self.p0=techbase.power['io']* techscl.power[mech][tech]
        self.v0=techbase.vdd * techscl.vdd[mech][tech]
        self.perf0 = math.sqrt(techbase.area['io'])
        
        self.area=techbase.area['io']* techscl.area[tech]
        self.mech = mech
        self.tech = tech

        self.name='io'

        
class O3Core(Core):
    def __init__ (self, mech='itrs', tech=45, volt=1.0, freq=3.7):
        Core.__init__(self)
        self.f0=techbase.freq['o3']* techscl.freq[mech][tech]
        self.p0=techbase.power['o3']* techscl.power[mech][tech]
        self.v0=techbase.vdd * techscl.vdd[mech][tech]
        self.perf0 = math.sqrt(techbase.area['o3'])
        
        self.area=techbase.area['o3']* techscl.area[tech]
        self.mech = mech
        self.tech = tech

        self.name = 'o3'

