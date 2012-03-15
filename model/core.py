#!/usr/bin/env python
""""
@author: Liang Wang <liang@cs.virginia.edu>
"""

import math
from tech import Base as techbase, Scale as techscl
from tech import LPBase as lpbase, PTMScale as ptmscl
import freq

from conf import misc as miscConfig
DEBUG=miscConfig.debug

MC_CKT='adder'
#TODO: add code to MC_BEST case
MC_BEST = False
class Core(object):
    """
    Core module
    """
    def __init__(self, ctype=None, mech=None, tech=None, pv=False, pen_adjust=None):

        update = True

        if ctype is None:
            update=False
        else:
            self._ctype = ctype

        if mech is None:
            update=False
        else:
            self._mech = mech

        if tech is None:
            update=False
        else:
            self._tech = tech

        
        self._pv = pv
        self.pen_adjust = pen_adjust

        if update:
            self.__update_config()


    def __update_config(self):
        """ Internal function to update value of mech/ctype/tech specific parameters """
        tech = self._tech
        mech = self._mech
        ctype = self._ctype
        pv = self._pv

        self._perf0 = math.sqrt(techbase.area[ctype])
        
        self._area = techbase.area[ctype] * techscl.area[tech]
        
        self._fsf = 1
        self._vsf = 1       

        if mech == 'ITRS' or mech == 'CONS':
            # Projection-based scaling, 'ITRS' or 'CONS'
            self._vt = techbase.vt * techscl.vt[tech]
            self._v0 = techbase.vdd * techscl.vdd[mech][tech]
            self._f0 = techbase.freq[ctype] * techscl.freq[mech][tech]
            
            self._dp0 = techbase.dp[ctype] * techscl.power[mech][tech]
            self._sp0 = techbase.sp[ctype] * techscl.power[mech][tech]
            if pv:
                print 'Projection-based scaling does not support process variation'

        elif mech == 'HKMGS':
            
            self._vt = ptmscl.vt[mech][tech]
            v0 = ptmscl.vdd[mech][tech]
            f0 = techbase.freq[ctype] * ptmscl.freq[mech][tech]
            #if pv:
                #mcmodel=freq.PTMScaleMC(MC_CKT, mech, tech, v0, f0)
                #self._v0 = v0
                #self._f0 = f0*mcmodel.freq_down
                #self._f0_nom = f0
                #if DEBUG:
                    #print 'mech: %s, tech: %d, freq_down: %g' % (mech, tech, model.freq_down)
            #else:
            self._v0 = v0
            self._f0 = f0
            
            self._dp0 = techbase.dp[ctype] * ptmscl.dp[mech][tech]
            self._sp0 = techbase.sp[ctype] * ptmscl.sp[mech][tech]
            #self._dp0 = techbase.dp[ctype] * ptmscl.dp[mech][tech]
            #self._sp0 = techbase.sp[ctype] * ptmscl.sp[mech][tech]

        elif mech == 'LP':
            self._vt = ptmscl.vt[mech][tech]
            v0 = ptmscl.vdd[mech][tech]
            f0 = techbase.freq[ctype] * ptmscl.freq['HKMGS'][tech] * lpbase.freq[tech]
            #if pv:
                #mcmodel=freq.PTMScaleMC(MC_CKT, mech, tech, v0, f0)
                #self._v0 = v0
                #self._f0 = f0*mcmodel.freq_down
                #self._f0_nom = f0
                #if DEBUG:
                    #print 'mech: %s, tech: %d, freq_down: %g' % (mech, tech, model.freq_down)
            #else:
            self._v0 = v0
            self._f0 = f0
            
            # dynamic power and static power use the same scaling factors
            #self._dp0 = techbase.dp[ctype] * lpbase.dp[tech] * techscl.power[mech][tech]
            #self._sp0 = techbase.sp[ctype] * lpbase.sp[tech] * techscl.power[mech][tech]
            self._dp0 = techbase.dp[ctype] * ptmscl.dp['HKMGS'][tech] * lpbase.dp[tech]
            self._sp0 = techbase.sp[ctype] * ptmscl.sp['HKMGS'][tech] * lpbase.sp[tech]
        
        

        if mech == 'ITRS' or mech == 'CONS':
            self._vsf_max = 1
            self._vsf_min = self._vt/self._v0

            self._model = freq.ProjectionScale(self._vt, self._v0, self._f0)
            self._sp_slope = self._model.sp_slope
        elif mech == 'HKMGS' or mech == 'LP':
            self._vsf_max = 1.1 / self._v0
            self._vsf_min = 0.3 / self._v0

            if pv:
                self._model = freq.PTMScaleMC(MC_CKT, mech, tech, v0, f0, self.pen_adjust)
                self.var_penalty = self._model.get_penalty(v0)
                #self._model_nom = freq.PTMScale(MC_CKT, mech, tech, self._v0, self._f0)
            else:
                self._model = freq.PTMScale(MC_CKT, mech, tech, self._v0, self._f0)

            #if pv:
                #self._sp_slope = self._mcmodel.sp_slope
            #else:
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
        #if self._pv:
            #return self._dp0 * self._fsf_nom * self._vsf**2
        #else:
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
        if self._pv:
            return self._f0 * self._fsf * self.var_penalty
        else:
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
    
    ## Update core configuration
    #_config_options = ('mech','ctype','tech','pv')
    
    def config(self, mech=None, ctype=None, tech=None, pv=None, pen_adjust=None):
        if mech is not None:
            self._mech=mech
        elif self._mech is None:
            print 'mech is not set, failed to config core'

        if ctype is not None:
            self._ctype=ctype
        elif self._ctype is None:
            print 'ctype is not set, failed to config core'

        if tech is not None:
            self._tech=tech
        elif self._tech is None:
            print 'tech is not set, failed to config core'

        if pv is not None:
            self._pv=pv
        elif self._pv is None:
            print 'pv is not set, failed to config core'

        if pen_adjust is not None:
            self.pen_adjust = pen_adjust

        self.__update_config()


    #def config(self, **kwargs):
        #""" Configurate core, available options are:
            #tech: Technology node, possible values: 45, 32, 22, 16, 11, 8
            #mech: Scaling mechanism, possible values: ITRS, CONS
            #ctype: Core type, possible values: IO, O3
            #"""
        #for k,v in kwargs.items():
            #k=k.lower()
            #if k not in self._config_options:
                #raise AttributeError("Can NOT set attribute %s" % k)
            #kk = '_'+k # translate key into internal name
            #setattr(self,kk,v)       
        #self.__update_config()


    def dvfs_by_factor(self, vsf):

        volt = self._v0 * vsf
        self._vsf = vsf

        scale = self._model
        freq = scale.get_freq(volt)
        self._fsf = freq / self._f0

        if self._pv:
            self.var_penalty = scale.get_penalty(volt)

    def dvfs_by_volt(self, v):
        self._vsf = v / self._v0
        scale = self._model
        freq = scale.get_freq(v)
        self._fsf = freq / self._f0

        if self._pv:
            self.var_penalty = scale.get_penalty(v)
        
    def scale_with_vlist(self, vlist):
        freqs = self._model.get_freqs(vlist)
        sp = 10**(vlist * self._sp_slope)/10**(self._v0*self._sp_slope) *self._sp0 
        #if not self._pv:
        dp = (freqs/self._f0) * (vlist/self._v0)**2 * self._dp0 
        #else:
            #freqs_nom = self._model_nom.get_freqs(vlist)
            #dp = (freqs_nom/self._f0_nom) * (vlist/self._v0)**2 * self._dp0

        if self._pv:
            var_penalties = self._model.get_penalties(vlist)
            return {'freq':freqs*var_penalties,
                    'dp': dp, 'sp': sp}
        else:
            return {'freq': freqs, 'dp': dp, 'sp': sp}


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
            c = Core(tech=tech, mech=mech, ctype='IO', pv=True)
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

