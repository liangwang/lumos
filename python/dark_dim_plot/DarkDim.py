#!/usr/bin/env python

import platform
if platform.system() == 'Linux':
    HOME_DIR='/home/lw2aw/eclipse_ws/analytical/python'
else:
    HOME_DIR='..'
    
import sys
sys.path.append(HOME_DIR)

from model.Core import *
from model.SymmetricSystem import *
from model.Application import *

from plot.Plot import Matplot, Gnuplot

from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
#import numpy as np


class Util2BudgetPlot(Gnuplot):
    def __init__(self, name='ITRS'):
        Gnuplot.__init__(self)


        self._tech_nodes = [45, 32, 22, 16, 11, 8]
        self._f_ratio = [1,0.99,0.9,0.8,0.5,0.01]

        self._mech = 'ITRS'
        self._name = 'util2budget'

        self._opt_list = {}


    def __writeScript(self):
        sfname = '%s.gpi' % self._name
        slines = []

        self._opt_list['figsize'] = '8.5in,22in'
        figtitle = 'Utilization ratio plotted to budget of area and power'
        slines.append('##FIGSIZE=%s\n' % self._opt_list['figsize'])
        slines.append("set multiplot layout 6,2 title '%s'\n" % figtitle)
        slines.append('set xrange [100:540]\n')
        slines.append('set xlabel "Area(mm^2)"\n')
        slines.append('set yrange [100:200]\n')
        slines.append('set ylabel "Power(W)"\n')
        slines.append('set zrange [0:1.1]\n')
        slines.append('set cbrange [0:1]\n')
        slines.append('set xyplane 0\n')
        slines.append('set contour\n')
        slines.append('set cntrparam levels incremental 0.2,0.2,1\n')
        slines.append('set grid xtics ytics\n')

        for tech in self._tech_nodes:
            for type in ['IO','O3']:
                plottitle = '%s-%dnm' % (type,tech)
                slines.append("set title '%s'\n" % plottitle)
                slines.append("splot '%s-%s-%dnm.dat' with pm3d notitle\n" % (self._name, type, tech))

        with open(sfname, 'wb') as f:
            f.writelines(slines)

    def __writeData(self):
        sys = SymmetricSystem()

        for t in self._tech_nodes:
            for type in ['IO','O3']:
                dfname = '%s-%s-%dnm.dat' % (self._name, type, t)
                dlines = []
                #dlines.append("Area Power Utilizaion\n")
                sys.core=Core(tech=t,mech=self._mech,type=type,dvfs_simple=False)
                for area in range(100,500,4):
                    for power in range(100,200):
                        sys.set_budget({'area':area,'power':power})
                        dlines.append("%d %d %g %g\n" % (area, power, sys.util_max, sys.util_max))
                    dlines.append("\n")

                with open(dfname, 'wb') as f:
                    f.writelines(dlines)

    def writeFiles(self):
        self.__writeScript()
        self.__writeData()

class Util2Budget(Matplot): # do not work well
    def __init__(self, name='ITRS'):
        Matplot.__init__(self)

        self._tech_nodes = [45, 32, 22, 16, 11, 8]
        self._f_ratio = [1,0.99,0.9,0.8,0.5,0.01]

        self._mech = 'ITRS'
        self._name = 'util2budget'

    def plot(self):
        sys = SymmetricSystem()

        fig = plt.figure(figsize=(11,8.5))
        fig.suptitle('title', y=0.99)
        fig_index = 1
        for t in self._tech_nodes:
            for type in ['IO', 'O3']:
                axes = fig.add_subplot(4,3,fig_index, projection='3d')
                sys.core = Core(tech=t,mech=self._mech,type=type,dvfs_simple=True)
                area_axis = []
                power_axis = []
                util_axis = []
                for area in range(100,500,4):
                    for power in range(100,200):
                        sys.set_budget({'area':area, 'power':power})
                        area_axis.append(area)
                        power_axis.append(power)
                        util_axis.append(sys.util_max)
                X=np.fromiter(area_axis,np.int).reshape((100,-1))
                Y=np.fromiter(power_axis,np.int).reshape((100,-1))
                Z=np.fromiter(util_axis,np.int).reshape((100,-1))
                axes.plot_surface(X,Y,Z)

                fig_index = fig_index + 1
        
        fig.savefig('test.pdf')


if __name__ == '__main__':
    p = Util2BudgetPlot()
    p.writeFiles()
