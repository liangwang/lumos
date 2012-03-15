"""
Python script use to generate figures in the final report

"""
import cPickle as pickle
import itertools
import numpy as np
import math
import matplotlib
matplotlib.use('Agg')
#import matplotlib.pyplot as plt
#import matplotlib.lines as mlines
#from matplotlib.ticker import MultipleLocator
from os.path import join as joinpath
from optparse import OptionParser
import os
from model.app import App
import model.system
from model.system import SymSys
from model.core import Core
from model.tech import PTMScale as ptmtech
from data import reader
import analysis
FIG_DIR=joinpath(analysis.FIG_DIR, 'final-report')
try:
    os.makedirs(FIG_DIR)
except OSError:
    if os.path.isdir(FIG_DIR):
        pass
    else:
        raise
DATA_DIR=joinpath(analysis.DATA_DIR, 'fina-report')
try:
    os.makedirs(DATA_DIR)
except OSError:
    if os.path.isdir(DATA_DIR):
        pass
    else:
        raise


SYS_SMALL={'area':107, 'power':33}
SYS_MEDIUM={'area':130, 'power':65}
SYS_LARGE={'area':200, 'power':120}

def speedup_by_vper(per_list, sys):
    perf_list = []
    for per in per_list:
        vnom = ptmtech.vdd[sys.core.mech][sys.core.tech]
        ret = sys.perf_by_vdd(vnom*per/100)
        perf_list.append(ret['perf'])

    return perf_list

def speedup_by_vmin(sys, var=False):
    vminr_list = (1.3, 1.2, 1.1, 0)
    tech_list = (45, 32, 22, 16)

    perf_lists = []

    for vminr in vminr_list:
        perf_list = []
        for tech in tech_list:
            sys.set_core_prop(tech=tech, pv=var)
            vmin = sys.core.vt * vminr
            ret = sys.opt_core_num(vmin=vmin)
            perf_list.append(ret['perf'])
        perf_lists.append(perf_list)

    return perf_lists
    

class PenaltyAdjustAnalysis(object):
    def __init__(self, fmt, sys_area=None, sys_power=None):
        self.prefix = 'penadj'
        self.fmt = fmt
        if sys_area:
            self.sys_area = sys_area
        if sys_power:
            self.sys_power = sys_power

        self.adjust_list = (1, 0.9, 0.5, 0.1, 0)
        self.tech_list = (45, 32, 22, 16)

    def set_sys(self, area, power):
        self.sys_area = area
        self.sys_power = power
        self.id = '%s_%dw_%dmm' % (self.prefix, power, area)

    def analyze(self):
        sys = SymSys()
        sys.set_sys_prop(area=self.sys_area, power=self.sys_power)
        sys.set_sys_prop(core=Core(ctype='IO', mech='HKMGS'))
        speed_lists = []
        for adjust in self.adjust_list:
            speed_list = []
            for ctech in self.tech_list:
                sys.set_core_prop(tech=ctech, pv=True, pen_adjust=adjust)
                ret = sys.opt_core_num()
                speed_list.append(ret['perf'])
            speed_lists.append(speed_list)
        
        dfn = joinpath(DATA_DIR, ('%s.pypkl'%self.id))
        with open(dfn, 'wb') as f:
            pickle.dump(speed_lists, f)

    def plot(self):
        dfn = joinpath(DATA_DIR, ('%s.pypkl'%self.id))
        try:
            with open(dfn, 'rb') as f:
                speed_lists = pickle.load(f)
        except IOError:
            print 'Pickle file %s.pypkl not found! No plots generated' % self.id
            return

        ofn = '%s_speedup' % self.id
        analysis.plot_series(self.tech_list, speed_lists,
                             xlabel='Technology Nodes',
                             ylabel='Speedup (normalized)',
                             legend_labels=[ ('adjust=%.1f'%a) for a in self.adjust_list],
                             legend_loc='upper left',
                             figsize=None,
                             figdir=FIG_DIR,
                             ofn='%s.%s' % (self.id, self.fmt))

