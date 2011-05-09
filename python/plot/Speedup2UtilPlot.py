#!/usr/bin/env python
    
from model.Core import *
from model.SymmetricSystem import *
from model.Application import *

from Plot import *


class Speedup2UtilPlot(Plot):
    def __init__(self, name='itrs'):
        Plot.__init__(self, name)

        self._samples = 100

        self._area = 111
        self._power = 125

        self._tech_nodes = [45, 32, 22, 16, 11, 8]
        self._f_ratio = [1,0.99,0.9,0.8,0.5,0.01]

        self._mech = 'itrs'


    def __writeScript(self):
        sfname = '%s.gpi' % self._name
        slines = []

        self._opt_list['figsize'] = '8.5in,22in'
        figtitle = 'Power=%dW, Area=%dmm^2' % (self._power, self._area)
        slines.append('##FIGSIZE=%s\n' % self._opt_list['figsize'])
        slines.append("set multiplot layout 6,2 title '%s'\n" % figtitle)
        slines.append('set xrange [0:1.1]\n')
        slines.append('set style data lines\n')
        slines.append('set key left top\n')

        for tech in self._tech_nodes:
            plottitle = 'IO-%dnm' % tech
            slines.append("set title '%s'\n" % plottitle)
            slines.append("plot for [i=1:%d] '%s-io-%dnm.dat' using 1:i+1 title columnhead\n" % (len(self._f_ratio), self._name, tech))

            plottitle = 'O3-%dnm' % tech
            slines.append("set title '%s'\n" % plottitle)
            slines.append("plot for [i=1:%d] '%s-o3-%dnm.dat' using 1:i+1 title columnhead\n" % (len(self._f_ratio), self._name, tech))

        with open(sfname, 'wb') as f:
            f.writelines(slines)

    def __writeData(self):
        sys = SymmetricSystem(budget={'power':self._power,'area':self._area})

        for t in self._tech_nodes:
            # IO Core
            sys.set_core(IOCore(tech=t))
            dfname = '%s-io-%dnm.dat' % (self._name, t)

            dlines = []

            # write title row
            dlines.append('Utilization ')
            for fratio in self._f_ratio:
                dlines.append('f=%g ' % fratio)
            dlines.append('\n')

            # write data
            urmax = sys.get_util_max()
            urmin = sys.get_util_min()
            step = (urmax - urmin) / self._samples
            for i in range(self._samples):
                ur = urmin + i * step

                dlines.append('%g ' % ur)
                sys.set_util_ratio(ur)
                for fratio in self._f_ratio:
                    dlines.append('%g ' % sys.speedup(Application(fratio)))

                dlines.append('\n')

            with open(dfname, 'wb') as f:
                f.writelines(dlines)

            # O3 Core
            sys.set_core(O3Core(tech=t))
            dfname = '%s-o3-%dnm.dat' % (self._name, t)

            dlines = []

            # write title row
            dlines.append('Utilization ')
            for fratio in self._f_ratio:
                dlines.append('f=%g ' % fratio)
            dlines.append('\n')

            # write data
            urmax = sys.get_util_max()
            urmin = sys.get_util_min()
            step = (urmax - urmin) / self._samples
            for i in range(self._samples):
                ur = urmin + i * step

                dlines.append('%g ' % ur)
                sys.set_util_ratio(ur)
                for fratio in self._f_ratio:
                    dlines.append('%g ' % sys.speedup(Application(fratio)))

                dlines.append('\n')

            with open(dfname, 'wb') as f:
                f.writelines(dlines)

    def writeFiles(self):
        self.__writeScript()
        self.__writeData()

    def setFigSize(self, size):
        self._opt_list['figsize'] = size

    def setSamples(self, sample):
        self._samples = sample

    def setScalingMechanism(self, mech):
        self._mech = mech

    def setBudget(self, budget):
        self._area = budget['area']
        self._power = budget['power']

    def setFRatioList(self, flist):
        self._f_ratio = flist

    def setTechnodeList(self, tlist):
        self._tech_nodes = tlist


