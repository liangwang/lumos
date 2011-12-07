'''
Created on Aug 12, 2011

@author: lw2aw
'''

from Plot import Matplot
from model.System import System
import matplotlib.pyplot as plt
from os.path import join as joinpath

class AreaPlot(Matplot):
    '''
    Maximum speedup scaled to area
    '''


    def __init__(self, power, prefix='area'):
        '''
        Constructor
        '''
        Matplot.__init__(self)

        self.format = 'pdf'

        self.power = power
        self.prefix = prefix

        self.sys = System()
        

    def do_plot(self):
        area_list = range(100,5000,100)

        self.sys.set_prop(power=self.power)
        speedup = []
        util = []
            
        for area in area_list:
            self.sys.set_prop(area=area)
            #sys.probe()
            self.sys.probe2()
            speedup.append(self.sys.speedup)
            util.append(self.sys.util)

        fig = plt.figure()
        ax1 = fig.add_subplot(111) # speedup scale
        ax2 = ax1.twinx() # utilization scale

        ax1.set_title('Area scaling (TDP=%dW)' % self.sys.power)
        ax1.set_ylabel('Speedup over single core running at nominal voltage(1v)')
        ax2.set_ylabel('Utilization')

        l_speedup, = ax1.plot(area_list, speedup,'b')
        l_util, = ax2.plot(area_list, util,'r')

    #    ax1.set_ylim(0,55)
        ax2.set_ylim(0,1.1)

        lines = [l_speedup, l_util]
        ax1.legend(lines, ['Speedup', 'Utilization'], loc="lower right")
        ax1.grid(True)

        figname = '%s_%dw' % (self.prefix, self.power)
        fname = '.'.join([figname,self.format])
        fullname = joinpath(self.outdir, fname)
        fig.savefig(fullname)

if __name__ == '__main__':
    plot = AreaPlot(power=80)
    plot.set_prop(format='png')
    index = 0
    for p in (80,120,160,200):
        prefix = 'area_%02d' % (index,)
        plot.set_prop(prefix=prefix,power=p)
        plot.do_plot()
        
        index = index + 1


### reference
#def area_scaling_plot():
    #area_list = range(100,5000,100)
    #sys = System()
    #sys.set_prop(tech=32)
    #for power in (80, 120, 160, 200):
        #sys.set_prop(power=power)
        #format = 'png'
        #speedup = []
        #util = []
        
        #for area in area_list:
            #sys.set_prop(area=area)
            #sys.probe()
            #speedup.append(sys.speedup)
            #util.append(sys.util)

        #fig = plt.figure()
        #ax1 = fig.add_subplot(111) # speedup scale
        #ax2 = ax1.twinx() # utilization scale

        #ax1.set_title('Area scaling (TDP=%dW)' % sys.power)
        #ax1.set_ylabel('Speedup over single core running at nominal voltage(1v)')
        #ax2.set_ylabel('Utilization')

        #l_speedup, = ax1.plot(area_list, speedup,'b')
        #l_util, = ax2.plot(area_list, util,'r')

    ##    ax1.set_ylim(0,55)
        #ax2.set_ylim(0,1.1)

        #lines = [l_speedup, l_util]
        #ax1.legend(lines, ['Speedup', 'Utilization'], loc="lower right")
        #ax1.grid(True)
        #fig.savefig('area_scaling_%dw.%s' % (sys.power,format))

