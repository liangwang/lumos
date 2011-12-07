#!/usr/bin/env python
""""
@author: Liang Wang <liang@cs.virginia.edu>
"""

import math
from Tech import Base as techbase, Scale as techscl
from Tech import LPBase as lpbase, PTMScale as ptmscl
from Freq import FreqScale,FreqScale2,FreqScaleMC

from conf import misc as miscConfig

MC_CKT='adder'
#TODO: add code to MC_BEST case
MC_BEST = False
class Core(object):
    """
    Core module
    """
    def __init__(self, ctype='IO', mech='ITRS', tech=45, variation=False):

        self._tech = tech
        self._mech = mech
        self._ctype = ctype
        
        self._variation = variation

 

        if mech == 'ITRS' or mech == 'CONS':
            self._vt = techbase.vt * techscl.vt[tech]
            self._v0 = techbase.vdd * techscl.vdd[mech][tech]
            self._f0 = techbase.freq[ctype] * techscl.freq[mech][tech]
            
            # dynamic power and static power use the same scaling factors
            self._dp0 = techbase.dp[ctype] * techscl.power[mech][tech]
            self._sp0 = techbase.sp[ctype] * techscl.power[mech][tech]
        elif mech == 'HKMGS':
            if variation:
                self._vt = ptmscl.vt[mech][tech]
                v0 = ptmscl.vdd[mech][tech]
                f0 = techbase.freq[ctype] * ptmscl.freq[mech][tech]
                model=FreqScaleMC(MC_CKT, mech, tech, v0, f0)
                self._v0 = v0
                self._f0 = f0 * model.freq_down
                if miscConfig.debug:
                    print 'mech: %s, tech: %d, freq_down: %g' % (self._mech, self._tech, model.freq_down)
                # dynamic power and static power use the same scaling factors
                self._dp0 = techbase.dp[ctype] * techscl.power[mech][tech]
                self._sp0 = techbase.sp[ctype] * techscl.power[mech][tech]

                if MC_BEST:
                    self._dp0 = self._dp0 * model.dp_down
                    self._sp0 = self._sp0 * model.sp_down

            else:
                self._vt = ptmscl.vt[mech][tech]
                self._v0 = ptmscl.vdd[mech][tech]
                self._f0 = techbase.freq[ctype] * ptmscl.freq[mech][tech]
                
                # dynamic power and static power use the same scaling factors
                self._dp0 = techbase.dp[ctype] * techscl.power[mech][tech]
                self._sp0 = techbase.sp[ctype] * techscl.power[mech][tech]
            #self._dp0 = techbase.dp[ctype] * ptmscl.dp[mech][tech]
            #self._sp0 = techbase.sp[ctype] * ptmscl.sp[mech][tech]

        elif mech == 'LP':
            if variation:
                self._vt = ptmscl.vt[mech][tech]
                v0 = ptmscl.vdd[mech][tech]
                f0 = techbase.freq[ctype] * lpbase.freq[tech] * ptmscl.freq[mech][tech]
                model=FreqScaleMC(MC_CKT, mech, tech, v0, f0)
                self._v0 = v0
                self._f0 = f0 * model.freq_down
                if miscConfig.debug:
                    print 'mech: %s, tech: %d, freq_down: %g' % (self._mech, self._tech, model.freq_down)

            else:
                self._vt = ptmscl.vt[mech][tech]
                self._v0 = ptmscl.vdd[mech][tech]
                self._f0 = techbase.freq[ctype] * lpbase.freq[tech] * ptmscl.freq[mech][tech]
            
            # dynamic power and static power use the same scaling factors
            self._dp0 = techbase.dp[ctype] * lpbase.dp[tech] * techscl.power[mech][tech]
            self._sp0 = techbase.sp[ctype] * lpbase.sp[tech] * techscl.power[mech][tech]
            #self._dp0 = techbase.dp[ctype] * lpbase.dp[tech] * ptmscl.dp[mech][tech]
            #self._sp0 = techbase.sp[ctype] * lpbase.sp[tech] * ptmscl.sp[mech][tech]
        else:
            print 'Unknown mech'
        

        self._perf0 = math.sqrt(techbase.area[ctype])
        
        self._area = techbase.area[ctype] * techscl.area[tech]
        
        self._fsf = 1
        self._vsf = 1       
        

        if mech == 'ITRS' or mech == 'CONS':
            self._vsf_max = 1
            self._vsf_min = self._vt/self._v0

            self._model = FreqScale(self._vt, self._v0, self._f0)
            self._sp_slope = self._model.sp_slope
        elif mech == 'HKMGS' or mech == 'LP':
            self._vsf_max = 1.1 / self._v0
            self._vsf_min = 0.3 / self._v0

            if variation:
                self._model = model
            else:
                self._model = FreqScale2(MC_CKT, mech, tech, self._v0, self._f0)
            self._sp_slope = self._model.sp_slope



    @property
    def tech(self):
        """ Get the technology node, in nm """
        return self._tech
    
    @property
    def mech(self):
        """ Get the scaling mechanism, either ITRS or CON(servative) """
        return self._mech
    
    @property
    def ctype(self):
        """ Get the core type, either IO or O3 """
        return self._ctype
    
    @property
    def dp0(self):
        """ Get the dynamic power in nominal voltage and frequency """
        return self._dp0
    @property
    def dp(self):
        """ Get the dynamic power """
        return self._dp0 * self._fsf * self._vsf**2
    
    @property
    def sp0(self):
        """ Get the static(leakage) power in nominal voltage and frequency """
        return self._sp0

    @property
    def sp(self):
        """ Get the static power """
        
        # FIXME: validate slope of 0.8?
        #return (self._sp0 * self._vsf *  
        return (self._sp0 *  
                10**(self._v0 * self._vsf * self._sp_slope) / 
                10**(self._v0 * self._sp_slope) )
    
    @property
    def power(self):
        """ Get the overall power """
        return self.sp + self.dp
    
    @property
    def v0(self):
        """ Get the nominal voltage """
        return self._v0
    @property
    def vdd(self):
        """ Get the supplying voltage """
        return self._v0 * self._vsf
    
    @property
    def f0(self):
        """ Get the nominal frequency """
        return self._f0   

    @property
    def freq(self):
        """ Get the frequency """
        return self._f0 * self._fsf


    @property
    def perf0(self):
        """ Get the base performance """
        return self._perf0
    
    @property
    def vt(self):
        """ Get the threshold voltage """
        return self._vt
    
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
    _config_options = ('mech','ctype','tech','variation')
    
    def __update_config(self):
        """ Internal function to update value of mech/ctype/tech specific parameters """
        # dynamic power and static power use the same scaling factors
        self._dp0 = techbase.dp[self._ctype] * techscl.power[self._mech][self._tech]
        self._sp0 = techbase.sp[self._ctype] * techscl.power[self._mech][self._tech]
        if self._mech == 'ITRS' or self._mech == 'CONS':
            self._vt = techbase.vt * techscl.vt[self._tech]
            self._v0 = techbase.vdd * techscl.vdd[self._mech][self._tech]
            self._f0 = techbase.freq[self._ctype] * techscl.freq[self._mech][self._tech]
            
            self._dp0 = techbase.dp[self._ctype] * techscl.power[self._mech][self._tech]
            self._sp0 = techbase.sp[self._ctype] * techscl.power[self._mech][self._tech]
        elif self._mech == 'HKMGS':
            if self._variation:
                self._vt = ptmscl.vt[self._mech][self._tech]
                v0 = ptmscl.vdd[self._mech][self._tech]
                f0 = techbase.freq[self._ctype] * ptmscl.freq[self._mech][self._tech]
                model=FreqScaleMC(MC_CKT, self._mech, self._tech, v0, f0)
                self._v0 = v0
                self._f0 = f0*model.freq_down
                if miscConfig.debug:
                    print 'mech: %s, tech: %d, freq_down: %g' % (self._mech, self._tech, model.freq_down)
            else:
                self._vt = ptmscl.vt[self._mech][self._tech]
                self._v0 = ptmscl.vdd[self._mech][self._tech]
                self._f0 = techbase.freq[self._ctype] * ptmscl.freq[self._mech][self._tech]
            
            # dynamic power and static power use the same scaling factors
            self._dp0 = techbase.dp[self._ctype] * techscl.power[self._mech][self._tech]
            self._sp0 = techbase.sp[self._ctype] * techscl.power[self._mech][self._tech]
            #self._dp0 = techbase.dp[self._ctype] * ptmscl.dp[self._mech][self._tech]
            #self._sp0 = techbase.sp[self._ctype] * ptmscl.sp[self._mech][self._tech]

        elif self._mech == 'LP':
            if self._variation:
                self._vt = ptmscl.vt[self._mech][self._tech]
                v0 = ptmscl.vdd[self._mech][self._tech]
                f0 = techbase.freq[self._ctype] * lpbase.freq[self._tech] * ptmscl.freq[self._mech][self._tech]
                model=FreqScaleMC(MC_CKT, self._mech, self._tech, v0, f0)
                self._v0 = v0
                self._f0 = f0*model.freq_down
                if miscConfig.debug:
                    print 'mech: %s, tech: %d, freq_down: %g' % (self._mech, self._tech, model.freq_down)
            else:
                self._vt = ptmscl.vt[self._mech][self._tech]
                self._v0 = ptmscl.vdd[self._mech][self._tech]
                self._f0 = techbase.freq[self._ctype] * lpbase.freq[self._tech] * ptmscl.freq[self._mech][self._tech]
            
            # dynamic power and static power use the same scaling factors
            self._dp0 = techbase.dp[self._ctype] * lpbase.dp[self._tech] * techscl.power[self._mech][self._tech]
            self._sp0 = techbase.sp[self._ctype] * lpbase.sp[self._tech] * techscl.power[self._mech][self._tech]
            #self._dp0 = techbase.dp[self._ctype] * lpbase.dp[self._tech] * ptmscl.dp[self._mech][self._tech]
            #self._sp0 = techbase.sp[self._ctype] * lpbase.sp[self._tech] * ptmscl.sp[self._mech][self._tech]
        
        self._perf0 = math.sqrt(techbase.area[self._ctype])
        
        self._area = techbase.area[self._ctype] * techscl.area[self._tech]
        
        self._fsf = 1
        self._vsf = 1       
        

        if self._mech == 'ITRS' or self._mech == 'CONS':
            self._vsf_max = 1
            self._vsf_min = self._vt/self._v0

            self._model = FreqScale(self._vt, self._v0, self._f0)
            self._sp_slope = self._model.sp_slope
        elif self._mech == 'HKMGS' or self._mech == 'LP':
            self._vsf_max = 1.1 / self._v0
            self._vsf_min = 0.3 / self._v0

            if self._variation:
                self._model = model
            else:
                self._model = FreqScale2(MC_CKT, self._mech, self._tech, self._v0, self._f0)
            self._sp_slope = self._model.sp_slope
        
    def config(self, **kwargs):
        """ Configurate core, available options are:
            tech: Technology node, possible values: 45, 32, 22, 16, 11, 8
            mech: Scaling mechanism, possible values: ITRS, CONS
            ctype: Core type, possible values: IO, O3
            """
        for k,v in kwargs.items():
            k=k.lower()
            if k not in self._config_options:
                raise AttributeError("Can NOT set attribute %s" % k)
            kk = '_'+k # translate key into internal name
            setattr(self,kk,v)       
        self.__update_config()


    def dvfs_by_factor(self, vsf):

        volt = self._v0 * vsf
        self._vsf = vsf

        scale = self._model
        freq = scale.get_freq(volt)
        self._fsf = freq / self._f0

    def dvfs_by_volt(self, v):
        self._vsf = v / self._v0
        scale = self._model
        freq = scale.get_freq(v)
        self._fsf = freq / self._f0
        
    def set_prop(self, **kwargs):
        for k,v in kwargs.items():
            k=k.lower()
            setattr(self, k, v)



