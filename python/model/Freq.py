#!/usr/bin/env python

import numpy as np
import scipy.interpolate as itpl
from Tech import Base as TechBase

class FreqScale:
    inv_mhz = {   1: 22306.73,
                0.9: 19128.17,
                0.8: 15459.06,
                0.7: 10686.1,
                0.6: 5270.448,
                0.5: 1345.931,
                0.4: 158.1074,
               0.35: 44.96318,
                0.3: 12.78681,
               0.25: 3.35367,
                0.2: 0.879594}
    inv_v = [v for v in sorted(inv_mhz.iterkeys())]
    inv_f = [inv_mhz[v] for v in inv_v]
    model = itpl.InterpolatedUnivariateSpline(np.array(inv_v),
                                              np.array(inv_f),
                                              k=3)
    
    data = {1: 4200,
            0.9: 3601.53,
            0.8: 2910.69,
            0.7: 2012.02,
            0.6: 992.341,
            0.5: 253.417,
            0.4: 29.7691,
            0.35:8.46594,
            0.3: 2.40755,
            0.25:0.63145,
            0.2: 0.16561}
    
    freq_in_ghz = dict([(v, data[v]/1000) for v in sorted(data.iterkeys())])
    freq_in_mhz = dict([(v, data[v]) for v in sorted(data.iterkeys())])
    
    def __init__(self, vth, vnorm, fnorm):
        self.v_translator = TechBase.vth / vth
        
        v = vnorm * self.v_translator
        f = self.model(v)
        self.f_translator = fnorm/f
        
        # FIXME: to be removed
        self.volts = np.array([volt for volt in sorted(self.data.iterkeys())])
        self.freqs_in_mhz = np.array([self.freq_in_mhz[volt] for volt in self.volts])
        self.freqs_in_ghz = np.array([self.freq_in_ghz[volt] for volt in self.volts])
        
        self._model_in_mhz = itpl.InterpolatedUnivariateSpline(self.volts,self.freqs_in_mhz,k=3)
        self._model_in_ghz = itpl.InterpolatedUnivariateSpline(self.volts,self.freqs_in_ghz,k=3)
        
    def get_freqs_in_mhz(self, volts):
        return self._model_in_mhz(volts)
    
    def get_freqs_in_ghz(self, volts):
        return self._model_in_ghz(volts)
    
    def get_freqs(self, volts):
        return self.model(volts*self.v_translator)*self.f_translator        

if __name__ == '__main__':
    import matplotlib.pyplot as plt
    scaler = FreqScale()
    
    volts_orig = scaler.volts
    freqs_orig = scaler.freqs
    
    volts = np.linspace(0.2,1,81)
    freqs = scaler.get_freqs_in_mhz(volts)
    
    fig = plt.figure()
    axes = fig.add_subplot(111)
    axes.set_xlabel('Supplying Voltage(V)')
    axes.set_ylabel('Frequency (MHz)')
    
    axes.plot(volts,freqs, volts_orig, freqs_orig, 'rD')
    axes.set_xlim(0,1.1)
    axes.set_yscale('log')
    axes.legend(axes.lines, ['Fitting','simulated'], loc='upper left')
    axes.grid(True)
    
    fig.savefig('freq_volt.pdf')

        

