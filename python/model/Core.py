#!/usr/bin/env python

import math

from Technology import Base as techbase
from Technology import Scale as techscl

class Core(object):
    def __init__ (self, type='IO',
                 mech='ITRS', tech=45,
                 dvfs_simple=True, alpha=1.4,
                 vslope=0.09, nth=0.2):
        self._tech = tech
        self._mech = mech
        self._type = type

        # Velocity saturation factor (alpha power law)
        self._alpha = alpha

        # use simple scaling or not
        self.dvfs_simple = dvfs_simple

        # sub-threshold voltage slope
        self.vslope = vslope

        # length of near threshold region
        self.nth = nth

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

        # Threshold Voltage
        self._vth = techbase.vth[self._tech]

        self.__update_scaling_constant()

        self._fsf = 1
        self._vsf = 1

    def __update_scaling_constant(self):
        #v_pivot = self._alpha*self.vslope/math.log(10)+self._vth
        v_pivot=self._vth + self.nth
        self._csuper = self._f0 * self._v0 / (self._v0-self._vth)**self._alpha

        self._csub = self._csuper * (v_pivot-self._vth)**self._alpha / 10**((v_pivot-self._vth)/(self.vslope))

    def alpha():
        """ @property: alpha """
        doc = "alpha: velocity saturation factor in alpha-power law"
        def fget(self):
            return self._alpha
        def fset(self, value):
            self._alpha = value
            self.__update_scaling_constant()
        return locals()
    alpha = property(**alpha())

    def tech():
        """ @property: tech """
        doc = "tech: technology node in nm, default is 45"
        def fget(self):
            return self._tech
        def fset(self, value):
            self._tech = value
            # default frequency
            self._f0=techbase.freq[self._type]* techscl.freq[self._mech][self._tech]
            # Power at norminal frequency
            self._p0=techbase.power[self._type]* techscl.power[self._mech][self._tech]
            # Norminal power at norminal frequency
            self._v0=techbase.vdd * techscl.vdd[self._mech][self._tech]
            # Area 
            self._area=techbase.area[self._type]* techscl.area[self._tech]
            # Threshold Voltage
            self._vth = techbase.vth[self._tech]
            self.__update_scaling_constant()
        return locals()
    tech = property(**tech())
    
    def freq():
        """ @property: freq """
        doc = "The freq property."
        def fget(self):
            return self._f0 * self._fsf
        return locals()
    freq = property(**freq())

    def volt():
        """ @property: volt """
        doc = "volt: voltage of the core"
        def fget(self):
            return self._v0 * self._vsf
        return locals()
    volt = property(**volt())
    
    def power():
        """ @property: power """
        doc = "The power property."
        def fget(self):
            return self._p0 * self._fsf * self._vsf**2
        return locals()
    power = property(**power())

    def area():
        """ @property: area """
        doc = "The area property."
        def fget(self):
            return self._area
        return locals()
    area = property(**area())

    def perf0():
        """ @property: perf0 """
        doc = "The perf0 property."
        def fget(self):
            return self._perf0
        return locals()
    perf0 = property(**perf0())

    def p0():
        """ @property: p0 """
        doc = "The p0 property."
        def fget(self):
            return self._p0
        return locals()
    p0 = property(**p0())
    
    def mech():
        """ @property: mech """
        doc = "mech: scaling mechanism, default is 'ITRS'"
        def fget(self):
            return self._mech
        def fset(self, value):
            self._mech = value
            # default frequency
            self._f0=techbase.freq[self._type]* techscl.freq[self._mech][self._tech]
            # Power at norminal frequency
            self._p0=techbase.power[self._type]* techscl.power[self._mech][self._tech]
            # Norminal power at norminal frequency
            self._v0=techbase.vdd * techscl.vdd[self._mech][self._tech]
            self.__update_scaling_constant()
        return locals()
    mech = property(**mech())

    def type():
        """ @property: type """
        doc = "type: core type, default is 'io'"
        def fget(self):
            return self._type
        def fset(self, value):
            self._type = value
            # default frequency
            self._f0=techbase.freq[self._type]* techscl.freq[self._mech][self._tech]
            # Power at norminal frequency
            self._p0=techbase.power[self._type]* techscl.power[self._mech][self._tech]
            # Perforamnce base factor (Pollack's Rule)
            self._perf0 = math.sqrt(techbase.area[self._type])
            # Area 
            self._area=techbase.area[self._type]* techscl.area[self._tech]
            self.__update_scaling_constant()
        return locals()
    type = property(**type())
    
    def vth():
        """ @property: vth """
        doc = "vth: threshold voltage for a certain technology node"
        def fget(self):
            return self._vth
        return locals()
    vth = property(**vth())

    def vsf_min():
        """ @property: vsf_min """
        doc = "vsf_min: voltage scaling factor, minimum"
        def fget(self):
            return 0.7 if self.dvfs_simple else self._vth/self._v0
        return locals()
    vsf_min = property(**vsf_min())
    
    def vsf_max():
        """ @property: vsf_max """
        doc = "vsf_max: voltage scaling factor, maximum"
        def fget(self):
            return 1.3
        return locals()
    vsf_max = property(**vsf_max())

    def dvfs(self, vsf):
        """ When tuning up/down the voltage, how would frequency changes
        
        vsf -- voltage scaling factor
        
        """
        self._vsf = vsf

        if self.dvfs_simple:
            fsf = vsf
        else:
            """ More realistic scaling """
            v = self._v0 * vsf
            base = self._csuper*(self._v0-self._vth)**self._alpha/self._v0
            if v >= self._vth + self.nth: 
                # super-threshold region
                super = self._csuper * (v-self._vth)**self._alpha / v
                fsf = super/base
            elif v >= self._vth: 
                # near-threshold region
                super = self._csuper * (v-self._vth)**self._alpha / v
                sub = self._csub * 10**((v-self._vth)/self.vslope)
                f = (v-self._vth)/self.nth
                fsf = ((1-f)*sub+f*super) / base
            else :
                # sub-threshold region
                #  should not happen in this case
                sub = self._csub * 10**((v-self._vth)/self.vslope)
                fsf = sub/base

        self._fsf = fsf 

        return fsf, self._f0*fsf

