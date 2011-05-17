#!/usr/bin/env python

import sys
sys.path.append('..')

from model.Core import *

from plot.Plot import *
import matplotlib.pyplot as plt

class Freq2VoltPlot(Plot):
    """ This class facilitate gnuplot to genearte figures """
    def __init__(self, prefix='freq2volt', mech='ITRS'):


        self._prefix = prefix
        self._mech = mech
        self._name = "%s-%s" % (prefix, mech)

        self._samples = 100

        self._area = 111
        self._power = 125

        self._tech_nodes = [45, 32, 22, 16, 11, 8]
        self._f_ratio = [0.99, 0.9, 0.8, 0.5, 0.1, 0.01]
        self._m_ratio = [0, 0.2, 0.4, 0.6, 0.8]
        self._alpha_list = [1.2, 1.4, 1.6, 1.8, 2]

        self._opt_list = {'figsize':'11in,8in'}

    def __writeData(self):

        dfname = '%s.dat' % (self._name)
        core = IOCore()
        core.dvfs_simple=False
        vfactor_lb = core.vsf_min * 0.3
        vfactor_ub = core.vsf_max

        samples = 200
        dlines = []

        dlines.append('Volt ')
        for alpha in self._alpha_list:
            dlines.append('%g ' % alpha)
        dlines.append('\n')

        step = 0.002
        v = vfactor_lb
        for i in range(samples):
            dlines.append('%g ' % v)
            for alpha in self._alpha_list:
                core.alpha=alpha
                dlines.append('%g ' % core.dvfs(v))
            dlines.append('\n')
            v = v+ step

        samples = 100
        step = (vfactor_ub - v)/samples
        for i in range(samples):
            dlines.append('%g ' % v)
            for alpha in self._alpha_list:
                core.alpha=alpha
                dlines.append('%g ' % core.dvfs(v))
            dlines.append('\n')
            v = v+step

        with open(dfname, 'wb') as f:
            f.writelines(dlines)



    def __writeScript(self):
        sfname = '%s.gpi' % self._name
        slines = []

        figtitle = 'Power=%dW, Area=%dmm^2' % (self._power, self._area)
        slines.append('##FIGSIZE=%s\n' % self._opt_list['figsize'])
        slines.append('set xrange [0:1.35]\n')
        slines.append('set style data linespoints\n')
        slines.append('set key left top Left\n')
        slines.append('set xtics rotate by -30\n')

        
        slines.append("plot for [i=1:%d] '%s.dat' using 1:i+1 title '{/Symbol a}=columnhead(i+1)'\n" % (len(self._alpha_list), self._name))

        with open(sfname, 'wb') as f:
            f.writelines(slines)

    def write_files(self):
        self.__writeScript()
        self.__writeData()

    def set_figsize(self, size):
        self._opt_list['figsize'] = size

    @property
    def samples(self):
        return self._samples

    @samples.setter
    def set_samples(self, sample):
        self._samples = sample

    @property
    def mech(self):
        return self._mech

    @mech.setter
    def set_mech(self, mech):
        self._mech = mech
        self._name = "%s-%s" % (self._prefix, self._mech)

    @property
    def prefix(self):
        return self._prefix

    @prefix.setter
    def set_prefix(self, prefix):
        self._prefix = prefix
        self._name = "%s-%s" % (self._prefix, self._mech)

    def set_budget(self, budget):
        self._area = budget['area']
        self._power = budget['power']

    def set_fratio_list(self, flist):
        self._f_ratio = flist

    def set_tech_list(self, tlist):
        self._tech_nodes = tlist


class Freq2Volt(object):
    """ This class exploit matplotlib """
    def __init__(self):
        # default figure size 1280pixels x 1024pixels
        self._fig = plt.figure(figsize=(12.8,10.24))
        
        # only one subplot
        self._axes = self._fig.add_subplot(111)

        self._alpha_list = [1.2, 1.4, 1.6, 1.8, 2]

        self._samples = 100

    def matplot(self):
        core = Core(type='IO', dvfs_simple=True)
        
        vfactor_lb = core.vsf_min * 0.3
        vfactor_ub = core.vsf_max
        vth = core.vth
        vnear = core.vth+0.2

        volts = []
        freqs = dict([ (alpha, []) for alpha in self._alpha_list])

        step = (vth - vfactor_lb)/self._samples
        v = vfactor_lb
        for i in range(self._samples):
            v = v + step
            volts.append(v)
            for alpha in self._alpha_list:
                core.alpha=alpha
                freqs[alpha].append(core.dvfs(v))
            
        v = vth
        step = (vnear - vth) /self._samples
        for i in range(self._samples):
            v = v + step
            volts.append(v)
            for alpha in self._alpha_list:
                core.alpha=alpha
                freqs[alpha].append(core.dvfs(v))

        v = vnear
        step = (vfactor_ub - vnear) / self._samples
        for i in range(self._samples):
            v = v+step
            volts.append(v)
            for alpha in self._alpha_list:
                core.alpha = alpha
                freqs[alpha].append(core.dvfs(v))

        for alpha in self._alpha_list:
            self._axes.plot(volts, freqs[alpha])

        
        self._axes.legend(self._axes.lines, [r'$\alpha$=%g' % alpha for alpha in self._alpha_list], 'upper left')
        self._axes.set_title('Frequency scaling (%dnm, %s)' % (core.tech, core.mech.upper()))
        self._axes.set_xlabel(r'$V_{dd}$ ($V$)')
        self._axes.set_ylabel(r'$f/f_{norm}$')
        self._fig.savefig('matplot.pdf')

        self._axes.set_yscale('log')
        self._fig.savefig('matplot-log.pdf')


    @property
    def samples(self):
        return self._samples

    @samples.setter
    def set_samples(self, sample):
        self._samples = sample

    @property
    def mech(self):
        return self._mech

    @mech.setter
    def set_mech(self, mech):
        self._mech = mech
        self._name = "%s-%s" % (self._prefix, self._mech)

    @property
    def prefix(self):
        return self._prefix

    @prefix.setter
    def set_prefix(self, prefix):
        self._prefix = prefix
        self._name = "%s-%s" % (self._prefix, self._mech)


if __name__ == '__main__':
    p = Freq2Volt()
    p.matplot()
    #p = Freq2VoltPlot()
    #p.write_files()

