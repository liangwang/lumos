#!/usr/bin/env python
# encoding: utf-8

import cPickle as pickle
from os.path import join as joinpath

from model import system, core
from model.application import App

import analyses.analysis as analysis
ANALYSIS_NAME = 'dimsi_deriv'
HOME = joinpath(analysis.HOME, ANALYSIS_NAME)
FIG_DIR, DATA_DIR = analysis.make_ws_dirs(ANALYSIS_NAME)

def anal():
    sys = system.SymSys(area=200, power=120)
    sys.set_sys_prop(core=core.Core(tech=16, ctype='IO', mech='HKMGS'))
    cnum_max = sys.get_core_numm()
    perf_list = [ sys.perf_by_cnum(cnum, app=App(f=1))['perf'] for cnum in xrange(1, cnum_max+1)]

    deriv_list = [ perf_list[i+1]-perf_list[i] for i in xrange(cnum_max-1) ]

    dfn = joinpath(DATA_DIR, ('%s.pypkl' % ANALYSIS_NAME))
    with open(dfn, 'wb') as f:
        pickle.dump(cnum_max, f)
        pickle.dump(perf_list, f)
        pickle.dump(deriv_list, f)

def plot():
    dfn = joinpath(DATA_DIR, ('%s.pypkl' % ANALYSIS_NAME))
    with open(dfn, 'rb') as f:
        cnum_max = pickle.load(f)
        perf_list = pickle.load(f)
        deriv_list = pickle.load(f)

    cnum_list = range(1, cnum_max+1)
    deriv_list.append(deriv_list[-1])
    analysis.plot_data_nomarker(cnum_list, [perf_list,],
            xlabel='Number of cores',
            ylabel='Speedup',
            figdir=FIG_DIR,
            figsize=(6,4.5),
            ofn='%s.pdf' % ANALYSIS_NAME)

if __name__ == '__main__':
    anal()
    plot()





