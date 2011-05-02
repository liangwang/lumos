#!/usr/bin/env python
    
from model.core import IOCore, O3Core
from model.system import *
from model.application import *
from model.technology import Base as techbase

class Plot:
    def __init__(self, name='default'):
        self._name = name

        self._opt_list = {'figsize': '5in,3in'}

    def setDataFileName(self, dfname):
        self.dat = dfname

    def setGPIFileName(slef, gfname):
        self.gpi = gfname


class SpeedupToUtilizationPlot(Plot):
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
            step = (sys.urmax - sys.urmin) / self._samples
            for i in range(self._samples):
                ur = sys.urmin + i * step

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
            step = (sys.urmax - sys.urmin) / self._samples
            for i in range(self._samples):
                ur = sys.urmin + i * step

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


def plot_to_uratio(sys, applist):
    samples = 1000
    step = (sys.urmax-sys.urmin) / samples
    utils = []
    for i in range(samples):
        utils.append(sys.urmin+i*step)
    perflist = []
    for app in applist:
        perfs = []
        for ur in utils:
            sys.set_util_ratio(ur)
            perfs.append(sys.speedup(app))
        perflist.append(perfs)

    plt.title('%s-%dw-%dmm2-%dnm' % (sys.core.name, sys.power, sys.area, sys.core.tech)) 
    plt.plot(utils, perflist[0],
             utils, perflist[1],
             utils, perflist[2],
             utils, perflist[3],
             utils, perflist[4],
             utils, perflist[5])
    plt.xlim(0, 1.1)

if __name__ == '__main__' :
    #techbase.dvfs_aggressive = False
    applist = [Application(f=1),
               Application(f=0.99),
               Application(f=0.9),
               Application(f=0.8),
               Application(f=0.5),
               Application(f=0.01)]

    plt.xlabel('Utilization Ratio')
    plt.ylabel('Speedup')
    sys = SymmetricSystem(budget={'area':111,'power':125}, core=O3Core(tech=45))
    plt.subplot(3,2,1)
    plot_to_uratio(sys, applist)

    sys = SymmetricSystem(core=O3Core(tech=32))
    plt.subplot(3,2,2)
    plot_to_uratio(sys, applist)

    sys = SymmetricSystem(core=O3Core(tech=22))
    plt.subplot(3,2,3)
    plot_to_uratio(sys, applist)

    sys = SymmetricSystem(core=O3Core(tech=16))
    plt.subplot(3,2,4)
    plot_to_uratio(sys, applist)

    sys = SymmetricSystem(core=O3Core(tech=11))
    plt.subplot(3,2,5)
    plot_to_uratio(sys, applist)

    sys = SymmetricSystem(core=O3Core(tech=8))
    plt.subplot(3,2,6)
    plot_to_uratio(sys, applist)

    #plt.show()

    p = SpeedupToUtilizationPlot()
    p.writeFiles()




