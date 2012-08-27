#!/usr/bin/env python

import numpy as np
import math
import XLSParser
from scipy.interpolate import InterpolatedUnivariateSpline as IUSpline
import scipy.interpolate
from os.path import join as joinpath
from data import reader
import logging
import cPickle as pickle
import conf.misc
SIM_RESULT_DIR = joinpath(conf.misc.homedir, 'data')

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
            logging.error('volts must be a numpy ndarray')
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
            loggin.error('volts can be a number of float/int.')
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
        #self.model = IUSpline(vdd_to_interp, freq_to_interp)
        #f = self.model(v0)[0]


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
            logging.error('volts must be a numpy ndarray')
            return 0

    def get_freq(self, volt):
        """""
        volt must be a float/int, otherwise, use get_freqs
        """
        if (isinstance(volt,float) or 
            isinstance(volt,int)):
            # input is a single number
            freq_np = self.model(volt)*self.f_translator
            #freq_np = self.model(volt)[0]*self.f_translator
            return float(freq_np)

        else:
            logging.error('volts can be a number of float/int.')
            return 0

    def config(self, v0, f0):
        """"
        Configurate model with new set of parameters (vt, v0, f0)
          v0 : nominal voltage
          f0 : frequency under nominal voltage
        """
        f = self.model(v0)

        self.f_translator = f0/f

simdata= dict()
for ckt in ('adder',):
    simdata[ckt]=dict()
    for ttype in ('HKMGS',):
        simdata[ckt][ttype]=dict()
        for tech in (45, 32, 22, 16):
            simdata[ckt][ttype][tech] = dict()
            dfn = joinpath(SIM_RESULT_DIR, '%s_%s_%d.pypkl' % (ckt, ttype, tech))
            with open(dfn, 'rb') as f:
                freq_dict = pickle.load(f)
                sp_slope = pickle.load(f)
            simdata[ckt][ttype][tech]['freq_dict'] = freq_dict
            simdata[ckt][ttype][tech]['sp_slope'] = sp_slope

