#!/usr/bin/env python

import numpy as np
import math
import csv
#import XLSParser
from scipy.interpolate import InterpolatedUnivariateSpline as IUSpline
import scipy.interpolate
import os
from os.path import join as joinpath
import logging
import cPickle as pickle
import lumos.settings as settings
SIM_RESULT_DIR = joinpath(settings.LUMOS_HOME, 'data', 'cktsim')

# class ProjectionScale:
#     """
#     Old V-f scaling using inverter chains at commercial 45nm technology (obsolete)
#     """
#     __DATA_FILE=joinpath(SIM_RESULT_DIR, 'data','inv_45.xls')
#     __DATA_OLD=joinpath(SIM_RESULT_DIR, 'data','inv_45_sudhanshu.xls')

#     inv_vt = 0.5

#     def __init__(self, vt, v0, f0):

#         p = XLSParser.XLSParser()
#         p.parse(self.__DATA_FILE)
#         dict_freq = p.get_freqs()
#         inv_v = [v for v in sorted(dict_freq.iterkeys())]
#         inv_f = [dict_freq[v] for v in inv_v]
#         self.model = IUSpline(np.array(inv_v), np.array(inv_f), k=3)


#         # FIXME: confirm vt for this technology
#         # FIXME: use over-drive voltage(v-vt) other than relative (v/vt)

#         # use relative voltage
#         #self.v_translator = inv_vt / vt
#         #v = v0 * self.v_translator
#         # use over-drive voltage
#         #   v = v_inv + v_translator
#         self.v_translator = vt - self.inv_vt
#         v = v0 - self.v_translator

#         f = self.model(v)

#         # use relative frequency
#         #   f = f_inv * f_translator
#         self.f_translator = f0/f

#         sp=p.get_static_power()
#         volts = sorted(sp.iterkeys())
#         st_power = [(sp[v]) for v in volts]
#         self.sp_slope = ((math.log10(st_power[-1])-math.log10(st_power[0])) /
#                          (volts[-1]-volts[0]))

#         # FIXME: to be removed
#         self.volts = np.array(inv_v)
#         self.freqs = np.array(inv_f)


#     def get_freqs(self, volts):
#         """"
#         volts must be a numpy.ndarray, otherwise, use get_freq
#         """
#         if isinstance(volts,np.ndarray):
#             # use relative voltage
#             #return self.model(volts*self.v_translator)*self.f_translator
#             # use over-drive voltage
#             return self.model(volts-self.v_translator)*self.f_translator
#         else:
#             logging.error('volts must be a numpy ndarray')
#             return 0

#     def get_freq(self, volt):
#         """""
#         volt must be a float/int, otherwise, use get_freqs
#         """
#         if (isinstance(volt,float) or
#             isinstance(volt,int)):
#             # input is a single number
#             freq_np = self.model(volt-self.v_translator)*self.f_translator
#             return freq_np[0]

#         else:
#             loggin.error('volts can be a number of float/int.')
#             return 0

#     def config(self, vt, v0, f0):
#         """"
#         Configurate model with new set of parameters (vt, v0, f0)
#           vt: threshold voltage
#           v0 : nominal voltage
#           f0 : frequency under nominal voltage
#         """
#         self.v_translator = vt - self.inv_vt

#         v = v0 - self.v_translator
#         f = self.model(v)

#         self.f_translator = f0/f

# class PTMScale:
#     """
#     Voltage-to-Frequency scaling based on circuits simulation with PTM (obsolete)
#     """

#     def __init__(self, ckt, ttype, tech, v0, f0):
#         """
#         ckt: the name of simulated circuit
#         ttype: the technology type, HKMGS and LP
#         tech: technology node, such as 45, 32, 22, 16
#         v0: nominal vdd
#         f0: frequency under nomial vdd
#         """

#         dset = reader.readNormData(ckt, ttype, tech)
#         vdd_to_interp = dset['vdd'][::-1]
#         freq_to_interp= dset['freq'][::-1]
#         self.model = scipy.interpolate.interp1d(vdd_to_interp, freq_to_interp, kind='cubic')
#         f = self.model(v0)
#         #self.model = IUSpline(vdd_to_interp, freq_to_interp)
#         #f = self.model(v0)[0]


#         # use relative frequency
#         #   f = f_inv * f_translator
#         self.f_translator = f0/f

#         st_power = dset['sp'].tolist()
#         volts = dset['vdd'].tolist()
#         self.sp_slope = ((math.log10(st_power[-1])-math.log10(st_power[0])) /
#                          (volts[-1]-volts[0]))

#     def get_freqs(self, volts):
#         """"
#         volts must be a numpy.ndarray, otherwise, use get_freq
#         """
#         if isinstance(volts,np.ndarray):
#             # use relative voltage
#             #return self.model(volts*self.v_translator)*self.f_translator
#             # use over-drive voltage
#             return self.model(volts)*self.f_translator
#         else:
#             logging.error('volts must be a numpy ndarray')
#             return 0

