#!/usr/bin/env python

HOME_DIR='/home/lw2aw/eclipse_ws/analytical/python'

import sys
sys.path.append(HOME_DIR)

from model.Core import *
from model.SymmetricSystem import *
from model.Application import *

from plot.Plot import *

import matplotlib.pyplot as plt


class Speedup2UtilPlot(Plot):
    def __init__(self, name='ITRS'):
        Plot.__init__(self, name)

        self._samples = 100

        self._area = 111
        self._power = 125

        self._tech_nodes = [45, 32, 22, 16, 11, 8]
        self._f_ratio = [1,0.99,0.9,0.8,0.5,0.01]

        self._mech = 'ITRS'



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
            sys.set_core_prop(type='IO',tech=t)
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
            sys.set_core_prop(type='O3',tech=t)
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
    def __init__(self, name='ITRS-mem'):
        Plot.__init__(self, name)

        self._samples = 100

        self._area = 111
        self._power = 125

        self._tech_nodes = [45, 32, 22, 16, 11, 8]
        self._f_ratio = [0.5,0.2,0.1,0.01]
        self._m_ratio = [0,0.2,0.4,0.6,0.8]

        self._mech = 'ITRS'


    def __writeScript(self):

        for tech in self._tech_nodes:
            sfname = '%s-%dnm.gpi' % (self._name, tech)
            slines = []

            self._opt_list['figsize'] = '11in,8.5in'
            figtitle = 'Power=%dW, Area=%dmm^2, Tech=%dnm' % (self._power, self._area, tech)
            slines.append('##FIGSIZE=%s\n' % self._opt_list['figsize'])
            slines.append("set multiplot layout 2,2 title '%s'\n" % figtitle)
            slines.append('set xrange [0:1.1]\n')
            slines.append('set style data lines\n')
            slines.append('set key left top\n')

            for fratio in self._f_ratio:
                plottitle = 'f=%g' % fratio
                slines.append("set title '%s'\n" % plottitle)
                slines.append("plot for [i=1:%d] '%s-io-%dnm-f%g.dat' using 1:i+1 title columnhead with lines linetype 1 linecolor i,\\\n" % (len(self._f_ratio), self._name, tech, fratio))

                #plottitle = 'O3-%dnm' % tech
                #slines.append("set title '%s'\n" % plottitle)
                slines.append("for [i=1:%d] '%s-o3-%dnm-f%g.dat' using 1:i+1 title columnhead with lines linetype 2 linecolor i\n" % (len(self._f_ratio), self._name, tech, fratio))

            with open(sfname, 'wb') as f:
                f.writelines(slines)

    def __writeData(self):
        sys = SymmetricSystem(budget={'power':self._power,'area':self._area})

        for t in self._tech_nodes:
            for fratio in self._f_ratio:
                app = Application(fratio)

                # IO Core
                sys.set_core_prop(type='IO', tech=t)
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
                sys.set_core_prop(type='O3', tech=t)
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