class VariationImpactAnalysis(object):
    def __init__(self, fmt, tech=None):
        self.prefix = 'varimpact'
        self.fmt = fmt

        self.marker_list = ['o', 'v']

        if tech:
            self.tech = tech
            self.id = '%s_%dnm' % ( self.prefix, tech)
        else:
            self.id = '%s' % (self.prefix)


    def set_tech(self, tech):
        self.tech = tech
        self.id = '%s_%dnm' % ( self.prefix, tech)

    def analyze(self):

        ttype = 'HKMGS'
        data_norm = reader.readNormData('adder', ttype, self.tech)
        data_mc = reader.readMCData('adder', ttype, self.tech)
        yerr_min = data_norm['freq'] - data_mc['freq_3sigma']
        x_list_hp = data_norm['vdd'][-14:]
        y_list_hp = [data_norm['freq'][-14:]/1e6, data_mc['freq_3sigma'][-14:]/1e6]

        ttype = 'LP'
        data_norm = reader.readNormData('adder', ttype, self.tech)
        data_mc = reader.readMCData('adder', ttype, self.tech)
        yerr_min = data_norm['freq'] - data_mc['freq_3sigma']
        x_list_lp = data_norm['vdd'][-14:]
        y_list_lp = [data_norm['freq'][-14:]/1e6, data_mc['freq_3sigma'][-14:]/1e6]

        dfn = joinpath(DATA_DIR, ('%s.pypkl'%self.id))
        with open(dfn, 'wb') as f:
            pickle.dump(x_list_hp, f)
            pickle.dump(y_list_hp, f)
            pickle.dump(x_list_lp, f)
            pickle.dump(y_list_lp, f)

    def plot(self):
        dfn = joinpath(DATA_DIR, ('%s.pypkl'%self.id))
        try:
            with open(dfn, 'rb') as f:
                x_list_hp = pickle.load(f)
                y_list_hp = pickle.load(f)
                x_list_lp = pickle.load(f)
                y_list_lp = pickle.load(f)
        except IOError:
            print 'Pickle file %s.pypkl not found! No plots generated' % self.id
            return
        
        def annotate_hp(axes, figure):
            textstr = '$V_t=%.3fV$' % ptmtech.vt['HKMGS'][self.tech]
            axes.text(0.3, 5e3, textstr,  fontsize=14,verticalalignment='top')
            axes.axvline(x=ptmtech.vt['HKMGS'][self.tech], ymin=0.1, ymax=0.9,
                         ls='--', c='black', lw=1, alpha=0.7)

            
            #props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
            textstr = '$V_{nom}=%.1fV$' % ptmtech.vdd['HKMGS'][self.tech]
            axes.text(0.72, 10, textstr,  fontsize=14,verticalalignment='top')
            axes.axvline(x=ptmtech.vdd['HKMGS'][self.tech], ymin=0.1, ymax=0.9,
                         ls='--', c='black', lw=1, alpha=0.7)
        analysis.plot_data(x_list_hp, y_list_hp,
                  xlabel = 'Supply voltage (V)',
                  ylabel = 'Frequency in log-scale (MHz)',
                  xlim = (0.25, 1.15),
                  ylog = True,
                  xgrid = False,
                  legend_labels = ['Normal', 'VarMin'],
                  legend_loc = 'lower right',
                  figsize=(6,4.5),
                  cb_func = annotate_hp,
                  figdir = FIG_DIR,
                  ofn = '%s_HKMGS.%s' % (self.id, self.fmt))

        def annotate_lp(axes, figure):
            textstr = '$V_t=%.3fV$' % ptmtech.vt['LP'][self.tech]
            axes.text(0.5, 5e-4, textstr,  fontsize=14,verticalalignment='top')
            axes.axvline(x=ptmtech.vt['LP'][self.tech], 
                         ls='--', c='black', lw=1, alpha=0.4)

            
            #props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
            textstr = '$V_{nom}=%.1fV$' % ptmtech.vdd['LP'][self.tech]
            axes.text(0.92, 5, textstr,  fontsize=14,verticalalignment='top')
            axes.axvline(x=ptmtech.vdd['LP'][self.tech], 
                         ls='--', c='black', lw=1, alpha=0.4)

        analysis.plot_data(x_list_lp, y_list_lp,
                  xlabel = 'Supply voltage (V)',
                  ylabel = 'Frequency in log-scale (MHz)',
                  xlim = (0.25, 1.15),
                  ylog = True,
                  xgrid = False,
                  legend_labels = ['Normal', 'VarMin'],
                  legend_loc = 'lower right',
                  figsize=(6,4.5),
                  cb_func = annotate_lp,
                  figdir = FIG_DIR,
                  ofn = '%s_LP.%s' % (self.id, self.fmt))

