#@PydevCodeAnalysisIgnore

#!/usr/bin/env python


import math

from Tech import Base as techbase
from Tech import Scale as techscl



class Core(object):
    def __init__ (self, type='IO',
                 mech='ITRS', tech=45,
                 dvfs_simple=True, alpha=1.4,
                 vslope=0.075, nth=0.2):
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
        # pivot is the boundary of near threshold region

        # boundary is dynamically set
        v_pivot = self._alpha*self.vslope+self._vth
        self.nth=v_pivot - self._vth

        # boundary is constantly set
        #v_pivot=self._vth + self.nth

        self._csuper = self._f0 * self._v0 / (self._v0-self._vth)**self._alpha

        self._csub = self._csuper * (v_pivot-self._vth)**self._alpha / 10**((v_pivot-self._vth)/(self.vslope))
        #self._csub = self._csub * 10

        self.dirty_scale()

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
            # Power at nominal frequency
            self._p0=techbase.power[self._type]* techscl.power[self._mech][self._tech]
            # Nominal power at nominal frequency
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
                #super = self._csuper * (v-self._vth)**self._alpha / v
                #sub = self._csub * 10**((v-self._vth)/self.vslope) / v
                #f = (v-self._vth)/self.nth
                #fsf = ((1-f)*sub+f*super) / base

                # dirty scaling for 45nm
                fsf = self._cnear * (2.916-15.2052*v+19.9008*v*v) / base
            else :
                # sub-threshold region
                #  should not happen in this case
                sub = self._csub * 10**((v-self._vth)/self.vslope) / v
                fsf = sub/base

        self._fsf = fsf 

        return fsf, self._f0*fsf

    # only for 45nm
    def dirty_scale(self):
        self.nth=0.3
        self._csuper = self._f0 / ( self._v0 / (self._v0-self._vth)**self._alpha / self._v0 )
        self._cnear = (self._csuper * (0.7-self._vth)**self._alpha / 0.7) / (2.916-15.2052*0.7+19.9008*0.7*0.7)
        self._csub = self._cnear * (2.916-15.2052*0.4+19.9008*0.4*0.4) * self._vth
        #print self._vth, self._csuper, self._cnear, self._csub

#discrete scaling core model
class Core45nm(object):
    def __init__(self):
        self.volt = 1.0
        self.freq = FS.freq[self.volt]

        self.p0=techbase.power['IO']
        self.f0=techbase.freq['IO']
        self.v0=techbase.vdd
        self.perf0 = math.sqrt(techbase.area['IO'])
        self.area=techbase.area['IO']

        self._fsf = 1
        self._vsf = 1

        self.vsf_max = 1
        self.vsf_min = 0.2

    def power():
        """ @property: power """
        doc = "The power property."
        def fget(self):
            return self.p0 * self._fsf * self._vsf**2
        return locals()
    power = property(**power())


    def dvfs(self, vsf):
        self.volt = self.v0 * vsf
        self._vsf = vsf

        self.freq =  FS.freq[self.volt]
        self._fsf = self.freq / self.f0

        
    def set_prop(self, **kwargs):
        for k,v in kwargs.items():
            k=k.lower()
            setattr(self, k, v)

# concret scaling core model
import numpy as np
from Freq import FreqScale
class Core45nmCon(object):
    def __init__(self):
        self.volt = 1.0
#        self.freq = FreqScale.freq_in_ghz[self.volt]
        
        self.vth = techbase.vth

        self.p0=techbase.power['IO']
        self.f0=techbase.freq['IO']
        self.freq = techbase.freq['IO']
        self.v0=techbase.vdd
        self.perf0 = math.sqrt(techbase.area['IO'])
        self.area=techbase.area['IO']
        self.pleak = techbase.pleak['IO']

        self._fsf = 1
        self._vsf = 1

        self.vsf_max = 1
        self.vsf_min = 0.2

        #build interpolation model
#        volts=np.arange(0.2,1.1,0.1) #from 0.2 to 1
#        freqs=np.array([0.00017,0.00241,0.02977,0.25342,0.99234,2.01202,2.91069,3.60153,4.2])
        self.model = FreqScale(self.vth, self.v0, self.f0)

    def power():
        """ @property: power """
        doc = "The power property."
        def fget(self):
            return self.p0 * self._fsf * self._vsf**2 + self.pleak * self._vsf * 10**(self._vsf/0.8)/10**(1/0.8)
        return locals()
    power = property(**power())


    def dvfs(self, vsf):
        self.volt = self.v0 * vsf
        self._vsf = vsf

        scale = self.model
#        self.freq = scale.get_freqs_in_ghz(self.volt)
        self.freq = scale.get_freqs(self.volt)
        self._fsf = self.freq / self.f0

        
    def set_prop(self, **kwargs):
        for k,v in kwargs.items():
            k=k.lower()
            setattr(self, k, v)
