from Plot import Matplot
from model.Application import Application as App
from model.System import System2
from model.Core import Core
import matplotlib.pyplot as plt

def plotPerf2Cores(sys_area, sys_power, ctech, ctype, cmech, app=App(f=0.99)):
    sys = System2()
    core = Core(tech=ctech, ctype=ctype, mech=cmech)
    sys.set_sys_prop(area=sys_area, power=sys_power, core=core)

    cnum_max = sys.get_core_num()

    cnumList = range(1, cnum_max+1)
    #cnumList = (1002,1003,1004,1005,1006,1007)
    perfList = []
    vddList = []
    utilList = []
    for cnum in cnumList:
        #print cnum
        r = sys.perf_by_cnum(cnum, app)
        perfList.append(r['perf'])
        vddList.append(r['vdd'])
        utilList.append(r['util'])

    fig = plt.figure()
    axes = fig.add_subplot(111)

    axes.plot(cnumList, perfList)
    axes.set_xlabel('Number of active cores')
    axes.set_ylabel('Performance')
    axes.grid(True)

    fig.savefig("%dmm_%dw_%dnm_%s_%s.png" % (sys_area, sys_power, ctech, ctype, cmech))
    #for (cnum, perf, vdd, util) in zip(cnumList,perfList,vddList, utilList):
        #print 'cnum:%d\tperf:%f\tvdd:%f\tutil:%f' % (cnum, perf, vdd, util)


if __name__ == '__main__':
    areaList = (200,)
    powerList = (100,)
    ctechList = (45,32,22,16)
    ctypeList = ('IO',)
    cmechList = ('ITRS','LP','HKMGS')

    for area in areaList:
        for power in powerList:
            for ctech in ctechList:
                for ctype in ctypeList:
                    for cmech in cmechList:
                        plotPerf2Cores(area, power, ctech, ctype, cmech)

