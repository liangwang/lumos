#!/usr/bin/env python
"""
This module models conventional cores. Two variants are derived from
an abstract base class AbstractCore, as IOCore and O3Core for an
in-order core and an out-of-order core respectively.
"""

import logging
from tech import Base as techbase, Scale as techscl
from tech import ProjScale as projscl
from tech import LPBase as lpbase, PTMScale as ptmscl
import freq
from freq import PTMScale2 as vfmodel

import lumos.settings as settings
MC_CKT = settings.LUMOS_SIM_CIRCUIT
#TODO: add code to MC_BEST case
MC_BEST = False

# from: http://www.spec.org/cpu2006/results/res2009q3/cpu2006-20090721-08251.html
# SPECfp_rate2006 / 8(cores) / 2 (threads) * (4.2/1.58) (freq scaling factor) * 1.4 ( 1/0.7, tech scaling factor)
#PERF_BASE = 15.92
# adjust to federation
PERF_BASE = 12.92

# from: http://www.spec.org/cpu2006/results/res2010q1/cpu2006-20100215-09685.html
# SPECfp2006 * (3.7/3.3) (freq scaling factor)
O3_PERF_BASE = 28.48

class AbstractCore(object):
    """
    Abstract Core module. Need to be extended to real cores with a
    couple of base line characteristics at nominal voltage and 45nm,
    such as area (``base_area``), frequency (``base_freq``), relative
    performance (``base_perf``), dynamic power (``base_dp``), and static power
    (``base_sp``).

    Attributes:
       tech (num):
          Technology nodes, possible values are 45, 32, 22, 16
       mech (str):
          Scaling mechanism, possible values are 'HKMGS' and 'LP'
       area (num):
          The area of the core, in mm^2.
       dp (num):
          Dynamic power, in Watts (W).
       dp0 (num):
          Dynamic power when the core is at nominal supply voltage and frequency, in Watts (W).
       sp (num):
          Static power, in Watts (W).
       sp0 (num):
          Statci power at nominal voltage, in Watts (W)
       power (num):
          Total power of the core, in Watts (W). It equals to dp+sp.
       vdd (num):
          Supply voltage, in Volts (V).
       vdd0 (num):
          Nominal supply voltage, in Volts (V)
       freq (num):
          Frequency, in GHz.
       f0 (num):
          Frequency at nominal supply voltage, in GHz.
       perf (num):
          Relative performance to the baseline in-order core at 45nm.
       perf0 (num):
          Relatvie performance at nominal supply.
       vt (num):
          Threshold voltage, in Volts (V)
       vsf_min (num):
          The minimum supply voltage factor.
       vsf_max (num):
          The maximum supply voltage factor.
    """

    def __init__(self, mech=None, tech=None, pv=False, pen_adjust=None, sigma_level=None):
        """
        Args:
           mech (str):
              The scaling mechanism, choose from 'HKMGS', 'LP'
           tech (num):
              The technology node, choose from '45','32','22','16'
           pv (bool):
              Boolean flag indicating whether process variation is modeled
           pen_adjust (num):
              Penalty adjustment thanks to variation tolerant techniques.
           sigma_level (num):
              How many sigmas to consider when modeling the variation-induced worst delay
        """

        update = True # A flag for lazy update. The core module only updates its
                      # parameters after all parameters (e.g. mech, tech) have been
                      # set.

        if mech is None:
            update = False
        self._mech = mech

        if tech is None:
            update = False
        self._tech = tech

        self._pv = pv
        if pen_adjust is None:
            self.pen_adjust = 1
        else:
            self.pen_adjust = pen_adjust

        if sigma_level is None:
            self.sigma_level = 3
        else:
            self.sigma_level = sigma_level

        if update:
            self.__update_config()


    def __update_config(self):
        """ Internal function to update value of mech/ctype/tech specific parameters """
        tech = self._tech
        mech = self._mech
        pv = self._pv

        self._perf0 = self.base_perf

        self._area = self.base_area * techscl.area[tech]

        self._fsf = 1
        self._vsf = 1

        if mech == 'ITRS' or mech == 'CONS':
            self._vt = projscl.vt[mech][tech]
            v0 = projscl.vdd[mech][tech]
            f0 = self.base_freq * projscl.freq[mech][tech]
            self._perf0 = self.base_perf * projscl.freq[mech][tech]
            self._bw0 = projscl.freq[mech][tech]
            self._v0 = v0
            self._f0 = f0

            self._dp0 = self.base_dp * projscl.dp[mech][tech]
            self._sp0 = self.base_sp * projscl.sp[mech][tech]

        elif mech == 'HKMGS':
            self._vt = ptmscl.vt[mech][tech]
            v0 = ptmscl.vdd[mech][tech]
            f0 = self.base_freq * ptmscl.freq[mech][tech]
            self._perf0 = self.base_perf * ptmscl.freq[mech][tech]
            self._bw0 = ptmscl.freq[mech][tech]
            self._v0 = v0
            self._f0 = f0

            self._dp0 = self.base_dp * ptmscl.dp[mech][tech]
            self._sp0 = self.base_sp * ptmscl.sp[mech][tech]

        elif mech == 'LP':
            self._vt = ptmscl.vt[mech][tech]
            v0 = ptmscl.vdd[mech][tech]
            f0 = self.base_freq * ptmscl.freq['HKMGS'][tech] * lpbase.freq[tech]
            self._perf0 = self.base_perf * ptmscl.freq['HKMGS'][tech] * lpbase.freq[tech]
            self._bw0 = ptmscl.freq['HKMGS'][tech] * lpbase.freq[tech]
            self._v0 = v0
            self._f0 = f0

            # dynamic power and static power use the same scaling factors
            self._dp0 = self.base_dp * ptmscl.dp['HKMGS'][tech] * lpbase.dp[tech]
            self._sp0 = self.base_sp * ptmscl.sp['HKMGS'][tech] * lpbase.sp[tech]

        if mech == 'ITRS' or mech == 'CONS':

            self._vsf_max = 1.1 / self._v0
            self._vsf_min = 0.3 / self._v0

            if pv:
                self._model = freq.PTMScaleMC(MC_CKT, 'HKMGS', tech, v0, f0, self.pen_adjust, self.sigma_level)
                self.var_penalty = self._model.get_penalty(v0)
            else:
                self._model = vfmodel(MC_CKT, 'HKMGS', tech, self._v0, self._f0)

            self._sp_slope = self._model.sp_slope
        elif mech == 'HKMGS' or mech == 'LP':
            self._vsf_max = 1.1 / self._v0
            self._vsf_min = 0.3 / self._v0

            if pv:
                self._model = freq.PTMScaleMC(MC_CKT, mech, tech, v0, f0, self.pen_adjust, self.sigma_level)
                self.var_penalty = self._model.get_penalty(v0)
            else:
                self._model = vfmodel(MC_CKT, mech, tech, self._v0, self._f0)

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
    def dp0(self):
        """ Get the dynamic power in nominal voltage and frequency """
        return self._dp0

    @property
    def dp(self):
        """ Get the dynamic power """
        #if self._pv:
            #return self._dp0 * self._fsf_nom * self._vsf**2
        #else:
        return self._dp0 * self._fsf * self._vsf ** 2

    @property
    def sp0(self):
        """ Get the static(leakage) power in nominal voltage and frequency """
        return self._sp0

    @property
    def sp(self):
        """ Get the static power """

        #return (self._sp0 * self._vsf *
        return (self._sp0 *
                10 ** (self._v0 * self._vsf * self._sp_slope) /
                10 ** (self._v0 * self._sp_slope))

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
    def perf(self):
        """ Get the performance """
        if self._pv:
            return self._perf0 * self._fsf * self.var_penalty
        else:
            return self._perf0 * self._fsf

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

    def config(self, mech=None, tech=None, pv=None, pen_adjust=None, sigma_level=None):
        """
        Configurate parameters of a core.

        Args:
           mech (str):
              Scaling mechanism, possible values are 'HKMGS' and 'LP'
           tech (num):
              Technology node, in nanometers (nm). Possbile values are 45, 32, 22, 16.
           pv (bool):
              Whether consider process variation.
           pen_adjust (num):
              The variation penalty reduction factor.
           sigma_level (int):
              How many sigmas when consider the worst case variation penalty, default to 3.

        Returns:
           N/A

        """

        update = True

        if mech is not None:
            self._mech = mech
        elif self._mech is None:
            update = False
            #logging.debug('mech is not set, failed to config core')

        #if ctype is not None:
            #self._ctype = ctype
        #elif self._ctype is None:
            #update = False
            ##logging.debug('ctype is not set, failed to config core')

        if tech is not None:
            self._tech = tech
        elif self._tech is None:
            update = False
            #logging.debug('tech is not set, failed to config core')

        if pv is not None:
            self._pv = pv
        elif self._pv is None:
            update = False
            #logging.debug('pv is not set, failed to config core')

        if pen_adjust is not None:
            self.pen_adjust = pen_adjust

        if sigma_level is not None:
            self.sigma_level = sigma_level

        if update:
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
        """
        Change the supply voltage and frequency accordingly by a factor.

        Args:
           vsf (num):
              Scaling factors of the supply voltage.

        Returns:
           N/A

        """
        volt = self._v0 * vsf
        self._vsf = vsf

        scale = self._model
        freq = scale.get_freq(volt)
        self._fsf = freq / self._f0

        if self._pv:
            self.var_penalty = scale.get_penalty(volt)

    def dvfs_by_volt(self, v):
        """
        Change the supply voltage and frquency accordingly by specifying the new voltage.

        Args:
           v (num):
              The new voltage value to be scaled to.

        Returns:
           N/A
        """
        self._vsf = v / self._v0
        scale = self._model
        freq = scale.get_freq(v)
        self._fsf = freq / self._f0

        if self._pv:
            self.var_penalty = scale.get_penalty(v)

    def scale_with_vlist(self, vlist):
        """
        Change the supply voltage in batch by providing a list of voltage values.

        Args:
           vlist (list):
              A list of supply voltage values to be scaled to.

        Returns:
           freq (list):
              The corresponding frequency of each input voltage.
           dp (list):
              The corresponding dynamic power of each input voltage.
           sp (list):
              The corresponding static power of each input voltage
        """
        freqs = self._model.get_freqs(vlist)
        sp = 10 ** (vlist * self._sp_slope) / 10 ** (self._v0 * self._sp_slope) * self._sp0
        #if not self._pv:
        dp = (freqs / self._f0) * (vlist / self._v0) ** 2 * self._dp0
        #else:
            #freqs_nom = self._model_nom.get_freqs(vlist)
            #dp = (freqs_nom/self._f0_nom) * (vlist/self._v0)**2 * self._dp0

        if self._pv:
            var_penalties = self._model.get_penalties(vlist)
            return {'freq': freqs * var_penalties,
                    'dp': dp, 'sp': sp}
        else:
            return {'freq': freqs, 'dp': dp, 'sp': sp}

    def set_base(self, **kwargs):
        """
        Set the base values for frequency, dynamic power, static
        power, and relative performance at nominal supply voltage, as
        well as the area, all at 45nm.

        Args:
           kwargs:
              Named parameters to be set. Candidates are 'area', 'freq', 'perf',
              'dp', 'sp'.

        Returns:
           N/A
        """

        for k, v in kwargs.items():
            k = k.lower()
            setattr(self, 'base_'+k, v)

        self.__update_config()