class Spd2Util(Plot):
    def __init__(self, 
                prefix='spd2util',
                mech='ITRS'):

        Plot.__init__(self)
        self.prefix = "spd2util"
        self.mech = mech

        self.area = 500
        self.power = 200

        self.samples = 100
        self.dvfs_simple = True

        #self.tech_list = [45, 32, 22, 16, 11, 8]
        self.tech_list = [45]
        self.pr_list = [0.1, 0.5, 0.8, 0.9, 0.99]
        self.mr_list = [0, 0.2, 0.4, 0.6, 0.8]

        self.outdir = os.path.join(HOME_DIR,'speedup_for_kevin')

    
    def __figname(self):
        return '-'.join([self.prefix,str(self.area),str(self.power),self.mech,
                         'simple' if self.dvfs_simple else 'real'])

    def plot(self):
        sys = SymmetricSystem(budget={'power':self.power, 'area':self.area},
                             core=Core(dvfs_simple=self.dvfs_simple, mech=self.mech))
        apps = dict((pr, Application(f=pr)) for pr in self.pr_list)

        fig = plt.figure(figsize=(5,4))
        fig.suptitle(r'%d$mm^2$, %d$watts$, 45nm' % (self.area, self.power),
                    y=0.99)
        #adjustprops = dict(left=0.05, bottom=0.02, right=0.97, top=0.96, wspace=0.2, hspace=0.2)
        #fig.subplots_adjust(**adjustprops)
        fig_index = 1
        for t in self.tech_list:
            #for type in ['IO','O3']:
            for type in ['IO']:
                sys.set_core_prop(type=type, tech=t)

                step = (sys.util_max-sys.util_min)/self.samples

                #axes = fig.add_subplot(6,2,fig_index)
                axes = fig.add_subplot(111)

                utils = []
                for i in range(self.samples):
                    util_ratio = sys.util_min + i*step
                    utils.append(util_ratio)

                for pr in self.pr_list:
                    perfs = []
                    for util in utils:
                        sys.util_ratio = util
                        perfs.append(sys.speedup(apps[pr]))
                    axes.plot(utils, perfs)
                #axes.set_title('%dnm-%s' %(t, type), size='small')
                axes.set_xlim(0,1.1)
                axes.set_xlabel('Chip Utilization')
                axes.set_ylabel('Speedup')
                for label in axes.xaxis.get_ticklabels():
                    label.set_fontsize('small')
                for label in axes.yaxis.get_ticklabels():
                    label.set_fontsize('small')

                axes.legend(axes.lines, [r'$\rho=%g$' % pr for pr in self.pr_list], 'upper left', 
                            prop=dict(size='x-small'))
                fig_index = fig_index + 1


        filename = self.__figname() + '.' + self.format
        fullname = os.path.join(self.outdir,filename)
        fig.savefig(fullname)

class Spd2Util2(Plot):
    def __init__(self, 
                prefix='spd2util',
                mech='ITRS'):

        Plot.__init__(self)
        self.prefix = "spd2util"
        self.mech = mech

        self.area = 500
        self.power = 200

        self.samples = 100
        self.dvfs_simple = True

        #self.tech_list = [45, 32, 22, 16, 11, 8]
        self.tech_list = [45]
        self.pr_list = [0.1, 0.5, 0.8, 0.9, 0.99]
        self.mr_list = [0, 0.2, 0.4, 0.6, 0.8]
        self.v_list = [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]

        self.outdir = os.path.join(HOME_DIR,'speedup_for_kevin')

    
    def __figname(self):
        return '-'.join([self.prefix,str(self.area),str(self.power),self.mech,
                         'simple' if self.dvfs_simple else 'real'])

    def plot(self):
        sys = SymmetricSystem2(power=self.power, area=self.area,
                             core=Core(dvfs_simple=self.dvfs_simple, mech=self.mech))
        apps = dict((pr, Application(f=pr)) for pr in self.pr_list)

        fig = plt.figure(figsize=(5,4))
        fig.suptitle(r'%d$mm^2$, %d$watts$, 45nm' % (self.area, self.power),
                    y=0.99)
        #adjustprops = dict(left=0.05, bottom=0.02, right=0.97, top=0.96, wspace=0.2, hspace=0.2)
        #fig.subplots_adjust(**adjustprops)
        fig_index = 1
        for t in self.tech_list:
            #for type in ['IO','O3']:
            for type in ['IO']:
                sys.set_core_prop(type=type, tech=t)

                #step = (sys.util_max-sys.util_min)/self.samples

                #axes = fig.add_subplot(6,2,fig_index)
                axes = fig.add_subplot(111)
                axes_util = axes.twinx()

                utils = []
                get_util = True

                for pr in self.pr_list:
                    perfs = []
                    for vsf in self.v_list :
                        sys.set_vsf(vsf)
                        if get_util :
                            utils.append(sys.get_util())
                        perfs.append(sys.perf(apps[pr]))
                    axes.plot(self.v_list, perfs)
                    if get_util :
                        get_util = False

                #axes.set_title('%dnm-%s' %(t, type), size='small')
                axes.set_xlim(0,1.1)
                axes.set_xlabel(r'Voltage scaled to $V_norm$')
                axes.set_ylabel('Speedup')
                for label in axes.xaxis.get_ticklabels():
                    label.set_fontsize('small')
                for label in axes.yaxis.get_ticklabels():
                    label.set_fontsize('small')

                axes_util.plot(self.v_list, utils)
                for label in axes_util.yaxis.get_ticklabels():
                    label.set_fontsize('small')


                axes.legend(axes.lines, [r'$\rho=%g$' % pr for pr in self.pr_list], 'upper left', 
                            prop=dict(size='x-small'))
                fig_index = fig_index + 1


        filename = self.__figname() + '.' + self.format
        fullname = os.path.join(self.outdir,filename)
        fig.savefig(fullname)

