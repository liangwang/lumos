#@PydevCodeAnalysisIgnore

#!/usr/bin/env python

#FIXME: make it compatible with new core module

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

        self._sys = SymmetricSystem(budget={'power':self._power,'area':self._area})
        self._sys.set_core_prop(dvfs_simple=False)

        self._tech_nodes = [45, 32, 22, 16, 11, 8]
        self._f_ratio = [0.99, 0.9, 0.8, 0.5, 0.1, 0.01]
        self._m_ratio = [0, 0.2, 0.4, 0.6, 0.8]

        self._opt_list = {'figsize':'11in,8in'}



    def __get_best_perf(self, app):
        """ Tune the system to have best performance with certain app """

        sys = self._sys

        if (self._sys.core.dvfs_simple):
            sys.util_ratio = sys.util_max

            sys.set_core_prop(type='IO')
            ioperf = sys.speedup(app)

            sys.set_core_prop(type='O3')
            o3perf = sys.speedup(app)
        else:
            sys.set_core_prop(type='O3')
            
            util_step = 0.01
            util = sys.util_min
            perf = 0
            while util < sys.util_max:
                sys.util_ratio = util
                speedup = sys.speedup(app)
                if speedup > perf:
                    perf = speedup
                #else:
                    #break
                util = util + util_step
            o3perf = perf

            sys.set_core_prop(type='IO')

            util = sys.util_min
            perf = 0
            while util < sys.util_max:
                sys.util_ratio = util
                speedup = sys.speedup(app)
                if speedup > perf:
                    perf = speedup
                #else:
                    #break
                util = util + util_step
            ioperf = perf


        if (ioperf > o3perf):
            ret = ioperf
        else :
            sys.set_core_prop(type='O3')
            ret = o3perf

        return ret


    def __writeData(self):

        sys = self._sys
        for f in self._f_ratio:
            dfname = '%s-f%g.dat' % (self._name, f)

            dlines = []

            dlines.append('Tech ')
            for mratio in self._m_ratio:
                dlines.append('m=%g ' % mratio)
            dlines.append('\n')

            for t in self._tech_nodes:
                sys.set_core_prop(tech=t)
                dlines.append('%dnm ' % t)
                for mratio in self._m_ratio:

                    perf = self.__get_best_perf(Application(f=f,m=mratio))

                    dlines.append('%g ' % perf)

                dlines.append('\n')

            with open(dfname, 'wb') as f:
                f.writelines(dlines)



    def __writeScript(self):
        sfname = '%s-logscale.gpi' % self._name
        #sfname = '%s.gpi' % self._name
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
        self._sys.set_core_prop(mech = mech)

    def set_plot_prefix(self, prefix):
        self._prefix = prefix
        self._name = "%s-%s" % (self._prefix, self._mech)

    def set_budget(self, budget):
        self._area = budget['area']
        self._power = budget['power']
        self._sys.set_budget(budget)

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

    p.set_mech('CONS')
    p.write_files()

    budget = {'area':111, 'power': 125}
    p.set_budget(budget)
    p.set_plot_prefix('%dmm2-%dw' % (budget['area'], budget['power']))
    p.set_mech('ITRS')
    p.write_files()

    p.set_mech('CONS')
    p.write_files()