class IOCore(AbstractCore):
    """
    A Niagara2-like in-order core model. Check out more details at :class:`~lumos.model.core.AbstractCore`.
    """
    def __init__(self, mech=None, tech=None, pv=False, pen_adjust=None, sigma_level=None):

        self.base_area = techbase.area['IO']
        self.base_freq = techbase.freq['IO']
        self.base_perf = PERF_BASE
        self.base_dp = techbase.dp['IO']
        self.base_sp = techbase.sp['IO']
        super(IOCore, self).__init__(mech=mech, tech=tech, pv=pv,
                pen_adjust=pen_adjust, sigma_level=sigma_level)


    def bandwidth(self, app):
        """
        Get the bandwidth requirement for a specific application. It
        assumes the bandwidth requirement scales linearly to the
        frequency.

        Args:
           app (:class:`~lumos.model.application.App`):
              The application.

        Returns:
           The bandwidth requirement for the given application.

        """
        return self._fsf * self._bw0 * app['IO'].bw


class O3Core(AbstractCore):
    """
    An out-of-order core model. More detials in :class:`~lumos.model.core.AbstractCore`
    """
    def __init__(self, mech=None, tech=None, pv=False, pen_adjust=None, sigma_level=None):

        self.base_area = techbase.area['O3']
        self.base_freq = techbase.freq['O3']
        self.base_perf = O3_PERF_BASE
        self.base_dp = techbase.dp['O3']
        self.base_sp = techbase.sp['O3']
        super(O3Core, self).__init__(mech=mech, tech=tech, pv=pv,
                pen_adjust=pen_adjust, sigma_level=sigma_level)


