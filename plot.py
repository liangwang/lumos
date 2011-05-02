#!/usr/bin/env python
    
class Plot:
    def __init__(self, name='default'):
        self.gpi = '%s.gpi' % name
        self.dat = '%s.dat' % name

        self.dlines = []
        self.slines = []

        self.xlabel = 'xlabel'
        self.ylabel = 'ylabel'

        self._opt_list = {}

    def writeDataFile(self):
        with open(self.dat, 'w') as f:
            f.writelines(self.datalines)

    def writeGPIFile(self):
        with open(self.gpi, 'w') as f:
            f.writelines(self.scriptlines)
        
    def writeFiles(self):
        self.writeDataFile(self)
        self.writeGPIFile(self)
        
    def setOption(opname, value):
        _opt_list[opname] = value


class LinepointPlot(Plot):
    def __init__(self, name='default'):
        Plot.__init__(self, name)

    def genScript(self):
        self.slines.append('##FIGSIZE=%S' % self._op_list['figsize'])

    def genData(self):
        pass





        


from core import IOCore, O3Core
from system import *
from application import *
from technology import Base as techbase

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

    plt.show()




