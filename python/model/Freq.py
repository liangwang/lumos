#!/usr/bin/env python

import numpy as np
import scipy.interpolate as itpl

class FreqScale:
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
    
    def __init__(self):
        self.volts = np.array([volt for volt in sorted(self.data.iterkeys())])
        self.freqs_in_mhz = np.array([self.freq_in_mhz[volt] for volt in self.volts])
        self.freqs_in_ghz = np.array([self.freq_in_ghz[volt] for volt in self.volts])
        
        self._model_in_mhz = itpl.InterpolatedUnivariateSpline(self.volts,self.freqs_in_mhz,k=3)
        self._model_in_ghz = itpl.InterpolatedUnivariateSpline(self.volts,self.freqs_in_ghz,k=3)
        
    def get_freqs_in_mhz(self, volts):
        return self._model_in_mhz(volts)
    
    def get_freqs_in_ghz(self, volts):
        return self._model_in_ghz(volts)
        
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

        

