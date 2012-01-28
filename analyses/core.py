import numpy as np
import matplotlib.pyplot as plt
from os.path import join as joinpath
import os
import csv
from model.core import Core
import model.system
import analysis
DATA_DIR=joinpath(analysis.DATA_DIR, 'core')
FIG_DIR=joinpath(analysis.FIG_DIR, 'core')

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

def analyze(ctype, mech, tech, variation,
           ofile=None):
    core = Core(ctype=ctype, mech=mech,
                tech=tech, variation=variation)

    vmin=model.system.VMIN
    vmax=model.system.VMAX
    vstep = 0.05
    num = int((vmax-vmin)/vstep)+1
    vlist =np.linspace(vmin, vmax, num)
    result = core.scale_with_vlist(vlist)

    if ofile is None:
        ofile = joinpath(DATA_DIR, 'core.dat')

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

    
if __name__ == '__main__':
    #analyze(ctype='IO', mech='LP', tech=45, variation=False)
    for mech in ('LP', 'HKMGS'):
        for tech in (45, 32, 22, 16):
            odf = joinpath(DATA_DIR, '%s_%d.dat' % (mech, tech))
            #analyze(ctype='IO', mech=mech, tech=tech, variation=False,
                     #ofile = odf)
            #opf = joinpath(FIG_DIR, 'power_%s_%d.png' % (mech, tech))
            #plot_power(ifile=odf, ofile=opf)
            opf = joinpath(FIG_DIR, 'freq_%s_%d.png' % (mech, tech))
            plot_freq(ifile=odf, ofile=opf)


