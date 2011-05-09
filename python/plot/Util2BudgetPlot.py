#!/usr/bin/env python
    
from model.Core import *
from model.SymmetricSystem import *
from model.Application import *

from Plot import *


class Util2BudgetPlot(Plot):
    def __init__(self, name='itrs'):
        Plot.__init__(self, name)


        self._tech_nodes = [45, 32, 22, 16, 11, 8]
        self._f_ratio = [1,0.99,0.9,0.8,0.5,0.01]

        self._mech = 'itrs'


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
            plottitle = 'IO-%dnm' % tech
            slines.append("set title '%s'\n" % plottitle)
            slines.append("splot '%s-io-%dnm.dat' with pm3d notitle\n" % (self._name, tech))

            plottitle = 'O3-%dnm' % tech
            slines.append("set title '%s'\n" % plottitle)
            slines.append("splot '%s-o3-%dnm.dat' with pm3d notitle\n" % (self._name, tech))

        with open(sfname, 'wb') as f:
            f.writelines(slines)

    def __writeData(self):
        sys = SymmetricSystem()

        for t in self._tech_nodes:
            dfname = '%s-io-%dnm.dat' % (self._name, t)
            dlines = []
            #dlines.append("Area Power Utilizaion\n")
            sys.set_core(IOCore(tech=t,mech=self._mech))
            for area in range(100,500,4):
                for power in range(100,200):
                    sys.set_budget({'area':area,'power':power})
                    urmax = sys.get_util_max()
                    urmin = sys.get_util_min()
                    dlines.append("%d %d %g %g\n" % (area, power, urmax, urmax))
                dlines.append("\n")

            with open(dfname, 'wb') as f:
                f.writelines(dlines)

            dfname = '%s-o3-%dnm.dat' % (self._name, t)
            dlines = []
            #dlines.append("Area Power Utilizaion\n")
            sys.set_core(O3Core(tech=t,mech=self._mech))
            for area in range(100,500,4):
                for power in range(100,200):
                    sys.set_budget({'area':area,'power':power})
                    urmax = sys.get_util_max()
                    urmin = sys.get_util_min()
                    dlines.append("%d %d %g %g\n" % (area, power, urmax, urmax))
                dlines.append("\n")

            with open(dfname, 'wb') as f:
                f.writelines(dlines)


    def writeFiles(self):
        self.__writeScript()
        self.__writeData()

    #def setFigSize(self, size):
        #self._opt_list['figsize'] = size

    #def setSamples(self, sample):
        #self._samples = sample

    #def setScalingMechanism(self, mech):
        #self._mech = mech

    #def setBudget(self, budget):
        #self._area = budget['area']
        #self._power = budget['power']

    #def setFRatioList(self, flist):
        #self._f_ratio = flist

    #def setTechnodeList(self, tlist):
        #self._tech_nodes = tlist