def plot_split(v, f, dp, sp, p, tech):
    fig = plt.figure()
    fig.suptitle('Technology node at %dnm' % (tech,))
    axes = fig.add_subplot(111)
    axes.set_xlabel('Supply Voltage (V)')
    axes.set_ylabel('Frequency (GHz)')
    axes.plot(v,f,v,f,'rD')
    axes.set_xlim(0,1.1)
    axes.set_yscale('log')
    axes.legend(axes.lines, ['Fitting', 'Simulated'], loc='upper left')
    axes.grid(True)
    fig.savefig('freq_volt.pdf')

    fig = plt.figure()
    axes = fig.add_subplot(111)
    axes.set_xlabel('Supply Voltage (V)')
    axes.set_ylabel('Power (W)')
    axes.plot(v,dp,'-D', v,sp,'-o', v,p,'-^')
    axes.set_xlim(0,1.1)
    axes.set_yscale('log')
    axes.legend(axes.lines, ['Dynamic Power', 'Static Power','Overall'], loc='upper left', prop=dict(size='medium'))
    axes.grid(True)
    fig.savefig('power.pdf')
    
def plot_nosplit(v,f,dp,sp,p, tech, mech):
    fig = plt.figure(figsize=(13.5, 6.9))
    fig.suptitle('%dnm' % (tech,))

    # Frequency scaling plot
    axes1 = fig.add_subplot(121)
    axes1.plot(v, f, marker='s')
    axes1.set_yscale('log')
    axes1.set_title('Freq')
    axes1.set_xlim(0.2,1.2)

    # Power scaling plot
    axes2 = fig.add_subplot(122)
    axes2.plot(v,dp, v,sp, v,p)
    axes2.set_yscale('log')
    axes2.set_title('Power')
    axes2.set_xlim(0.2,1.2)

    fig.savefig('%s_core_%dnm.png' % (mech,tech,))




if __name__ == '__main__':
    """"
    This is a test program to generate freq/power plots for Core
    """
    import matplotlib.pyplot as plt
    techList = (45,32,22,16)
    mechList = ('LP', 'HKMGS')
    vsList = [ x*0.05 for x in xrange(6,23) ]
    for tech in techList:
        for mech in mechList:
            c = Core(tech=tech, mech=mech)
            #c.config(tech=32)
            #print 'tech:%d, mech: %s, dp: %f, sp: %f, freq:%f' % (tech, mech, c.dp0, c.sp0, c.freq)

            fs = []
            dp = []
            sp = []
            p=[]

            for v in vsList:
                c.dvfs_by_volt(v)
                fs.append(c.freq)
                dp.append(c.dp)
                sp.append(c.sp)
                p.append(c.power)
                
            #plot_split(vs, fs, dp, sp, p, tech)
            plot_nosplit(vsList, fs, dp, sp, p, tech, mech)

