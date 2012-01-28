#!/usr/bin/env python

import numpy as np
import math
import XLSParser
from scipy.interpolate import InterpolatedUnivariateSpline as IUSpline
import scipy.interpolate
from os.path import join as joinpath
from data import reader

class ProjectionScale:
    __DATA_FILE=joinpath('data','inv_45.xls')
    __DATA_OLD=joinpath('data','inv_45_sudhanshu.xls')

    inv_vt = 0.5
    
    def __init__(self, vt, v0, f0):
        
        p = XLSParser.XLSParser()
        p.parse(self.__DATA_FILE)
        dict_freq = p.get_freqs()
        inv_v = [v for v in sorted(dict_freq.iterkeys())]
        inv_f = [dict_freq[v] for v in inv_v]
        self.model = IUSpline(np.array(inv_v), np.array(inv_f), k=3)


        # FIXME: confirm vt for this technology
        # FIXME: use over-drive voltage(v-vt) other than relative (v/vt)

        # use relative voltage
        #self.v_translator = inv_vt / vt
        #v = v0 * self.v_translator
        # use over-drive voltage
        #   v = v_inv + v_translator
        self.v_translator = vt - self.inv_vt
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
        self.volts = np.array(inv_v)
        self.freqs = np.array(inv_f)
        
    
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

    def config(self, vt, v0, f0):
        """"
        Configurate model with new set of parameters (vt, v0, f0)
          vt: threshold voltage
          v0 : nominal voltage
          f0 : frequency under nominal voltage
        """
        self.v_translator = vt - self.inv_vt

        v = v0 - self.v_translator
        f = self.model(v)

        self.f_translator = f0/f

class PTMScale:
    """ Voltage-to-Frequency scaling based on circuits simulation with PTM
    """

    def __init__(self, ckt, ttype, tech, v0, f0):
        """
        ckt: the name of simulated circuit
        ttype: the technology type, HKMGS and LP
        tech: technology node, such as 45, 32, 22, 16
        v0: nominal vdd
        f0: frequency under nomial vdd
        """
        
        dset = reader.readNormData(ckt, ttype, tech)
        vdd_to_interp = dset['vdd'][::-1]
        freq_to_interp= dset['freq'][::-1]
        self.model = scipy.interpolate.interp1d(vdd_to_interp, freq_to_interp, kind='cubic')
        
        f = self.model(v0)

        # use relative frequency
        #   f = f_inv * f_translator
        self.f_translator = f0/f
        
        st_power = dset['sp'].tolist()
        volts = dset['vdd'].tolist()
        self.sp_slope = ((math.log10(st_power[-1])-math.log10(st_power[0])) /
                         (volts[-1]-volts[0]))

        
    def get_freqs(self, volts):
        """"
        volts must be a numpy.ndarray, otherwise, use get_freq
        """
        if isinstance(volts,np.ndarray):
            # use relative voltage
            #return self.model(volts*self.v_translator)*self.f_translator        
            # use over-drive voltage
            return self.model(volts)*self.f_translator        
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
            freq_np = self.model(volt)*self.f_translator
            return float(freq_np)

        else:
            print 'volts can be a number of float/int.'
            return 0

    def config(self, v0, f0):
        """"
        Configurate model with new set of parameters (vt, v0, f0)
          v0 : nominal voltage
          f0 : frequency under nominal voltage
        """
        f = self.model(v0)

        self.f_translator = f0/f

class FreqScale2:

    def __init__(self, ckt, ttype, tech, v0, f0):
        
        dset = reader.readNormData(ckt, ttype, tech)
        #self.model = IUSpline(dset['vdd'], dset['freq'], k=3)
        vdd_to_interp = dset['vdd'][::-1]
        freq_to_interp= dset['freq'][::-1]
        #self.model = IUSpline(vdd_to_interp, freq_to_interp)
        self.model = scipy.interpolate.interp1d(vdd_to_interp, freq_to_interp, kind='cubic')


        # FIXME: confirm vt for this technology
        # FIXME: use over-drive voltage(v-vt) other than relative (v/vt)

        # use relative voltage
        #self.v_translator = inv_vt / vt
        #v = v0 * self.v_translator
        # use over-drive voltage
        #   v = v_inv + v_translator
        
        f = self.model(v0)

        # use relative frequency
        #   f = f_inv * f_translator
        self.f_translator = f0/f
        
        st_power = dset['sp'].tolist()
        volts = dset['vdd'].tolist()
        self.sp_slope = ((math.log10(st_power[-1])-math.log10(st_power[0])) /
                         (volts[-1]-volts[0]))

        # FIXME: to be removed
        self.volts = dset['vdd']
        self.freqs = dset['freq']
        
    def get_freqs(self, volts):
        """"
        volts must be a numpy.ndarray, otherwise, use get_freq
        """
        if isinstance(volts,np.ndarray):
            # use relative voltage
            #return self.model(volts*self.v_translator)*self.f_translator        
            # use over-drive voltage
            return self.model(volts)*self.f_translator        
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
            freq_np = self.model(volt)*self.f_translator
            return freq_np

        else:
            print 'volts can be a number of float/int.'
            return 0

    def config(self, v0, f0):
        """"
        Configurate model with new set of parameters (vt, v0, f0)
          v0 : nominal voltage
          f0 : frequency under nominal voltage
        """
        f = self.model(v0)

        self.f_translator = f0/f