class MainAnalyzer(object):

    def __init__(self):

        self.fmt = 'pdf'



    def analyze_var_penalty(self):
        core = Core(mech='HKMGS', ctype='IO', pv=True)
        for tech in (45, 32, 22, 16):
            core.config(tech=tech)
            print core.var_penalty

    def ntc_speedup(self):
        areaList = (SYS_SMALL['area'], SYS_MEDIUM['area'], SYS_LARGE['area'])
        powerList = (SYS_SMALL['power'], SYS_MEDIUM['power'], SYS_LARGE['area'])
        ctechList = (45,16)
        cmechList = ('HKMGS', )

        #perList = (100, 95, 90, 85, 80, 75, 70, 65, 60, 55, 50)
        per_list = range(130, 49, -5)

        ylabel = 'Speedup (normalized)'

        sys = SymSys()

        # 45nm without variation
        def annotate45(axes, figure):
            textstr = '$V_{nom}=%.1fV$\n$V_t=%.3fV$' % (ptmtech.vdd['HKMGS'][45], ptmtech.vt['HKMGS'][45])
            props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
            axes.text(0.75, 0.95, textstr, transform=axes.transAxes, fontsize=18,verticalalignment='top',bbox=props)

        sys.set_sys_prop(core=Core(tech=45, ctype='IO',mech='HKMGS'))

        y_lists = []
        sys.set_sys_prop(area=SYS_SMALL['area'], power=SYS_SMALL['power'])
        y_lists.append(speedup_by_vper(per_list,sys))
        sys.set_sys_prop(area=SYS_MEDIUM['area'], power=SYS_MEDIUM['power'])
        y_lists.append(speedup_by_vper(per_list,sys))
        sys.set_sys_prop(area=SYS_LARGE['area'], power=SYS_LARGE['power'])
        y_lists.append(speedup_by_vper(per_list,sys))

        ofn = 'ntc_speedup_45nm.%s' % (self.fmt,)
        ofile = joinpath(FIG_DIR, ofn)

        analysis.plot_series(per_list, y_lists,
                    xlabel = 'Supply voltage relative to nominal Vdd (%)',
                    ylabel = ylabel,
                    legend_labels=['small', 'medium', 'large'],
                    #legend_labels=['normal', 'large'],
                    ylim = (0,20),
                    legend_loc='upper left',
                    figsize=(8,4.5),
                    cb_func = annotate45,
                  figdir = FIG_DIR,
                    ofn=ofn)

        # 45nm with variation
        sys.set_sys_prop(core=Core(tech=45, ctype='IO',mech='HKMGS', pv=True))

        y_lists = []
        sys.set_sys_prop(area=SYS_SMALL['area'], power=SYS_SMALL['power'])
        y_lists.append(speedup_by_vper(per_list,sys))
        sys.set_sys_prop(area=SYS_MEDIUM['area'], power=SYS_MEDIUM['power'])
        y_lists.append(speedup_by_vper(per_list,sys))
        sys.set_sys_prop(area=SYS_LARGE['area'], power=SYS_LARGE['power'])
        y_lists.append(speedup_by_vper(per_list,sys))

        ofn = 'ntc_speedup_var_45nm.%s' % (self.fmt,)
        ofile = joinpath(FIG_DIR, ofn)

        analysis.plot_series(per_list, y_lists,
                    xlabel = 'Supply voltage relative to nominal Vdd (%)',
                    ylabel = ylabel,
                    legend_labels=['small', 'medium', 'large'],
                    #legend_labels=['normal', 'large'],
                    ylim = (0,20),
                    legend_loc='upper left',
                    figsize=(8,4.5),
                    cb_func=annotate45,
                  figdir = FIG_DIR,
                    ofn=ofn)

        # 16nm without variation
        def annotate16(axes, figure):
            textstr = '$V_{nom}=%.1fV$\n$V_t=%.3fV$' % (ptmtech.vdd['HKMGS'][16], ptmtech.vt['HKMGS'][16])
            props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
            axes.text(0.05, 0.95, textstr, transform=axes.transAxes, fontsize=18,verticalalignment='top',bbox=props)

        sys.set_sys_prop(core=Core(tech=16, ctype='IO',mech='HKMGS'))
        y_lists = []
        sys.set_sys_prop(area=SYS_SMALL['area'], power=SYS_SMALL['power'])
        y_lists.append(speedup_by_vper(per_list,sys))
        sys.set_sys_prop(area=SYS_MEDIUM['area'], power=SYS_MEDIUM['power'])
        y_lists.append(speedup_by_vper(per_list,sys))
        sys.set_sys_prop(area=SYS_LARGE['area'], power=SYS_LARGE['power'])
        y_lists.append(speedup_by_vper(per_list,sys))

        ofn = 'ntc_speedup_16nm.%s' % (self.fmt,)
        ofile = joinpath(FIG_DIR, ofn)

        analysis.plot_series(per_list, y_lists,
                    xlabel = 'Supply voltage relative to nominal Vdd (%)',
                    ylabel = ylabel,
                    legend_labels=['small', 'medium', 'large'],
                    #legend_labels=['normal', 'large'],
                    ylim = (0, 70),
                    legend_loc='upper right',
                    figsize=(8,4.5),
                    cb_func = annotate16,
                  figdir = FIG_DIR,
                    ofn=ofn)

        # 16nm with variation
        sys.set_sys_prop(core=Core(tech=16, ctype='IO',mech='HKMGS', pv=True))
        y_lists = []
        sys.set_sys_prop(area=SYS_SMALL['area'], power=SYS_SMALL['power'])
        y_lists.append(speedup_by_vper(per_list,sys))
        sys.set_sys_prop(area=SYS_MEDIUM['area'], power=SYS_MEDIUM['power'])
        y_lists.append(speedup_by_vper(per_list,sys))
        sys.set_sys_prop(area=SYS_LARGE['area'], power=SYS_LARGE['power'])
        y_lists.append(speedup_by_vper(per_list,sys))

        ofn = 'ntc_speedup_var_16nm.%s' % (self.fmt,)
        ofile = joinpath(FIG_DIR, ofn)

        analysis.plot_series(per_list, y_lists,
                    xlabel = 'Supply voltage relative to nominal Vdd (%)',
                    ylabel = ylabel,
                    legend_labels=['small', 'medium', 'large'],
                    #legend_labels=['normal', 'large'],
                    ylim = (0, 70),
                    legend_loc='upper right',
                    figsize=(8,4.5),
                    cb_func = annotate16,
                  figdir = FIG_DIR,
                    ofn=ofn)
        

    def ntc_vmin(self):
        tech_list = (45, 32, 22, 16)
        ms_list = (10,10,8,8)
        figsize = (6, 3.5)
        ylabel = 'Speedup (normalized)'

        sys = SymSys()

        sys.set_sys_prop(core=Core(ctype='IO',mech='HKMGS'))

        #sys.set_sys_prop(area=800, power=140)
        sys.set_sys_prop(area=SYS_LARGE['area'], power=SYS_LARGE['power'])
        y_lists = speedup_by_vmin(sys)
        ofn = 'ntc_vmin_%dw_%dmm.%s' % (SYS_LARGE['power'], SYS_LARGE['area'], self.fmt)
        ofile=joinpath(FIG_DIR, ofn)
        analysis.plot_series(tech_list, y_lists,
                    xlabel='Technology Nodes',
                    ylabel=ylabel,
                    ylim = (0,70),
                    legend_labels=['HP-1.3Vt', 'HP-1.2Vt', 'HP-1.1Vt', 'HP-nolimit'],
                    legend_loc='upper left',
                    ms_list=ms_list,
                    figsize=figsize,
                  figdir = FIG_DIR,
                    ofn=ofn)

        sys.set_sys_prop(area=SYS_LARGE['area'], power=SYS_LARGE['power'])
        y_lists = speedup_by_vmin(sys, var=True)
        ofn = 'ntc_vmin_var_%dw_%dmm.%s' % (SYS_LARGE['power'], SYS_LARGE['area'], self.fmt)
        ofile=joinpath(FIG_DIR, ofn)
        analysis.plot_series(tech_list, y_lists,
                    xlabel='Technology Nodes',
                    ylabel=ylabel,
                    ylim = (0,70),
                    legend_labels=['HP-1.3Vt', 'HP-1.2Vt', 'HP-1.1Vt', 'HP-nolimit'],
                    legend_loc='upper left',
                    ms_list=ms_list,
                    figsize=figsize,
                  figdir = FIG_DIR,
                    ofn=ofn)

        sys.set_sys_prop(area=SYS_MEDIUM['area'], power=SYS_MEDIUM['power'])
        y_lists = speedup_by_vmin(sys)
        ofn = 'ntc_vmin_%dw_%dmm.%s' % (SYS_MEDIUM['power'], SYS_MEDIUM['area'], self.fmt)
        ofile=joinpath(FIG_DIR, ofn)
        analysis.plot_series(tech_list, y_lists,
                    xlabel='Technology Nodes',
                    ylabel=ylabel,
                    ylim = (0,50),
                    legend_labels=['HP-1.3Vt', 'HP-1.2Vt', 'HP-1.1Vt', 'HP-nolimit'],
                    legend_loc='upper left',
                    ms_list=ms_list,
                    figsize=figsize,
                  figdir = FIG_DIR,
                    ofn=ofn)

        sys.set_sys_prop(area=SYS_MEDIUM['area'], power=SYS_MEDIUM['power'])
        y_lists = speedup_by_vmin(sys, var=True)
        ofn = 'ntc_vmin_var_%dw_%dmm.%s' % (SYS_MEDIUM['power'], SYS_MEDIUM['area'], self.fmt)
        ofile=joinpath(FIG_DIR, ofn)
        analysis.plot_series(tech_list, y_lists,
                    xlabel='Technology Nodes',
                    ylabel=ylabel,
                    ylim = (0,50),
                    legend_labels=['HP-1.3Vt', 'HP-1.2Vt', 'HP-1.1Vt', 'HP-nolimit'],
                    legend_loc='upper left',
                    ms_list=ms_list,
                    figsize=figsize,
                  figdir = FIG_DIR,
                    ofn=ofn)

        sys.set_sys_prop(area=SYS_SMALL['area'], power=SYS_SMALL['power'])
        y_lists = speedup_by_vmin(sys)
        ofn = 'ntc_vmin_%dw_%dmm.%s' % (SYS_SMALL['power'], SYS_SMALL['area'], self.fmt)
        ofile=joinpath(FIG_DIR, ofn)
        analysis.plot_series(tech_list, y_lists,
                    xlabel='Technology Nodes',
                    ylabel=ylabel,
                    ylim = (0,35),
                    legend_labels=['HP-1.3Vt', 'HP-1.2Vt', 'HP-1.1Vt', 'HP-nolimit'],
                    legend_loc='upper left',
                    ms_list=ms_list,
                    figsize=figsize,
                  figdir = FIG_DIR,
                    ofn=ofn)

        sys.set_sys_prop(area=SYS_SMALL['area'], power=SYS_SMALL['power'])
        y_lists = speedup_by_vmin(sys, var=True)
        ofn = 'ntc_vmin_var_%dw_%dmm.%s' % (SYS_SMALL['power'], SYS_SMALL['area'], self.fmt)
        ofile=joinpath(FIG_DIR, ofn)
        analysis.plot_series(tech_list, y_lists,
                    xlabel='Technology Nodes',
                    ylabel=ylabel,
                    ylim = (0,35),
                    legend_labels=['HP-1.3Vt', 'HP-1.2Vt', 'HP-1.1Vt', 'HP-nolimit'],
                    legend_loc='upper left',
                    ms_list=ms_list,
                    figsize=figsize,
                  figdir = FIG_DIR,
                    ofn=ofn)

    def do_ntc(self):
        self.ntc_speedup()
        self.ntc_vmin()

    def plot_darkdim(self, sys):

        figsize=(6,3.5)

        tech_list = (45, 32, 22, 16)
        #tech_list = (22, 16)
        speed_lists = []
        util_lists = []
        vdd_lists = []

        # no variation
        speed_list_dark = []
        util_list_dark = []
        vdd_list_dark = []
        speed_list_dim = []
        util_list_dim = []
        vdd_list_dim = []

        for ctech in tech_list:
            sys.set_core_prop(tech=ctech, pv=False)
            ret = sys.perf_by_dark()
            speed_list_dark.append(ret['perf'])
            util_list_dark.append(ret['util'])
            vdd_list_dark.append(ret['vdd'])

            vmin = sys.core.vt * 1.1
            ret = sys.opt_core_num(vmin=vmin)
            speed_list_dim.append(ret['perf'])
            util_list_dim.append(ret['util'])
            vdd_list_dim.append(ret['vdd'])

        speed_lists.append(speed_list_dark)
        util_lists.append(util_list_dark)
        vdd_lists.append(vdd_list_dark)
        speed_lists.append(speed_list_dim)
        util_lists.append(util_list_dim)
        vdd_lists.append(vdd_list_dim)

        
        # dark with variation
        speed_list_dark = []
        util_list_dark = []
        vdd_list_dark = []
        speed_list_dim = []
        util_list_dim = []
        vdd_list_dim = []

        for ctech in tech_list:
            sys.set_core_prop(tech=ctech, pv=True)
            ret = sys.perf_by_dark()
            speed_list_dark.append(ret['perf'])
            util_list_dark.append(ret['util'])
            vdd_list_dark.append(ret['vdd'])

            #pdb.set_trace()
            vmin = sys.core.vt * 1.1
            ret = sys.opt_core_num(vmin=vmin)
            speed_list_dim.append(ret['perf'])
            util_list_dim.append(ret['util'])
            vdd_list_dim.append(ret['vdd'])

        speed_lists.append(speed_list_dark)
        util_lists.append(util_list_dark)
        vdd_lists.append(vdd_list_dark)
        speed_lists.append(speed_list_dim)
        util_lists.append(util_list_dim)
        vdd_lists.append(vdd_list_dim)

        #plot speedup
        ofn = 'darkdim_speedup_%dw_%dmm.%s' % (sys.power, sys.area, self.fmt,)

        analysis.plot_series(tech_list, speed_lists,
                    xlabel = 'Technology Nodes',
                    ylabel = 'Speedup (normalized)',
                    legend_labels=['Dark Si.', 'Dim Si.', 'Dark Si.(var)','Dim Si.(var)'],
                    legend_loc='upper left',
                    figsize=figsize,
                  figdir = FIG_DIR,
                    ofn=ofn)

        #plot utilization
        ofn = 'darkdim_util_%dw_%dmm.%s' % (sys.power, sys.area, self.fmt,)

        #if sys.power == SYS_SMALL['power']:
            #plot_series(tech_list, util_lists,
                        #xlabel = 'Technology Nodes',
                        #ylabel = r'System Utilization ($\%$)',
                        #legend_labels=['Dark Si.', 'Dim Si.', 'Dark Si.(var)','Dim Si.(var)'],
                        #legend_loc='center right',
                        #figsize=(6,4.5),
                        #ylim=(0, 105),
                        #ofn=ofn)
        #elif sys.power == SYS_LARGE['power']:
        analysis.plot_series(tech_list, util_lists,
                    xlabel = 'Technology Nodes',
                    ylabel = r'System Utilization ($\%$)',
                    legend_labels=['Dark Si.', 'Dim Si.', 'Dark Si.(var)','Dim Si.(var)'],
                    legend_loc='center left',
                    figsize=figsize,
                    ylim=(0, 105),
                  figdir = FIG_DIR,
                    ofn=ofn)

        #plot voltage(vdd)
        vdd_lists.append([(ptmtech.vt['HKMGS'][tech]) for tech in tech_list])
        ofn = 'darkdim_vdd_%dw_%dmm.%s' % (sys.power, sys.area, self.fmt,)
        ofile = joinpath(FIG_DIR, ofn)

        #if sys.power == SYS_SMALL['power']:
            #plot_series2(tech_list, vdd_lists,
                        #xlabel = 'Technology Nodes',
                        #ylabel = 'Optimal supply voltage',
                        #legend_labels=['Dark Si.', 'Dim Si.', 'Dark Si.(var)','Dim Si.(var)', r'$V_t$'],
                        #legend_loc='lower left',
                        #ylim=(0.1,1.45),
                        #figsize=figsize,
                        #ofn=ofn)
        #elif sys.power == SYS_LARGE['power']:
        analysis.plot_series2(tech_list, vdd_lists,
                    xlabel = 'Technology Nodes',
                    ylabel = 'Optimal supply voltage',
                    legend_labels=['Dark Si.', 'Dim Si.', 'Dark Si.(var)','Dim Si.(var)', r'$V_t$'],
                    legend_loc='lower left',
                    ylim=(0.1,1.45),
                    figsize=figsize,
                  figdir = FIG_DIR,
                    ofn=ofn)



    def do_darkdim(self):

        sys = SymSys()
        sys.set_sys_prop(core=Core(ctype='IO', mech='HKMGS'))

        sys.set_sys_prop(area=SYS_LARGE['area'], power=SYS_LARGE['power'])
        self.plot_darkdim(sys)

        sys.set_sys_prop(area=SYS_SMALL['area'], power=SYS_SMALL['power'])
        self.plot_darkdim(sys)

    def plot_hplp(self, sys):

        figsize=(6,4)

        tech_list = (45, 32, 22, 16)

        speed_lists = []
        vdd_lists = []

        # HP no variation
        speed_list = []
        vdd_list = []

        for ctech in tech_list:
            sys.set_core_prop(tech=ctech, pv=False, mech='HKMGS')
            ret = sys.opt_core_num()
            speed_list.append(ret['perf'])
            vdd_list.append(ret['vdd'])

        speed_lists.append(speed_list)
        vdd_lists.append(vdd_list)

        # HP variation
        speed_list = []
        vdd_list = []

        for ctech in tech_list:
            sys.set_core_prop(tech=ctech, pv=True, mech='HKMGS')
            ret = sys.opt_core_num()
            speed_list.append(ret['perf'])
            vdd_list.append(ret['vdd'])

        speed_lists.append(speed_list)
        vdd_lists.append(vdd_list)

        
        #LP no variation
        speed_list = []
        vdd_list = []

        for ctech in tech_list:
            sys.set_core_prop(tech=ctech, pv=False, mech='LP')
            ret = sys.opt_core_num()
            speed_list.append(ret['perf'])
            vdd_list.append(ret['vdd'])

        speed_lists.append(speed_list)
        vdd_lists.append(vdd_list)

        #LP variation
        speed_list = []
        vdd_list = []

        for ctech in tech_list:
            sys.set_core_prop(tech=ctech, pv=True, mech='LP')
            ret = sys.opt_core_num()
            speed_list.append(ret['perf'])
            vdd_list.append(ret['vdd'])

        speed_lists.append(speed_list)
        vdd_lists.append(vdd_list)

        #plot speedup
        ofn = 'hplp_speedup_%dw_%dmm.%s' % (sys.power, sys.area, self.fmt,)
        ofile = joinpath(FIG_DIR, ofn)

        analysis.plot_series(tech_list, speed_lists,
                    xlabel = 'Technology Nodes',
                    ylabel = 'Speedup (normalized)',
                    legend_labels=['HP', 'HP-var', 'LP','LP-var'],
                    legend_loc='upper left',
                    figsize=figsize,
                  figdir = FIG_DIR,
                    ofn=ofn)

        #plot vdd
        vdd_lists.append([(ptmtech.vt['HKMGS'][tech]) for tech in tech_list])
        vdd_lists.append([(ptmtech.vt['LP'][tech]) for tech in tech_list])
        ofn = 'hplp_vdd_%dw_%dmm.%s' % (sys.power, sys.area, self.fmt,)
        ofile = joinpath(FIG_DIR, ofn)

        analysis.plot_series2(tech_list, vdd_lists,
                    xlabel = 'Technology Nodes',
                    ylabel = 'Optimal supply voltage',
                    legend_labels=['HP', 'HP-var', 'LP','LP-var', r'HP-$V_t$', r'LP-$V_t$'],
                    legend_loc='lower left',
                    ylim=(0.1,1.45),
                    figsize=figsize,
                  figdir = FIG_DIR,
                    ofn=ofn)


    def do_hplp(self):

        sys = SymSys()
        sys.set_sys_prop(core=Core(ctype='IO'))

        sys.set_sys_prop(area=SYS_SMALL['area'], power=SYS_SMALL['power'])
        self.plot_hplp(sys)

        sys.set_sys_prop(area=SYS_MEDIUM['area'], power=SYS_MEDIUM['power'])
        self.plot_hplp(sys)

        sys.set_sys_prop(area=SYS_LARGE['area'], power=SYS_LARGE['power'])
        self.plot_hplp(sys)

    def plot_sysconf(self, sys):

        figsize=(6,4)
        xlabel = 'Power (W)'
        plist = (30, 40, 50, 60, 70, 80, 90, 100)

        speed_lists = []
        util_lists = []
        vdd_lists = []

        speed_list = []
        util_list = []
        vdd_list = []

        for power in plist:
            sys.set_core_prop(pv=False)
            sys.set_sys_prop(power=power)
            ret = sys.opt_core_num()
            speed_list.append(ret['perf'])
            util_list.append(ret['util'])
            vdd_list.append(ret['vdd'])

        speed_lists.append(speed_list)
        util_lists.append(util_list)
        vdd_lists.append(vdd_list)

        speed_list = []
        util_list = []
        vdd_list = []

        for power in plist:
            sys.set_core_prop(pv=True)
            sys.set_sys_prop(power=power)
            ret = sys.opt_core_num()
            speed_list.append(ret['perf'])
            util_list.append(ret['util'])
            vdd_list.append(ret['vdd'])

        speed_lists.append(speed_list)
        util_lists.append(util_list)
        vdd_lists.append(vdd_list)

        #ofn = 'sysconf_sputil_%dnm.%s' % (sys.core.tech, self.fmt)
        #plot_twinx(plist, speed_lists, util_lists,
                   #xlabel = xlabel, y1label = 'Speedup (normalized', 
                   #y2label = 'Utilization ($\%$)',
                   #legend_labels = ['Normal', 'Var'],
                   #legend_loc = 'lower right',
                   #xlim=(25, 105),
                   #y2lim=(10, 110),
                   #figsize=figsize,
                   #ofn = ofn)
        ofn = 'sysconf_speedup_%dnm.%s' % (sys.core.tech, self.fmt)
        analysis.plot_data(plist, speed_lists,
                  xlabel = xlabel,
                  ylabel = 'Speedup (normalized)',
                  legend_labels = ['Normal','Var'],
                  legend_loc = 'lower right',
                  figsize = figsize,
                  xlim = (25, 105),
                  ylim = (5, 55),
                  figdir = FIG_DIR,
                  ofn = ofn)
        
        ofn = 'sysconf_util_%dnm.%s' % (sys.core.tech, self.fmt)
        analysis.plot_data(plist, util_lists,
                  xlabel = xlabel,
                  ylabel = 'Utilization',
                  legend_labels = ['Normal','Var'],
                  legend_loc = 'lower right',
                  figsize = figsize,
                  xlim = (25, 105),
                  ylim = (10, 110),
                  figdir = FIG_DIR,
                  ofn = ofn)

        def annotate_vdd(axes, fig):
            tech = sys.core.tech
            textstr = '$V_t=%.3fV$' % ptmtech.vt['HKMGS'][tech]
            axes.text(40, ptmtech.vt['HKMGS'][tech]+0.05, textstr, transform=axes.transData, fontsize=16,verticalalignment='top')
            #axes.axhline(y=ptmtech.vt['HKMGS'][tech], xmin=30, xmax=100, 
                         #ls='-', c='black', lw=1, alpha=0.8)

            
            #props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
            textstr = '$V_{nom}=%.1fV$' % ptmtech.vdd['HKMGS'][tech]
            axes.text(40, ptmtech.vdd['HKMGS'][tech]+0.03, textstr, transform=axes.transData, fontsize=16,verticalalignment='top')
            axes.axhline(y=ptmtech.vdd['HKMGS'][tech], xmin=0.06, xmax=0.94, ls='--', c='black', lw=1, alpha=0.7)

            #textstr = '$V_{nom}=%.1fV$\n$V_t=%.3fV$' % (ptmtech.vdd['HKMGS'][tech], ptmtech.vt['HKMGS'][tech])
            #props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
            #axes.text(52, 0.62, textstr, fontsize=14,verticalalignment='top',bbox=props)

        
        ofn = 'sysconf_vdd_%dnm.%s' % (sys.core.tech, self.fmt)
        analysis.plot_data(plist, vdd_lists,
                  xlabel = xlabel,
                  ylabel = 'Optimal supply voltage',
                  legend_labels = ['Normal','Var'],
                  legend_loc = 'lower right',
                  figsize = figsize,
                  xlim = (25, 105),
                  ylim = (0.50, 0.9),
                  xgrid= False,
                  ygrid= False,
                  cb_func = annotate_vdd,
                  figdir = FIG_DIR,
                  ofn = ofn)
        

    def do_sysconf(self):

        sys = SymSys()
        sys_area = 100

        sys.set_sys_prop(core=Core(ctype='IO',mech='HKMGS'), area = sys_area)

        #sys.set_core_prop(tech = 32)
        #self.plot_sysconf(sys)

        sys.set_core_prop(tech = 22)
        self.plot_sysconf(sys)

        sys.set_core_prop(tech = 16)
        self.plot_sysconf(sys)