class PTMScale2:
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

        self.freq_dict = simdata[ckt][ttype][tech]['freq_dict']
        f = self.freq_dict[int(v0*1000)]

        # use relative frequency
        self.f_translator = f0/f

        self.sp_slope = simdata[ckt][ttype][tech]['sp_slope']


    def get_freq(self, volt):
        """""
        volt must be a float/int, otherwise, use get_freqs
        """
        return self.freq_dict[int(volt*1000)]*self.f_translator

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
            logging.error('volts must be a numpy ndarray')
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
            logging.error('volts can be a number of float/int.')
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

    def __init__(self, ckt, ttype, tech, v0, f0, pen_adjust=1.0, sigma_level=3):
        
        dset = reader.readNormData(ckt, ttype, tech)
        #self.model = IUSpline(dset['vdd'], dset['freq'], k=3)
        vdd_to_interp = dset['vdd'][::-1]
        freq_to_interp= dset['freq'][::-1]
        #self.model = IUSpline(vdd_to_interp, freq_to_interp)
        #f = self.model(v0)[0]
        self.model = scipy.interpolate.interp1d(vdd_to_interp, freq_to_interp, kind='cubic')
        f = self.model(v0)
        self.f_translator = f0/f


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
        if sigma_level == 2:
            freq_tointerp = mcdset['freq_2sigma'][::-1]
        elif sigma_level == 1:
            freq_tointerp = mcdset['freq_sigma'][::-1]
        else:
            freq_tointerp = mcdset['freq_3sigma'][::-1]

        self.mcmodel = scipy.interpolate.interp1d(vdd_tointerp, freq_tointerp, kind='cubic')
        #self.mcmodel = IUSpline(vdd_tointerp, freq_tointerp)
        #self.freq_down = self.mcmodel(v0)/self.model(v0)

        #f = self.mcmodel(v0)
        #self.f_translator = f0*self.freq_down/f

        #st_power = mcdset['sp_min'].tolist()
        st_power = dset['sp'].tolist()
        volts = mcdset['vdd'].tolist()
        self.sp_slope = ((math.log10(st_power[-1])-math.log10(st_power[0])) /
                         (volts[-1]-volts[0]))

        self.pen_adjust = pen_adjust

        #dp_nom = dset['dp'][::-1]
        #model = scipy.interpolate.interp1d(vdd_to_interp, dp_nom, kind='cubic')
        #dp_mc = mcdset['dp_min'][::-1]
        #mcmodel = scipy.interpolate.interp1d(vdd_to_interp, dp_mc, kind='cubic')
        #self.dp_down = mcmodel(v0) / model(v0)

        #sp_nom = dset['sp'][::-1]
        #model = scipy.interpolate.interp1d(vdd_to_interp, sp_nom, kind='cubic')
        #sp_mc = mcdset['sp_min'][::-1]
        #mcmodel = scipy.interpolate.interp1d(vdd_to_interp, sp_mc, kind='cubic')
        #self.sp_down = mcmodel(v0) / model(v0)

        ## FIXME: to be removed
        #self.volts = dset['vdd']
        #self.freqs = dset['freq']

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
            logging.error('volts must be a numpy ndarray')
            return 0

    def get_freq(self, volt):
        """""
        volt must be a float/int, otherwise, use get_freqs
        """
        if (isinstance(volt,float) or 
            isinstance(volt,int)):
            # input is a single number
            freq_np = self.model(volt)*self.f_translator
            #freq_np = self.model(volt)[0]*self.f_translator
            return float(freq_np)

        else:
            logging.error('volts can be a number of float/int.')
            return 0
        
    def get_penalties(self, volts):
        """"
        volts must be a numpy.ndarray, otherwise, use get_penalty
        """
        if isinstance(volts,np.ndarray):
            # use relative voltage
            #return self.model(volts*self.v_translator)*self.f_translator        
            # use over-drive voltage
            freq_mc = self.mcmodel(volts)
            freq_nom = self.model(volts)
            freq_adjust = freq_mc+(freq_nom-freq_mc)*self.pen_adjust
            return freq_adjust/freq_nom
        else:
            logging.error('volts must be a numpy ndarray')
            return 0

    def get_penalty(self, volt):
        """""
        volt must be a float/int, otherwise, use get_panelties
        """
        if (isinstance(volt,float) or 
            isinstance(volt,int)):
            # input is a single number
            freq_mc = self.mcmodel(volt)
            freq_nom = self.model(volt)
            freq_adjust = freq_nom-(freq_nom-freq_mc)*self.pen_adjust
            return freq_adjust/freq_nom
        else:
            logging.error('volts can be a number of float/int.')
            return 0

    def config(self, v0, f0, pen_adjust=None):
        """"
        Configurate model with new set of parameters (vt, v0, f0)
          v0 : nominal voltage
          f0 : frequency under nominal voltage
        """
        f = self.model(v0)

        self.f_translator = f0/f

        if pen_adjust:
            self.pen_adjust = pen_adjust

if __name__ == '__main__':
    #import matplotlib.pyplot as plt
    #scaler = FreqScale2('inv', 'LP', 45, 1, 4.2)
    #scaler = FreqScale(0.5, 1, 4.2)
    
    #volts_orig = scaler.volts
    #freqs_orig = scaler.freqs/1e9

    
    #volts = np.linspace(0.3,1.1,10000)
    #freqs = scaler.get_freqs(volts)

    #freqs = []
    #for volt in volts:
        #freqs.append(scaler.get_freq(volt))




    #print volts
    #freqs = scaler.get_freqs_in_mhz(volts)
    #print freqs
    
    #fig = plt.figure()
    #axes = fig.add_subplot(111)
    #axes.set_xlabel('Supplying Voltage(V)')
    #axes.set_ylabel('Frequency (MHz)')
    
    #axes.plot(volts,freqs, volts_orig, freqs_orig, 'rD')
    ##axes.set_xlim(0,1.4)
    #axes.set_yscale('log')
    #axes.legnd(axes.lines, ['Fitting','simulated'], loc='upper left')
    #axes.grid(True)
    
    #fig.savefig('freq_volt.pdf')
    pass