class PTMScaleMC:

    def __init__(self, ckt, ttype, tech, v0, f0):
        
        dset = reader.readNormData(ckt, ttype, tech)
        #self.model = IUSpline(dset['vdd'], dset['freq'], k=3)
        vdd_to_interp = dset['vdd'][::-1]
        freq_to_interp= dset['freq'][::-1]
        #self.model = IUSpline(vdd_to_interp, freq_to_interp)
        self.model = scipy.interpolate.interp1d(vdd_to_interp, freq_to_interp, kind='cubic')


        # FIXME: confirm vt for this technology
        # FIXME: use over-drive voltage(v-vt) other than relative (v/vt)

        # use relative voltage
        #self.v_translator = inv_vt / vt
        #v = v0 * self.v_translator
        # use over-drive voltage
        #   v = v_inv + v_translator
        

        # use relative frequency
        #   f = f_inv * f_translator
        

        mcdset = reader.readMCData(ckt, ttype, tech)
        vdd_tointerp = mcdset['vdd'][::-1]
        freq_tointerp = mcdset['freq_min'][::-1]
        self.mcmodel = scipy.interpolate.interp1d(vdd_tointerp, freq_tointerp, kind='cubic')
        self.freq_down = self.mcmodel(v0)/self.model(v0)

        f = self.mcmodel(v0)
        self.f_translator = f0*self.freq_down/f

        st_power = mcdset['sp_min'].tolist()
        volts = mcdset['vdd'].tolist()
        self.sp_slope = ((math.log10(st_power[-1])-math.log10(st_power[0])) /
                         (volts[-1]-volts[0]))

        dp_nom = dset['dp'][::-1]
        model = scipy.interpolate.interp1d(vdd_to_interp, dp_nom, kind='cubic')
        dp_mc = mcdset['dp_min'][::-1]
        mcmodel = scipy.interpolate.interp1d(vdd_to_interp, dp_mc, kind='cubic')
        self.dp_down = mcmodel(v0) / model(v0)

        sp_nom = dset['sp'][::-1]
        model = scipy.interpolate.interp1d(vdd_to_interp, sp_nom, kind='cubic')
        sp_mc = mcdset['sp_min'][::-1]
        mcmodel = scipy.interpolate.interp1d(vdd_to_interp, sp_mc, kind='cubic')
        self.sp_down = mcmodel(v0) / model(v0)

        # FIXME: to be removed
        self.volts = dset['vdd']
        self.freqs = dset['freq']
        
    def get_freqs(self, volts):
        """"
        volts must be a numpy.ndarray, otherwise, use get_freq
        """
        if isinstance(volts,np.ndarray):
            # use relative voltage
            #return self.model(volts*self.v_translator)*self.f_translator        
            # use over-drive voltage
            return self.mcmodel(volts)*self.f_translator        
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
            freq_np = self.mcmodel(volt)*self.f_translator
            return freq_np

        else:
            print 'volts can be a number of float/int.'
            return 0

    #def config(self, v0, f0):
        #""""
        #Configurate model with new set of parameters (vt, v0, f0)
          #v0 : nominal voltage
          #f0 : frequency under nominal voltage
        #"""
        #f = self.model(v0)

        #self.f_translator = f0/f

if __name__ == '__main__':
    import matplotlib.pyplot as plt
    scaler = FreqScale2('inv', 'LP', 45, 1, 4.2)
    #scaler = FreqScale(0.5, 1, 4.2)
    
    volts_orig = scaler.volts
    freqs_orig = scaler.freqs/1e9

    
    volts = np.linspace(0.3,1.1,100)
    print volts
    #freqs = scaler.get_freqs_in_mhz(volts)
    freqs = scaler.get_freqs(volts)
    print freqs
    
    fig = plt.figure()
    axes = fig.add_subplot(111)
    axes.set_xlabel('Supplying Voltage(V)')
    axes.set_ylabel('Frequency (MHz)')
    
    axes.plot(volts,freqs, volts_orig, freqs_orig, 'rD')
    #axes.set_xlim(0,1.4)
    axes.set_yscale('log')
    axes.legend(axes.lines, ['Fitting','simulated'], loc='upper left')
    axes.grid(True)
    
    fig.savefig('freq_volt.pdf')

        

