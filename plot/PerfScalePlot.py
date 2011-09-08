'''
Created on Aug 11, 2011

@author: liang
'''
from Plot import Matplot
from model.System import System
import matplotlib.pyplot as plt
from os.path import join as joinpath

class PerfScalePlot(Matplot):
    '''
    Performance scaling to voltage
    '''


    def __init__(self, area, power, prefix='power'):
        '''
        Constructor
        '''
        Matplot.__init__(self)
        
        self.format = 'pdf'
        
        self.power = power
        self.area = area
        self.prefix = prefix
        
        self.sys = System()

        
    def do_plot(self):
        v = [(0.05*i) for i in range(4,21)]
        
        self.sys.build(area=self.area,power=self.power)
        s = self.sys.get_speedup(v)
        
        
        fig = plt.figure(figsize=(9.5,6.9))
        fig.suptitle('%dmm, %dw' % (self.area,self.power))
        axes = fig.add_subplot(111)
        axes.plot(v,s)
#        axes.set_ylim(0,55)
        
        figname = '%dw_%s_%dmm' % (self.power, self.prefix, self.area)
        fname = '.'.join([figname,self.format])
        fullname = joinpath(self.outdir, fname)
        fig.savefig(fullname)
                            
#        area_list = (100, 200, 300, 400, 500, 1000, 2000, 3000, 4000)
#        sys = System2.System2()
#        index = 0
# 
#        for area in area_list:
#            sys.build(area=area,power=self.power)
#            s = sys.get_speedup(v)
#    
#            idstr = '%02d' % (index,)
#            figname = '_'.join([idstr, self.figname, str(area)+'mm'])
#
#            index = index + 1
#    
#            fig = plt.figure(figsize=(9.5,6.9))
#            fig.suptitle('%dmm, 80w' % area)
#            axes = fig.add_subplot(111)
#            axes.plot(v,s)
#            axes.set_ylim(0,55)
#        
#            fname = '.'.join([figname,self.format])
#            fullname = joinpath(self.outdir, fname)
#            fig.savefig(fullname)
            
if __name__=='__main__':
    plot = PerfScalePlot(100,80)
    plot.set_prop(format='png')
    index = 0
    for p in (80,120,160,200):
        plot.set_prop(power=p)
        for a in (100, 200, 300, 400, 500, 600,1000, 2000, 4000, 8000, 16000):
            prefix = '%02d_power' % (index,)
            plot.set_prop(prefix=prefix,area=a)
            plot.do_plot()
            
            index = index+1
            
