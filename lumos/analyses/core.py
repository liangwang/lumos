#!/usr/bin/env python
"""
   A simple analysis on voltage-frequency scaling. This analysis also
   plots power (dynamic and static) scaled to the supply voltage.

"""

import numpy as np
import matplotlib.pyplot as plt
from os.path import join as joinpath
import os
import csv
from lumos.model.core import IOCore, O3Core
from lumos.model.system import VMIN,VMAX
import analysis

ANALYSIS_NAME = 'core'
HOME = joinpath(analysis.HOME, ANALYSIS_NAME)
FIG_DIR,DATA_DIR = analysis.make_ws_dirs(ANALYSIS_NAME)

def analyze(ctype, mech, tech, variation, ofile=None):
    if ctype == 'IO':
        core = IOCore(mech=mech, tech=tech, pv=variation)
    elif ctype == 'O3':
        core = O3Core(mech=mech, tech=tech, pv=variation)

    vstep = 0.05
    num = int((VMAX-VMIN)/vstep)+1
    vlist =np.linspace(VMIN, VMAX, num)
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
            analyze(ctype='IO', mech=mech, tech=tech, variation=False,
                     ofile = odf)
            opf = joinpath(FIG_DIR, 'power_%s_%d.png' % (mech, tech))
            plot_power(ifile=odf, ofile=opf)
            opf = joinpath(FIG_DIR, 'freq_%s_%d.png' % (mech, tech))
            plot_freq(ifile=odf, ofile=opf)
