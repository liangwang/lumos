#!/usr/bin/env python

import numpy as np
from scipy.interpolate import InterpolatedUnivariateSpline as IUSpline
from Tech import Base as techbase
import XLSParser
from os.path import join as joinpath
import math

class FreqScale:
    __DATA_FILE=joinpath('data','inv_45.xls')
    __DATA_OLD=joinpath('data','inv_45_sudhanshu.xls')

    #inv_mhz = {   1: 22306.73,
                #0.9: 19128.17,
                #0.8: 15459.06,
                #0.7: 10686.1,
                #0.6: 5270.448,
                #0.5: 1345.931,
                #0.4: 158.1074,
               #0.35: 44.96318,
                #0.3: 12.78681,
               #0.25: 3.35367,
                #0.2: 0.879594}
    #inv_v = [v for v in sorted(inv_mhz.iterkeys())]
    #inv_f = [inv_mhz[v] for v in inv_v]
    #model = itpl.InterpolatedUnivariateSpline(np.array(inv_v),
                                              #np.array(inv_f),
                                              #k=3)
    
    #data = {1: 4200,
            #0.9: 3601.53,
            #0.8: 2910.69,
            #0.7: 2012.02,
            #0.6: 992.341,
            #0.5: 253.417,
            #0.4: 29.7691,
            #0.35:8.46594,
            #0.3: 2.40755,
            #0.25:0.63145,
            #0.2: 0.16561}
    
    #freq_in_ghz = dict([(v, data[v]/1000) for v in sorted(data.iterkeys())])
    #freq_in_mhz = dict([(v, data[v]) for v in sorted(data.iterkeys())])

    inv_vth = 0.5
    
    def __init__(self, vth, v0, f0):
        
        p = XLSParser.XLSParser()
        p.parse(self.__DATA_FILE)
        dict_freq = p.get_freqs()
        inv_v = [v for v in sorted(dict_freq.iterkeys())]
        inv_f = [dict_freq[v] for v in inv_v]
        self.model = IUSpline(np.array(inv_v), np.array(inv_f), k=3)


        # FIXME: confirm vt for this technology
        # FIXME: use over-drive voltage(v-vt) other than relative (v/vt)

        # use relative voltage
        #self.v_translator = inv_vth / vth
        #v = v0 * self.v_translator
        # use over-drive voltage
        #   v = v_inv + v_translator
        self.v_translator = vth - self.inv_vth
        v = v0 - self.v_translator
        
        f = self.model(v)

        # use relative frequency
        #   f = f_inv * f_translator
        self.f_translator = f0/f
        
        sp=p.get_static_power()
        volts = sorted(sp.iterkeys())
        st_power = [(sp[v]) for v in volts]
        self.sp_slope = ((math.log10(st_power[-1])-math.log10(st_power[0])) /
                         (volts[-1]-volts[0]))
        # FIXME: to be removed
        #self.volts = np.array([volt for volt in sorted(self.data.iterkeys())])
        #self.freqs_in_mhz = np.array([self.freq_in_mhz[volt] for volt in self.volts])
        #self.freqs_in_ghz = np.array([self.freq_in_ghz[volt] for volt in self.volts])
        
        #self._model_in_mhz = itpl.InterpolatedUnivariateSpline(self.volts,self.freqs_in_mhz,k=3)
        #self._model_in_ghz = itpl.InterpolatedUnivariateSpline(self.volts,self.freqs_in_ghz,k=3)

        # FIXME: to be removed
        self.volts = np.array(inv_v)
        self.freqs = np.array(inv_f)
        
    #def get_freqs_in_mhz(self, volts):
        #return self._model_in_mhz(volts)
    
    #def get_freqs_in_ghz(self, volts):
        #return self._model_in_ghz(volts)
    
    def get_freqs(self, volts):
        """"
        volts must be a numpy.ndarray, otherwise, use get_freq
        """
        if isinstance(volts,np.ndarray):
            # use relative voltage
            #return self.model(volts*self.v_translator)*self.f_translator        
            # use over-drive voltage
            return self.model(volts-self.v_translator)*self.f_translator        
        else:
            print 'volts must be a numpy ndarray'
            return 0

    def get_freq(self, volt):
        """""
        volt must be a float/int, otherwise, use get_freqs
        """
        if (isinstance(volt,float) or 
            isinstance(volt,int)):
            # input is a single number
            freq_np = self.model(volt-self.v_translator)*self.f_translator
            return freq_np[0]

        else:
            print 'volts can be a number of float/int.'
            return 0

    def config(self, vth, v0, f0):
        """"
        Configurate model with new set of parameters (vth, v0, f0)
          vth: threshold voltage
          v0 : nominal voltage
          f0 : frequency under nominal voltage
        """
        self.v_translator = vth - self.inv_vth

        v = v0 - self.v_translator
        f = self.model(v)

        self.f_translator = f0/f

if __name__ == '__main__':
    import matplotlib.pyplot as plt
    scaler = FreqScale(techbase.vth, 1, 4.2)
    print scaler.sp_slope
    
    #volts_orig = scaler.volts
    #freqs_orig = scaler.freqs

    
    #volts = np.linspace(0.2,3,100)
    ##freqs = scaler.get_freqs_in_mhz(volts)
    #freqs = scaler.get_freqs(volts)
    
    #fig = plt.figure()
    #axes = fig.add_subplot(111)
    #axes.set_xlabel('Supplying Voltage(V)')
    #axes.set_ylabel('Frequency (MHz)')
    
    #axes.plot(volts,freqs, volts_orig, freqs_orig, 'rD')
    ##axes.set_xlim(0,1.4)
    #axes.set_yscale('log')
    #axes.legend(axes.lines, ['Fitting','simulated'], loc='upper left')
    #axes.grid(True)
    
    #fig.savefig('freq_volt.pdf')

        