class Spd2Util3(Plot):
    def __init__(self, 
                prefix='spd2util',
                mech='ITRS'):

        Plot.__init__(self)
        self.prefix = "spd2util"
        self.mech = mech

        self.area = 500
        self.power = 200

        self.samples = 100
        self.dvfs_simple = True

        #self.tech_list = [45, 32, 22, 16, 11, 8]
        self.tech_list = [45]
        self.pr_list = [0.1, 0.5, 0.8, 0.9, 0.99]
        self.mr_list = [0, 0.2, 0.4, 0.6, 0.8]
        self.v_list = [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]

        self.outdir = os.path.join(HOME_DIR,'speedup_for_kevin')

    
    def __figname(self):
        return '-'.join([self.prefix,str(self.area),str(self.power),self.mech,
                         'simple' if self.dvfs_simple else 'real'])

    def plot(self):
        sys = SymmetricSystem3(power=self.power, area=self.area)
        apps = dict((pr, Application(f=pr)) for pr in self.pr_list)

        fig = plt.figure(figsize=(5,4))
        fig.suptitle(r'%d$mm^2$, %d$watts$, 45nm' % (self.area, self.power),
                    y=0.99)
        #adjustprops = dict(left=0.05, bottom=0.02, right=0.97, top=0.96, wspace=0.2, hspace=0.2)
        #fig.subplots_adjust(**adjustprops)
        fig_index = 1


        axes = fig.add_subplot(111)
        axes_util = axes.twinx()

        utils = []
        get_util = True

        for pr in self.pr_list:
            perfs = []
            for vsf in self.v_list :
                sys.set_vsf(vsf)
                if get_util :
                    utils.append(sys.get_util())
                perfs.append(sys.perf(apps[pr]))
            axes.plot(self.v_list, perfs)
            if get_util :
                get_util = False

        #axes.set_title('%dnm-%s' %(t, type), size='small')
        axes.set_xlim(0,1.1)
        axes.set_xlabel(r'Voltage scaled to $V_norm$')
        axes.set_ylabel('Speedup')
        for label in axes.xaxis.get_ticklabels():
            label.set_fontsize('small')
        for label in axes.yaxis.get_ticklabels():
            label.set_fontsize('small')

        axes_util.plot(self.v_list, utils, '--')
        axes_util.set_ylabel('Utilization')
        for label in axes_util.yaxis.get_ticklabels():
            label.set_fontsize('small')


        axes.legend(axes.lines, [r'$\rho=%g$' % pr for pr in self.pr_list], 'upper left', 
                    prop=dict(size='x-small'))


        filename = self.__figname() + '.' + self.format
        fullname = os.path.join(self.outdir,filename)
        fig.savefig(fullname)


def main():
    p = Spd2Util3()
    p.format='png'
    for power,area in [(80,500)]:
    #for power,area in [(125,111),(200,500),(125,200)]:
        p.power=power
        p.area=area
        #for mech in ['ITRS', 'CONS']:
        for mech in ['ITRS']:
            p.mech=mech
            for dvfs_simple in [False]:
            #for dvfs_simple in [True, False]:
                p.dvfs_simple = dvfs_simple
                p.plot()


if __name__ == '__main__':
    main()

    
    
    
    
    
    
    