if __name__ == '__main__':

    # Init command line arguments parser
    parser = OptionParser()
    section_choices = ('variation','ntc','hplp','darkdim','sysconf', 'vpen', 'penadj')
    parser.add_option('--sec', default='penadj', choices=section_choices,
                      help='choose the secitons of plotting, choose from ('
                      +','.join(section_choices)
                      +'), default: %default]')
    mode_choices = ('a','p','ap')
    parser.add_option('--mode', default='p', choices=mode_choices,
                      help='choose the running mode, choose from ('
                      +','.join(mode_choices)
                      +'), default: %default]')
    parser.add_option('--sys-area', type='int', default=400)
    parser.add_option('--sys-power', type='int', default=100)
    fmt_choices=('png','pdf', 'eps')
    parser.add_option('--fmt', default='pdf', choices=fmt_choices,
                      help='choose the format of output, choose from ('
                      +','.join(fmt_choices)
                      +'), default: %default')
        
    (options,args) = parser.parse_args()
    
    # Init main analyzer
    anl = MainAnalyzer()

    anl.fmt = options.fmt

    if options.sec == 'variation':
        anl_varimpact = VariationImpactAnalysis(fmt=options.fmt)
        anl_varimpact.set_tech(16)
        if 'a' in options.mode:
            anl_varimpact.analyze()
        if 'p' in options.mode:
            anl_varimpact.plot()

    elif options.sec == 'ntc':
        anl.do_ntc()
    elif options.sec == 'darkdim':
        anl.do_darkdim()
    elif options.sec == 'hplp':
        anl.do_hplp()
    elif options.sec == 'sysconf':
        anl.do_sysconf()
    elif options.sec == 'vpen':
        anl.analyze_var_penalty()
    elif options.sec == 'penadj':
        anl_penadj = PenaltyAdjustAnalysis(fmt=options.fmt)
        anl_penadj.set_sys(area=SYS_SMALL['area'], power=SYS_SMALL['power'])
        if 'a' in options.mode:
            anl_penadj.analyze()
        if 'p' in options.mode:
            anl_penadj.plot()

        anl_penadj.set_sys(area=SYS_MEDIUM['area'], power=SYS_MEDIUM['power'])
        if 'a' in options.mode:
            anl_penadj.analyze()
        if 'p' in options.mode:
            anl_penadj.plot()

        anl_penadj.set_sys(area=SYS_LARGE['area'], power=SYS_LARGE['power'])
        if 'a' in options.mode:
            anl_penadj.analyze()
        if 'p' in options.mode:
            anl_penadj.plot()

