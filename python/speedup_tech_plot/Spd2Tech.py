#!/usr/bin/env python

import sys
sys.path.append('..')

from model.Core import *
from model.SymmetricSystem import *
from model.Application import *

from plot.Plot import *

class Spd2TechPlot(Plot):
    def __init__(self, prefix='spd2tech', mech='ITRS'):

        self._prefix = prefix
        self._mech = mech
        self._name = "%s-%s" % (prefix, mech)

        self._samples = 100

        self._area = 111
        self._power = 125

        self._tech_nodes = [45, 32, 22, 16, 11, 8]
        self._f_ratio = [0.99, 0.9, 0.8, 0.5, 0.1, 0.01]
        self._m_ratio = [0, 0.2, 0.4, 0.6, 0.8]

        self._opt_list = {'figsize':'11in,8in'}


    def __writeData(self):
        sys = SymmetricSystem(budget={'power':self._power,'area':self._area})


        for f in self._f_ratio:
            dfname = '%s-f%g.dat' % (self._name, f)

            dlines = []

            dlines.append('Tech ')
            for mratio in self._m_ratio:
                dlines.append('m=%g ' % mratio)
            dlines.append('\n')

            for t in self._tech_nodes:
                dlines.append('%dnm ' % t)
                for mratio in self._m_ratio:
                    sys.set_core(core=IOCore(tech=t, mech=self._mech))
                    ioperf = sys.get_best_perf(Application(f=f,m=mratio))

                    sys.set_core(core=O3Core(tech=t, mech=self._mech))
                    o3perf = sys.get_best_perf(Application(f=f,m=mratio))

                    dlines.append('%g ' % (ioperf if ioperf>o3perf else o3perf))

                dlines.append('\n')

            with open(dfname, 'wb') as f:
                f.writelines(dlines)



    def __writeScript(self):
        sfname = '%s.gpi' % self._name
        slines = []

        figtitle = 'Power=%dW, Area=%dmm^2' % (self._power, self._area)
        slines.append('##FIGSIZE=%s\n' % self._opt_list['figsize'])
        slines.append("set multiplot layout 2,3 title '%s'\n" % figtitle)
        slines.append('set xrange [-0.5:5.5]\n')
        slines.append('set style data linespoints\n')
        slines.append('set key left top Left\n')
        slines.append('set xtics rotate by -30\n')
        slines.append('set logscale y\n')

        for fratio in self._f_ratio:
            plottitle = 'f=%g' % fratio
            slines.append("set title '%s'\n" % plottitle)
            
            slines.append("plot for [i=1:%d] '%s-f%g.dat' using i+1:xtic(1) title columnhead\n" % (len(self._m_ratio), self._name, fratio))

        with open(sfname, 'wb') as f:
            f.writelines(slines)

    def write_files(self):
        self.__writeScript()
        self.__writeData()

    def set_figsize(self, size):
        self._opt_list['figsize'] = size

    def set_samples(self, sample):
        self._samples = sample

    def set_mech(self, mech):
        self._mech = mech
        self._name = "%s-%s" % (self._prefix, self._mech)

    def set_plot_prefix(self, prefix):
        self._prefix = prefix
        self._name = "%s-%s" % (self._prefix, self._mech)

    def set_budget(self, budget):
        self._area = budget['area']
        self._power = budget['power']

    def set_fratio_list(self, flist):
        self._f_ratio = flist

    def set_tech_list(self, tlist):
        self._tech_nodes = tlist


if __name__ == '__main__':
    p = Spd2TechPlot()
    p.set_figsize('12in,9in')

    budget = {'area':500, 'power': 200}
    p.set_budget(budget)
    p.set_plot_prefix('%dmm2-%dw' % (budget['area'], budget['power']))
    p.set_mech('ITRS')
    p.write_files()

    p.set_mech('cons')
    p.write_files()

    budget = {'area':111, 'power': 125}
    p.set_budget(budget)
    p.set_plot_prefix('%dmm2-%dw' % (budget['area'], budget['power']))
    p.set_mech('ITRS')
    p.write_files()

    p.set_mech('cons')
    p.write_files()

