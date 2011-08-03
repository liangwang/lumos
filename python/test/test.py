#!/usr/bin/env python

HOME_DIR='/home/lw2aw/eclipse_ws/analytical/python'

import sys
sys.path.append(HOME_DIR)

from model.Core import *
from model.SymmetricSystem import *
from model.Application import *

from plot.Plot import *

import matplotlib.pyplot as plt


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

def main():
    sys = SymmetricSystem(budget={'power':80, 'area':350},
                         core=Core(dvfs_simple=False, mech='ITRS'))
    apps = dict((pr, Application(f=pr)) for pr in [0.1,0.99])
    sys.util_ratio = 0.3
    sys.speedup(apps[0.1])
    #sys.speedup(apps[0.99])
    sys.util_ratio = 0.8
    sys.speedup(apps[0.1])
    #sys.speedup(apps[0.99])
    sys.util_ratio = 0.99
    sys.speedup(apps[0.1])


if __name__ == '__main__':
    main()

    
    
    
    
    
    
    
