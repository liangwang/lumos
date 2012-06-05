#!/usr/bin/env python

#import math
#import numpy as np
import matplotlib.pyplot as plt

#from model.core import Core
#from model.system import *
#from model.application import *
#from model.SymmetricSystem import *
#from model.UnlimitedPowerSystem import *


def do1():
    technodes = [45, 32, 22, 16, 11, 8]
    #sys = UnlimitedPowerSystem(area=300)
    datalines = []
    line = "tech_node Power(IO) Power(O3)\n"
    datalines.append(line)
    for tech in technodes:
        #sys.set_core(IOCore(tech=tech))
        iopower = sys.power

        #sys.set_core(O3Core(tech=tech))
        o3power = sys.power

        line = "%d %f %f\n" % (tech, iopower, o3power)
        datalines.append(line)

    datalines.append('\n\n')

    line = "tech_node Power(IO) Power(O3)\n"
    datalines.append(line)
    for tech in technodes:
        #sys.set_core(IOCore(tech=tech, mech='cons'))
        iopower = sys.power

        #sys.set_core(O3Core(tech=tech, mech='cons'))
        o3power = sys.power

        line = "%d %f %f\n" % (tech, iopower, o3power)
        datalines.append(line)

    with open('power.dat', 'w') as f:
        f.writelines(datalines)


def do_matplot():
    pass
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


def do2():
    pass
    #p = Util2BudgetPlot()
    #p.writeFiles()


def do3():
    pass
    #p = Speedup2UtilPlot2()
    #p.writeFiles()


def do4():
    pass
    #p = Speedup2UtilPlot()
    #p.writeFiles()


def do5():
    pass
    #p = Spd2TechPlot()
    #p.writeFiles()


def testSystem():
    pass
    #sys = SymmetricSystem(budget={'area': 500, 'power': 200})
    #app = Application(f=0.99, m=0)
    #sys.util_ratio = 0.52
    #sys.set_core_prop(type='O3', tech=11)
    #print sys.speedup(app)


def testCore():
    #core = Core(tech=32)
    #core.dvfs_simple = False
    #vmin = core.volt * 0.8
    #vmax = core.volt * 1.3
    #v = vmin
    print "Real DVFS\n"
    #while v <= vmax:
        #core.dvfs(v)
        #print (v, core.freq, core.power)
        #v = v + 0.1

    print "Simple DVFS\n"
    #core.dvfs_simple = True
    #v = vmin
    #while v <= vmax:
        #core.dvfs(v)
        #print (v, core.freq, core.power)
    #    v = v + 0.1


def plot_to_uratio(sys, applist):
    samples = 1000
    step = (sys.urmax - sys.urmin) / samples
    utils = []
    for i in range(samples):
        utils.append(sys.urmin + i * step)
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


import optparse
if __name__ == '__main__':
    parser = optparse.OptionParser()
    parser.add_option('-x', '--gui', action='store_true', default=False,
                      help='Start a GUI environment to analyze and plot')
    parser.add_option('-r', '--run-mode', default='a',
                      help='Run mode, analysis, plot, or both')
    parser.add_option('--sys-area', type='int', default=400,
                      help='Area budget (mm^2) for the whole chip')
    parser.add_option('--sys-power', type='int', default=100,
                      help='Power budget (W) for the whole chip')
    parser.add_option('--use-sys2', action='store_true', default=False,
                      help='Use SymSys')
    options, args = parser.parse_args()

    if options.gui:
        #import gui.test as GUITest
        #from PyQt4.QtCore import *
        #from PyQt4.QtGui import *
        import sys
        #app=QApplication(sys.argv)
        #form = GUITest.AppForm()
        #form.show()
        #app.exec_()

    if options.run_mode == 'a':
        pass
    elif options.run_mode == 'p':
        pass
    elif options.run_mode == 'ap':
        pass
    else:
        print 'Unknown run mode: %s' % options.run_mode