class Speedup2UtilPlot2(Plot):
    """ Speedup to Utilization ratio with memory factor alpha
    """
    def __init__(self, name='itrs-mem'):
        Plot.__init__(self, name)

        self._samples = 100

        self._area = 111
        self._power = 125

        self._tech_nodes = [45, 32, 22, 16, 11, 8]
        self._f_ratio = [0.5,0.2,0.1,0.01]
        self._m_ratio = [0,0.2,0.4,0.6,0.8]

        self._mech = 'itrs'


    def __writeScript(self):
        sfname = '%s.gpi' % self._name
        slines = []

        self._opt_list['figsize'] = '8.5in,22in'
        figtitle = 'Power=%dW, Area=%dmm^2' % (self._power, self._area)
        slines.append('##FIGSIZE=%s\n' % self._opt_list['figsize'])
        slines.append("set multiplot layout 6,2 title '%s'\n" % figtitle)
        slines.append('set xrange [0:1.1]\n')
        slines.append('set style data lines\n')
        slines.append('set key left top\n')

        for tech in self._tech_nodes:
            plottitle = 'IO-%dnm' % tech
            slines.append("set title '%s'\n" % plottitle)
            slines.append("plot for [i=1:%d] '%s-io-%dnm.dat' using 1:i+1 title columnhead\n" % (len(self._f_ratio), self._name, tech))

            plottitle = 'O3-%dnm' % tech
            slines.append("set title '%s'\n" % plottitle)
            slines.append("plot for [i=1:%d] '%s-o3-%dnm.dat' using 1:i+1 title columnhead\n" % (len(self._f_ratio), self._name, tech))

        with open(sfname, 'wb') as f:
            f.writelines(slines)

    def __writeData(self):
        sys = SymmetricSystem(budget={'power':self._power,'area':self._area})

        for t in self._tech_nodes:
            for fratio in self._f_ratio:
                app = Application(fratio)

                # IO Core
                sys.set_core(IOCore(tech=t))
                dfname = '%s-io-%dnm-f%g.dat' % (self._name, t, fratio)

                dlines = []

                # write title row
                dlines.append('Utilization ')
                for mratio in self._m_ratio:
                    dlines.append('m=%g ' % mratio)
                dlines.append('\n')

                # write data
                urmax = sys.get_util_max()
                urmin = sys.get_util_min()
                step = (urmax - urmin) / self._samples
                for i in range(self._samples):
                    ur = urmin + i * step

                    dlines.append('%g ' % ur)
                    sys.set_util_ratio(ur)

                    for mratio in self._m_ratio:
                        app.m = mratio
                        dlines.append('%g ' % sys.speedup(app))

                    dlines.append('\n')

                with open(dfname, 'wb') as f:
                    f.writelines(dlines)

                # O3 Core
                sys.set_core(O3Core(tech=t))
                dfname = '%s-o3-%dnm-f%g.dat' % (self._name, t, fratio)

                dlines = []

                # write title row
                dlines.append('Utilization ')
                for mratio in self._m_ratio:
                    dlines.append('m=%g ' % mratio)
                dlines.append('\n')

                # write data
                urmax = sys.get_util_max()
                urmin = sys.get_util_min()
                step = (urmax - urmin) / self._samples
                for i in range(self._samples):
                    ur = urmin + i * step

                    dlines.append('%g ' % ur)
                    sys.set_util_ratio(ur)

                    for mratio in self._m_ratio:
                        app.m = mratio
                        dlines.append('%g ' % sys.speedup(app))

                    dlines.append('\n')

                with open(dfname, 'wb') as f:
                    f.writelines(dlines)

    def writeFiles(self):
        self.__writeScript()
        self.__writeData()

    def setFigSize(self, size):
        self._opt_list['figsize'] = size

    def setSamples(self, sample):
        self._samples = sample

    def setScalingMechanism(self, mech):
        self._mech = mech

    def setBudget(self, budget):
        self._area = budget['area']
        self._power = budget['power']

    def setFRatioList(self, flist):
        self._f_ratio = flist

    def setTechnodeList(self, tlist):
        self._tech_nodes = tlist
