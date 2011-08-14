#!/usr/bin/env python

import math
from Tech import Base as techbase, Scale as techscl
from Freq import FreqScale

class Core(object):
    def __init__(self, type='IO', mech='ITRS', tech=45):
        self._tech = tech
        self._mech = mech
        self._type = type
 
        self._vth = techbase.vth * techscl.vth[self._tech]
        self._v_nom = techbase.vdd * techscl.vdd[self._tech]
        self._f_nom = techbase.freq[self._type] * techscl.freq[self._mech][self._tech]
        
        # dynamic power and static power use the same scaling factors
        self._dp_nom = techbase.dp[self._type] * techscl.power[self._mech][self._tech]
        self._sp_nom = techbase.sp[self._type] * techscl.power[self._mech][self._tech]
        
        self._perf_nom = math.sqrt(techbase.area[self._type])
        
        self._area = techbase.area[self._type] * techscl.area[self._tech]
        
        self._fsf = 1
        self._vsf = 1       
        

        self._vsf_max = 1
        self._vsf_min = self._vth/self._v_nom


        self._model = FreqScale(self._vth, self._v_nom, self._f_nom)

    @property
    def tech(self):
        """ Get the technology node, in nm """
        return self._tech
    
    @property
    def mech(self):
        """ Get the scaling mechanism, either ITRS or CON(servative) """
        return self._mech
    
    @property
    def type(self):
        """ Get the core type, either IO or O3 """
        return self._type
    
    @property
    def dp_nom(self):
        """ Get the dynamic power in nominal voltage and frequency """
        return self._dp_nom
    @property
    def dp(self):
        """ Get the dynamic power """
        return self._dp_nom * self._fsf * self._vsf**2
    
    @property
    def sp_nom(self):
        """ Get the static(leakage) power in nominal voltage and frequency """
        return self._sp_nom
    @property
    def sp(self):
        """ Get the static power """
        
        # FIXME: validate slope of 0.8?
        return self._sp_nom * self._vsf * 10**(self._vsf/0.8)/10**(1/0.8)
    
    @property
    def power(self):
        """ Get the overall power """
        return self.sp + self.dp
    
    @property
    def v_nom(self):
        """ Get the nominal voltage """
        return self._v_nom
    @property
    def vdd(self):
        """ Get the supplying voltage """
        return self._v_nom * self._vsf
    
    @property
    def f_nom(self):
        """ Get the nominal frequency """
        return self._f_nom   
    @property
    def freq(self):
        """ Get the frequency """
        return self._f_nom * self._fsf
    
    @property
    def vth(self):
        """ Get the threshold voltage """
        return self._vth
    
    @property
    def area(self):
        """ Get the area of the core """
        return self._area 
    
    @property
    def vsf_max(self):
        """ voltage scaling factor, maximum """
        return self._vsf_max
    
    @property
    def vsf_min(self):
        """ voltage scaling factor, minimum """
        return self._vsf_min
    
    # Update core configuration
    _config_options = ('mech','type','tech')
    
    def _update_config(self):
        """ Internal function to update value of mech/type/tech specific parameters """
        self._vth = techbase.vth * techscl.vth[self._tech]
        self._v_nom = techbase.vdd * techscl.vdd[self._tech]
        self._f_nom = techbase.freq[self._type] * techscl.freq[self._mech][self._tech]
        
        # dynamic power and static power use the same scaling factors
        self._dp_nom = techbase.dp[self._type] * techscl.power[self._mech][self._tech]
        self._sp_nom = techbase.sp[self._type] * techscl.power[self._mech][self._tech]
        
        self._perf_nom = math.sqrt(techbase.area[self._type])
        
        self._area = techbase.area[self._type] * techscl.area[self._tech]
        
        # reset all DVFS scaling factors
        # FiXME: necessary?
        self._fsf = 1
        self._vsf = 1
        
        self._vsf_max = 1
        self._vsf_min = self._vth/self._v_nom
        
    def config(self, **kwargs):
        """ Configurate core, available options are:
            tech: Technology node, possible values: 45, 32, 22, 16, 11, 8
            mech: Scaling mechanism, possible values: ITRS, CONS
            type: Core type, possible values: IO, O3
            """
        for k,v in kwargs.items():
            k=k.lower()
            if k not in self._config_options:
                raise AttributeError("Can NOT set attribute %s" % k)
            setattr(self,k,v)       
        self._update_config()


    def dvfs(self, vsf):
        self.volt = self.v0 * vsf
        self._vsf = vsf

        scale = self._model
#        self.freq = scale.get_freqs_in_ghz(self.volt)
        self.freq = scale.get_freqs(self.volt)
        self._fsf = self.freq / self.f0

        
    def set_prop(self, **kwargs):
        for k,v in kwargs.items():
            k=k.lower()
            setattr(self, k, v)


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
