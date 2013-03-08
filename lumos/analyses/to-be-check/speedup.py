import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
from os.path import join as joinpath
import os
import csv
from model.core import Core
from model.tech import PTMScale
import model.system
from model.system import HomogSys
import analysis
DATA_DIR=joinpath(analysis.DATA_DIR, 'speedup')
FIG_DIR=joinpath(analysis.FIG_DIR, 'speedup')

try:
    os.makedirs(DATA_DIR)
except OSError:
    if os.path.isdir(DATA_DIR):
        pass
    else:
        raise

try:
    os.makedirs(FIG_DIR)
except OSError:
    if os.path.isdir(FIG_DIR):
        pass
    else:
        raise

# to be developed
def analyze(ctype, mech, tech, variation,
           ofile=None):
    sys = HomogSys()
    core = Core(ctype=ctype, mech=mech,
                tech=tech, variation=variation)

    vmin=model.system.VMIN
    vmax=model.system.VMAX
    vstep = 0.05
    num = int((vmax-vmin)/vstep)+1
    vlist =np.linspace(vmin, vmax, num)
    result = core.scale_with_vlist(vlist)

    if ofile is None:
        ofile = joinpath(DATA_DIR, 'speedup.dat')

    with open(ofile, 'w') as f:
        of = csv.writer(f,delimiter=':')
        of.writerows(zip(vlist, result['freq'], result['dp'], result['sp']))

def plot_freq(ifile=None, ofile=None, has_title=False):
    if ifile is None:
        ifile = joinpath(DATA_DIR, 'core.dat')

    with open(ifile, 'r') as f:
        inf = csv.reader(f, delimiter=':')
        col1, col2, col3, col4 = zip(*inf)

    vlist = [float(x) for x in col1]
    freqList = [float(x) for x in col2]

    fig = plt.figure()
    axes = fig.add_subplot(111)
    axes.plot(vlist, freqList)
    axes.set_xlabel('Supply Voltage (V)')
    axes.set_ylabel('Frequency (GHz)')
    axes.set_yscale('log')

    if has_title:
        axes.set_title('Frequency Scaling')

    if ofile is None:
        ofile = joinpath(FIG_DIR, 'core_freq.png')

    fig.savefig(ofile)

def plot_power(ifile=None, ofile=None, has_title=False):
    if ifile is None:
        ifile = joinpath(DATA_DIR, 'core.dat')

    with open(ifile, 'r') as f:
        inf = csv.reader(f, delimiter=':')
        col1, col2, col3, col4 = zip(*inf)

    vlist = [float(x) for x in col1]
    dpList = [float(x) for x in col3]
    spList = [float(x) for x in col4]

    fig = plt.figure()
    axes = fig.add_subplot(111)
    axes.plot(vlist, dpList, vlist, spList)
    axes.set_xlabel('Supply Voltage (V)')
    axes.set_ylabel('Power (W)')
    axes.set_yscale('log')

    if has_title:
        axes.set_title('Power Scaling')

    if ofile is None:
        ofile = joinpath(FIG_DIR, 'core_power.png')

    fig.savefig(ofile)

def plot_speedup(ifile=None, ofile=None, has_title=False):

    areaList = (400,)
    powerList = (100,)
    ctechList = (45,32,22,16)
    cmechList = ('HKMGS', )

    perList = (100, 95, 90, 85, 80, 75, 70, 65, 60, 55, 50)

    sys = HomogSys()
    for area in areaList:
        for power in powerList:
            sys.set_sys_prop(area=area, power=power, core=Core())

            for mech in cmechList:
                fig = plt.figure(figsize=(8,6))
                axes = fig.add_subplot(111)
                xList = range(1, len(perList)+1)
                for ctech in ctechList:
                    sys.set_core_prop(tech=ctech, ctype='IO', mech=mech)

                    perfList = []
                    for percentage in perList:
                        vnom = PTMScale.vdd[mech][ctech]
                        ret = sys.perf_by_vdd(vnom*percentage/100)
                        perfList.append(ret['perf'])

                    axes.plot(xList, perfList)

                majorLocator=MultipleLocator()
                axes.set_xlim(0.5, len(perList)+0.5)
                axes.set_xlabel('Supply voltage relative to norminal Vdd (%)')
                axes.set_ylabel('Speedup normalized to a single core at 45nm')
                axes.xaxis.set_major_locator(majorLocator)
                axes.set_xticklabels(perList)
                legend_labels = [ ('%dnm' % tech) for tech in ctechList ]
                axes.legend(axes.lines, legend_labels, loc='upper right')
                #ofn = 'speedup_%s_%dw_%dmm.png' % (mech, power, area)
                ofn = 'speedup_%s_%dw_%dmm.pdf' % (mech, power, area)
                ofile = joinpath(FIG_DIR, ofn)
                fig.savefig(ofile)



if __name__ == '__main__':
    #analyze(ctype='IO', mech='LP', tech=45, variation=False)
    #for mech in ('LP', 'HKMGS'):
        #for tech in (45, 32, 22, 16):
            #odf = joinpath(DATA_DIR, '%s_%d.dat' % (mech, tech))
            ##analyze(ctype='IO', mech=mech, tech=tech, variation=False,
                     ##ofile = odf)
            ##opf = joinpath(FIG_DIR, 'power_%s_%d.png' % (mech, tech))
            ##plot_power(ifile=odf, ofile=opf)
            #opf = joinpath(FIG_DIR, 'freq_%s_%d.png' % (mech, tech))
            #plot_freq(ifile=odf, ofile=opf)
    plot_speedup()