def __plot_split(v, f, dp, sp, p, tech):
    fig = plt.figure()
    fig.suptitle('Technology node at %dnm' % (tech,))
    axes = fig.add_subplot(111)
    axes.set_xlabel('Supply Voltage (V)')
    axes.set_ylabel('Frequency (GHz)')
    axes.plot(v, f, v, f, 'rD')
    axes.set_xlim(0, 1.1)
    axes.set_yscale('log')
    axes.legend(axes.lines, ['Fitting', 'Simulated'], loc='upper left')
    axes.grid(True)
    fig.savefig('freq_volt.pdf')

    fig = plt.figure()
    axes = fig.add_subplot(111)
    axes.set_xlabel('Supply Voltage (V)')
    axes.set_ylabel('Power (W)')
    axes.plot(v, dp, '-D', v, sp, '-o', v, p, '-^')
    axes.set_xlim(0, 1.1)
    axes.set_yscale('log')
    axes.legend(axes.lines, ['Dynamic Power', 'Static Power', 'Overall'], loc='upper left', prop=dict(size='medium'))
    axes.grid(True)
    fig.savefig('power.pdf')


def __plot_nosplit(v, f, dp, sp, p, tech, mech):
    fig = plt.figure(figsize=(13.5, 6.9))
    fig.suptitle('%dnm' % (tech,))

    # Frequency scaling plot
    axes1 = fig.add_subplot(121)
    axes1.plot(v, f, marker='s')
    axes1.set_yscale('log')
    axes1.set_title('Freq')
    axes1.set_xlim(0.2, 1.2)

    # Power scaling plot
    axes2 = fig.add_subplot(122)
    axes2.plot(v, dp, v, sp, v, p)
    axes2.set_yscale('log')
    axes2.set_title('Power')
    axes2.set_xlim(0.2, 1.2)

    fig.savefig('%s_core_%dnm.png' % (mech, tech,))