#     def get_freq(self, volt):
#         """""
#         volt must be a float/int, otherwise, use get_freqs
#         """
#         if (isinstance(volt,float) or
#             isinstance(volt,int)):
#             # input is a single number
#             freq_np = self.model(volt)*self.f_translator
#             #freq_np = self.model(volt)[0]*self.f_translator
#             return float(freq_np)

#         else:
#             logging.error('volts can be a number of float/int.')
#             return 0

#     def config(self, v0, f0):
#         """"
#         Configurate model with new set of parameters (vt, v0, f0)
#           v0 : nominal voltage
#           f0 : frequency under nominal voltage
#         """
#         f = self.model(v0)

#         self.f_translator = f0/f


# Preprocessing circuit simulation data
def gen_interp(ckt, ttype, tech):
    ifn = joinpath(SIM_RESULT_DIR,
                   ckt, 'NonVar', '%s_%s_%d.data' % (ckt, ttype, tech))
    ifn_mtime = os.path.getmtime(ifn)

    ofn = joinpath(SIM_RESULT_DIR,
                   ckt, 'NonVar', '%s_%s_%d.pypkl' % (ckt, ttype, tech))

    try:
        ofn_mtime = os.path.getmtime(ofn)
    except OSError:
        ofn_mtime = 0

    if ofn_mtime > ifn_mtime:
        return

    with open(ifn, 'rb') as f:
        freader = csv.reader(f, delimiter='\t')

        vdd_list = []
        tp_list = []
        dp_list = []
        sp_list = []
        for row in freader:
            vdd_list.append(float(row[0]))
            tp_list.append(float(row[1]))
            dp_list.append(float(row[2]))
            sp_list.append(float(row[3]))

    vdd = np.array(vdd_list)

    dp = np.array(dp_list)

    sp = np.array(sp_list)

    delay = np.array(tp_list)
    freq = np.reciprocal(delay)

    vdd_to_interp = vdd[::-1]
    freq_to_interp = freq[::-1]
    model = scipy.interpolate.interp1d(vdd_to_interp, freq_to_interp, kind='cubic')
    vmin = int(min(vdd_list) * 1000)
    vmax = int(max(vdd_list) * 1000)
    samples = vmax-vmin + 1
    vdd_mv_np = np.linspace(vmin, vmax, num=samples)
    vdd_np = np.array([ (float(v)/1000) for v in vdd_mv_np])
    freq_np = model(vdd_np)
    freq_dict = dict( (v, f) for (v,f) in zip(vdd_mv_np, freq_np) )
    sp_slopes = ((math.log10(sp_list[-1])-math.log10(sp_list[0])) / (vdd_list[-1]-vdd_list[0]))

    with open(ofn, 'wb') as f:
        pickle.dump(freq_dict, f)
        pickle.dump(sp_slopes, f)

def preproc_sim_data():
    for ckt in ('adder32', 'adder16', 'adder8', 'adder4', 'inv', 'inv50'):
        for ttype in ('HKMGS', 'LP'):
            for tech in (45, 32, 22, 16):
                gen_interp(ckt, ttype, tech)

simdata= dict()
ckt=settings.LUMOS_SIM_CIRCUIT
simdata[ckt]=dict()
for ttype in ('HKMGS','LP'):
    simdata[ckt][ttype]=dict()
    for tech in (45, 32, 22, 16):
        simdata[ckt][ttype][tech] = dict()
        dfn = joinpath(SIM_RESULT_DIR,
                       ckt, 'NonVar', '%s_%s_%d.pypkl' % (ckt, ttype, tech))

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

    def get_freqs(self, volts):
        """"
        volts must be a numpy.ndarray, otherwise, use get_freq
        """
        try:
            freqs = np.array([self.freq_dict[int(volt*1000)]*self.f_translator
                     for volt in volts])
        except TypeError:
            logging.error('volts must be a numpy ndarray')
            return 0

        return freqs


    def config(self, v0, f0):
        """"
        Configurate model with new set of parameters (vt, v0, f0)
          v0 : nominal voltage
          f0 : frequency under nominal voltage
        """
        f = self.model(v0)

        self.f_translator = f0/f

# class FreqScale2:
#     """
#     obsolete scaling mechanism
#     """
#     def __init__(self, ckt, ttype, tech, v0, f0):

#         dset = reader.readNormData(ckt, ttype, tech)
#         #self.model = IUSpline(dset['vdd'], dset['freq'], k=3)
#         vdd_to_interp = dset['vdd'][::-1]
#         freq_to_interp= dset['freq'][::-1]
#         #self.model = IUSpline(vdd_to_interp, freq_to_interp)
#         self.model = scipy.interpolate.interp1d(vdd_to_interp, freq_to_interp, kind='cubic')


#         # FIXME: confirm vt for this technology
#         # FIXME: use over-drive voltage(v-vt) other than relative (v/vt)

#         # use relative voltage
#         #self.v_translator = inv_vt / vt
#         #v = v0 * self.v_translator
#         # use over-drive voltage
#         #   v = v_inv + v_translator

