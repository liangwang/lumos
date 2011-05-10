#!/usr/bin/env python

import math
import numpy as np
import matplotlib.pyplot as plt

from model.Core import IOCore, O3Core
from model.System import *
from model.Application import *
from model.SymmetricSystem import *
from model.UnlimitedPowerSystem import *

from plot.Util2Budget import *
from plot.Spd2Util import *
from plot.Spd2Tech import *

def do1():
    technodes = [45, 32, 22, 16, 11, 8]
    sys = UnlimitedPowerSystem(area=300)
    datalines = []
    line = "tech_node Power(IO) Power(O3)\n"
    datalines.append(line)
    for tech in technodes:
        sys.set_core(IOCore(tech=tech))
        iopower = sys.power

        sys.set_core(O3Core(tech=tech))
        o3power = sys.power

        line = "%d %f %f\n" % (tech, iopower, o3power)
        datalines.append(line)
        
    datalines.append('\n\n')

    line = "tech_node Power(IO) Power(O3)\n"
    datalines.append(line)
    for tech in technodes:
        sys.set_core(IOCore(tech=tech, mech='cons'))
        iopower = sys.power

        sys.set_core(O3Core(tech=tech, mech='cons'))
        o3power = sys.power

        line = "%d %f %f\n" % (tech, iopower, o3power)
        datalines.append(line)
        
    with open('power.dat', 'w') as f:
        f.writelines(datalines)

def do_matplot():
    #techbase.dvfs_aggressive = False
    #applist = [Application(f=1),
               #Application(f=0.99), @IndentOk
               #Application(f=0.9),
               #Application(f=0.8),
               #Application(f=0.5),
               #Application(f=0.01)]

    #plt.xlabel('Utilization Ratio')
    #plt.ylabel('Speedup')
    #sys = SymmetricSystem(budget={'area':111,'power':125}, core=O3Core(tech=45))
    #plt.subplot(3,2,1)
    #plot_to_uratio(sys, applist)

    #sys = SymmetricSystem(core=O3Core(tech=32))
    #plt.subplot(3,2,2)
    #plot_to_uratio(sys, applist)

    #sys = SymmetricSystem(core=O3Core(tech=22))
    #plt.subplot(3,2,3)
    #plot_to_uratio(sys, applist)

    #sys = SymmetricSystem(core=O3Core(tech=16))
    #plt.subplot(3,2,4)
    #plot_to_uratio(sys, applist)

    #sys = SymmetricSystem(core=O3Core(tech=11))
    #plt.subplot(3,2,5)
    #plot_to_uratio(sys, applist)

    #sys = SymmetricSystem(core=O3Core(tech=8))
    #plt.subplot(3,2,6)
    #plot_to_uratio(sys, applist)

    #plt.show()
    pass

def do2():
    p = Util2BudgetPlot()
    p.writeFiles()

def do3():
    p = Speedup2UtilPlot2()
    p.writeFiles()

def do4():
    p = Speedup2UtilPlot()
    p.writeFiles()

def do5():
    p = Spd2TechPlot()
    p.writeFiles()

def test():
    sys = SymmetricSystem(budget={'area':111,'power':125})
    app = Application(f=0.5,m=0)
    sys.set_util_ratio(1)
    print sys.speedup(app)

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



if __name__ == '__main__':
    #test()
    do5()