if __name__ == '__main__':
    """"
    This is a test program to generate freq/power plots for Core
    """
    import matplotlib.pyplot as plt
    techList = (45, 32, 22, 16)
    #mechList = ('LP', 'HKMGS', 'ITRS', 'CONS')
    mechList = ('HKMGS', )
    vsList = [x * 0.05 for x in xrange(6, 23)]
    for mech in mechList:
        fig = plt.figure()
        axes = fig.add_subplot(111)
        for tech in techList:
            c = IOCore(tech=tech, mech=mech)
            #c.config(tech=32)
            #print 'tech:%d, mech: %s, dp: %f, sp: %f, freq:%f' % (tech, mech, c.dp0, c.sp0, c.freq)

            fs = []
            dp = []
            sp = []
            p = []

            for v in vsList:
                c.dvfs_by_volt(v)
                fs.append(c.freq/c.f0)
                dp.append(c.dp)
                sp.append(c.sp)
                p.append(c.power)

            #axes.plot(vsList, dp)
            #__plot_split(vs, fs, dp, sp, p, tech)
            __plot_nosplit(vsList, fs, dp, sp, p, tech, mech)

        #axes.set_yscale('log')
        #axes.legend(axes.lines, [ ('%dnm' % tech) for tech in techList ], loc='lower right')
        #axes.set_xlim(0.2, 1.2)
        #fig.savefig('%s.png' % mech)