#         f = self.model(v0)

#         # use relative frequency
#         #   f = f_inv * f_translator
#         self.f_translator = f0/f

#         st_power = dset['sp'].tolist()
#         volts = dset['vdd'].tolist()
#         self.sp_slope = ((math.log10(st_power[-1])-math.log10(st_power[0])) /
#                          (volts[-1]-volts[0]))

#         # FIXME: to be removed
#         self.volts = dset['vdd']
#         self.freqs = dset['freq']

#     def get_freqs(self, volts):
#         """"
#         volts must be a numpy.ndarray, otherwise, use get_freq
#         """
#         if isinstance(volts,np.ndarray):
#             # use relative voltage
#             #return self.model(volts*self.v_translator)*self.f_translator
#             # use over-drive voltage
#             return self.model(volts)*self.f_translator
#         else:
#             logging.error('volts must be a numpy ndarray')
#             return 0

#     def get_freq(self, volt):
#         """""
#         volt must be a float/int, otherwise, use get_freqs
#         """
#         if (isinstance(volt,float) or
#             isinstance(volt,int)):
#             # input is a single number
#             freq_np = self.model(volt)*self.f_translator
#             return freq_np

#         else:
#             logging.error('volts can be a number of float/int.')
#             return 0

#     def config(self, v0, f0):
#         """"
#         Configurate model with new set of parameters (vt, v0, f0)
#           v0 : nominal voltage
#           f0 : frequency under nominal voltage
#         """
#         f = self.model(v0)

#         self.f_translator = f0/f


def readNormData(ckt, ttype, tech):
    """
    ckt: 'inv', 'adder'
    ttype: 'HKMGS', 'LP'
    tech: 45, 32, 22, 16
    """

    ifn = joinpath(SIM_RESULT_DIR, ckt, 'NonVar',
                       '%s_%s_%d.data' % (ckt, ttype, tech))

    with open(ifn, 'rb') as f:
        freader = csv.reader(f, delimiter='\t')

        vdd_raw = []
        tp_raw = []
        dp_raw = []
        sp_raw = []

        for row in freader:
            vdd_raw.append(float(row[0]))
            tp_raw.append(float(row[1]))
            dp_raw.append(float(row[2]))
            sp_raw.append(float(row[3]))


    vdd = np.array(vdd_raw)
    dp = np.array(dp_raw)
    sp = np.array(sp_raw)
    delay = np.array(tp_raw)
    freq = np.reciprocal(delay)

    return {'vdd':vdd,'freq':freq,'dp':dp,'sp':sp}

def readMCData(ckt, ttype, tech, mctype='ProcessAndMismatch'):
    ifn = joinpath(SIM_RESULT_DIR, ckt, mctype,
                       '%s_%s_%d.mcdata' % (ckt, ttype, tech))

    with open(ifn, 'rb') as f:
        freader = csv.reader(f, delimiter='\t')

        vdd = []
        freqs_3sigma = []
        freqs_2sigma = []
        freqs_sigma = []
        freqs_min = []
        freqs_mean = []

        for row in freader:
            vdd.append(float(row[0]))
            freqs_3sigma.append(float(row[1]))
            freqs_min.append(float(row[2]))
            freqs_mean.append(float(row[3]))
            freqs_2sigma.append(float(row[4]))
            freqs_sigma.append(float(row[5]))

    return {'vdd':np.array(vdd),
            'freq_3sigma': np.array(freqs_3sigma),
            'freq_2sigma': np.array(freqs_2sigma),
            'freq_sigma': np.array(freqs_sigma),
            'freqs_mean': np.array(freqs_mean),
            'freqs_min': np.array(freqs_min),}


class PTMScaleMC:
    """
    scaling with variation from Monte-Carlo simulation
    """
    def __init__(self, ckt, ttype, tech, v0, f0, pen_adjust=1.0, sigma_level=3):

        dset = readNormData(ckt, ttype, tech)
        vdd_to_interp = dset['vdd'][::-1]
        freq_to_interp= dset['freq'][::-1]
        self.model = scipy.interpolate.interp1d(vdd_to_interp, freq_to_interp, kind='cubic')
        f = self.model(v0)
        self.f_translator = f0/f


        mcdset = readMCData(ckt, ttype, tech)
        vdd_tointerp = mcdset['vdd'][::-1]
        if sigma_level == 2:
            freq_tointerp = mcdset['freq_2sigma'][::-1]
        elif sigma_level == 1:
            freq_tointerp = mcdset['freq_sigma'][::-1]
        else:
            freq_tointerp = mcdset['freq_3sigma'][::-1]

        self.mcmodel = scipy.interpolate.interp1d(vdd_tointerp, freq_tointerp, kind='cubic')

        st_power = dset['sp'].tolist()
        volts = mcdset['vdd'].tolist()
        self.sp_slope = ((math.log10(st_power[-1])-math.log10(st_power[0])) /
                         (volts[-1]-volts[0]))

        self.pen_adjust = pen_adjust


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
    preproc_sim_data()
