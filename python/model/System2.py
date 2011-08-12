#!/usr/bin/env python

from Core import Core45nmCon
import matplotlib.pyplot as plt

class System2(object):
    def __init__(self):
        self.numIO = 0
        self.numO3 = 0
        self.area = 0
        self.power= 0
        self.tech = 45

        self.active_num = 0
        self.perf_max = 0
        self.speedup = 0
        self.util = 0
        self.volt = 0

    def set_prop(self, **kwargs):
        for k,v in kwargs.items():
            k=k.lower()
            setattr(self, k, v)

    def build(self,type='sym-io',area=200,power=80,tech=45):
        self.area = area
        self.power = power
        self.tech = tech

        #if type=='sym-io':
            #iocore = Core45nmCon()
            #self.numIO = area / iocore.area


    def probe(self):
        core = Core45nmCon()

        para_ratio = 0.99

        perf_base = core.perf0 * core.freq
        perf_max = perf_base
        core_num = min(self.area/core.area, self.power/core.power)
        util = core_num*core.area/self.area
        volt = core.volt

        for vsf in [(1-0.001*i) for i in range(1,1000)]:
            core.dvfs(vsf)
            active_num = min(self.area/core.area, self.power/core.power)
            perf = 1/ ( (1-para_ratio)/perf_base + para_ratio/(active_num*core.perf0*core.freq))

            if perf > perf_max:
                perf_max = perf
                core_num = active_num
                util = core_num*core.area/self.area
                volt = core.volt
            else :
                break

        self.active_num = core_num
        self.perf_max = perf_max
        self.speedup = perf_max / perf_base
        self.util = util
        self.volt = volt

    def get_speedup(self, vsf_list):
        core = Core45nmCon()

        para_ratio = 0.99

        perf_base = core.perf0 * core.freq

        perf_list = []
        speedup_list = []

        for vsf in vsf_list:
            core.dvfs(vsf)
            active_num = min(self.area/core.area, self.power/core.power)
            perf = 1/ ((1-para_ratio)/perf_base + para_ratio/(active_num*core.perf0*core.freq))
            speedup_list.append(perf/perf_base)

        return speedup_list
    
def voltage_scaling_plot():
    v = [(0.1*i) for i in range(2,11)]
    #area_list = [100, 500, 1000, 2000, 4000, 8000, 16000, 32000, 64000, 100000, 200000, 400000, 800000, 2000000, 4000000]
    #area_list = [100, 150, 200, 250, 300, 350, 400, 450, 500]
    area_list = (100, 200, 300, 400, 500, 1000, 2000, 3000, 4000)
    sys = System2()
    format = 'png'
    index = 0
    prefix = '160w_leakage'
    for area in area_list:
        sys.build(area=area)
        s = sys.get_speedup(v)

        idstr = '%02d' % (index,)
        figname = '_'.join([prefix,idstr,str(area)+'mm'])
#        if index < 10:
#            figname = '_'.join([prefix,'0'+str(index),str(area)+'mm'])
#        else:
#            figname = '_'.join([prefix,str(index),str(area)+'mm'])
        index = index + 1

        fig = plt.figure(figsize=(9.5,6.9))
        fig.suptitle('%dmm, 80w' % area)
        axes = fig.add_subplot(111)
        axes.plot(v,s)
        axes.set_ylim(0,55)
        fig.savefig(figname)

def area_scaling_plot():
    area_list = range(100,3000,100)
    sys = System2()
    format = 'png'
    speedup = []
    util = []
    
    for area in area_list:
        sys.build(area=area)
        sys.probe()
        speedup.append(sys.speedup)
        util.append(sys.util)

    fig = plt.figure()
    ax1 = fig.add_subplot(111) # speedup scale
    ax2 = ax1.twinx() # utilization scale

    ax1.set_title('Area scaling (TDP=%dW)' % sys.power)
    ax1.set_ylabel('Speedup over single core running at nominal voltage(1v)')
    ax2.set_ylabel('Utilization')

    l_speedup, = ax1.plot(area_list, speedup,'b')
    l_util, = ax2.plot(area_list, util,'r')

    ax1.set_ylim(0,55)
    ax2.set_ylim(0,1.1)

    lines = [l_speedup, l_util]
    ax1.legend(lines, ['Speedup', 'Utilization'], loc="lower right")
    ax1.grid(True)
    fig.savefig('area_scaling_%dw' % sys.power)

if __name__ == '__main__':
#    voltage_scaling_plot()
    area_scaling_plot()

