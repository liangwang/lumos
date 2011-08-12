'''
Created on Aug 11, 2011

@author: liang
'''
from Plot import Matplot
from model import System2
import matplotlib.pyplot as plt
from os.path import join as joinpath

class PerfScalePlot(Matplot):
    '''
    Performance scaling to voltage
    '''


    def __init__(self, power):
        '''
        Constructor
        '''
        Matplot.__init__(self)
        
        self.figname = 'perf_%dw' % (power)
        self.format = 'pdf'
        
        self.power = power
        
    def do_plot(self):
        v = [(0.1*i) for i in range(2,11)]
        area_list = (100, 200, 300, 400, 500, 1000, 2000, 3000, 4000)
        sys = System2.System2()
        index = 0
 
        for area in area_list:
            sys.build(area=area,power=self.power)
            s = sys.get_speedup(v)
    
            idstr = '%02d' % (index,)
            figname = '_'.join([idstr, self.figname, str(area)+'mm'])

            index = index + 1
    
            fig = plt.figure(figsize=(9.5,6.9))
            fig.suptitle('%dmm, 80w' % area)
            axes = fig.add_subplot(111)
            axes.plot(v,s)
            axes.set_ylim(0,55)
        
            fname = '.'.join([figname,self.format])
            fullname = joinpath(self.outdir, fname)
            fig.savefig(fullname)
            
if __name__=='__main__':
    p = PerfScalePlot(160)
    p.do_plot()