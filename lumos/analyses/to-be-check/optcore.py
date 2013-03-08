import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
from os.path import join as joinpath
from optparse import OptionParser
import os
from model.app import App
import model.system
from model.system import HomogSys
from model.core import Core
import analysis
FIG_DIR=joinpath(analysis.FIG_DIR, 'optcore')

try:
    os.makedirs(FIG_DIR)
except OSError:
    if os.path.isdir(FIG_DIR):
        pass
    else:
        raise

def plotHPLP(area, power, var, suffix):
    ctechList = (45, 32, 22, 16)
    cmechList = ('LP', 'HKMGS')
    lsList = ('o-', 's-', '*-', '^-')
    legendList = []

    sys = HomogSys()
    sys.set_sys_prop(area=area, power=power, core=Core())

    fig = plt.figure(figsize=(8,6))
    axes_perf = fig.add_subplot(111)
    xList = range(1, len(ctechList)+1)
    ctype = 'IO'
    series_idx = 0
    for cmech in cmechList:
        if cmech == 'HKMGS':
            legendList.append('HP')
        else:
            legendList.append(cmech)

        perfList = []
        for ctech in ctechList:
            sys.set_core_prop(tech=ctech, ctype=ctype, mech=cmech)
            result = sys.opt_core_num()
            perfList.append(result['perf'])

        axes_perf.plot(xList, perfList, lsList[series_idx])

        series_idx = series_idx + 1

    majorLocator = MultipleLocator()
    axes_perf.set_xlim(0.5, len(xList)+0.5)
    axes_perf.set_xlabel('Technology nodes')
    axes_perf.set_ylabel('Normalized speedup')
    axes_perf.xaxis.set_major_locator(majorLocator)
    axes_perf.set_xticklabels(['45nm', '32nm', '22nm', '16nm'])
    axes_perf.legend(axes_perf.lines, legendList, loc='upper left')

    ofn = 'hplp_%dmm_%dw.pdf' % (area, power)
    ofile = joinpath(FIG_DIR, ofn)
    fig.savefig(ofile)
        
def plotWithVmin(area, power, var, suffix):

    #areaList = (1000,)
    #powerList = (80,120,160)
    vminList = (model.system.VMIN, 1.3, 1.2, 1.1)
    ctechList = (45,32,22,16)
    #cmechList = ('LP','HKMGS','ITRS','CONS')
    var = False
    hponly = True
    if var:
        varList = (False, True, False, True)
        cmechList = ('LP', 'LP', 'HKMGS', 'HKMGS')
    else:
        if hponly:
            varList = (False, False, False, False)
            cmechList = ('HKMGS','HKMGS','HKMGS','HKMGS')
            vminList = (0, 1.1, 1.2, 1.3)
            legendList = ('HP-free', 'HP-1.1Vt', 'HP-1.2Vt', 'HP-1.3Vt')
        else:
            varList = (False, False, False, False, False, False, False, False)
            cmechList = ('LP','LP','LP','LP','HKMGS','HKMGS','HKMGS','HKMGS')
            vminList = (0, 1.1, 1.2, 1.3, 0, 1.1, 1.2, 1.3)
            legendList = ('LP-free', 'LP-1.1Vt', 'LP-1.2Vt', 'LP-1.3Vt',
                          'HP-free', 'HP-1.1Vt', 'HP-1.2Vt', 'HP-1.3Vt')

    sys = HomogSys()
    sys.set_sys_prop(area=area, power=power, core=Core())

    lsList = ('o-', 's-', '*-', '^-','o-', 's-', '*-', '^-')
    ctype='IO'
    fig = plt.figure(figsize=(12,10))
    fig.subplots_adjust(left=0.05, right=0.95, top=0.9, bottom=0.05)
    #fig.suptitle(r'%d$mm^2$, %dw, %s' % (area, power, ctype))
    axes_cnum = fig.add_subplot(221)
    axes_perf = fig.add_subplot(222)
    axes_util = fig.add_subplot(223)
    axes_vdd = fig.add_subplot(224)
    xList = range(1, len(ctechList)+1)
    for (var, mech, vminr, ls) in zip(varList, cmechList, vminList, lsList):
    #for cmech in cmechList:
        #idx = cmech.find('Var')
        #if idx != -1:
            #mech = cmech[:idx]
            #variation = True
        #else:
            #mech = cmech
            #variation = False
        cnumList = []
        perfList = []
        utilList = []
        vddList = []
        for ctech in ctechList:

            sys.set_core_prop(tech=ctech, ctype=ctype, mech=mech)
            vmin = sys.core.vt * vminr
            result=sys.opt_core_num(vmin=vmin)
            cnumList.append(result['cnum'])
            perfList.append(result['perf'])
            utilList.append(result['util'])
            vddList.append(result['vdd'])


        axes_cnum.plot(xList, cnumList, ls)
        axes_perf.plot(xList, perfList, ls)
        axes_util.plot(xList, utilList, ls)
        axes_vdd.plot(xList, vddList, ls)

    majorLocator=MultipleLocator()

    axes_cnum.set_xlim(0.5, len(cnumList)+0.5)
    axes_cnum.set_title('Optimal Core Number')
    axes_cnum.xaxis.set_major_locator(majorLocator)
    axes_cnum.set_xticklabels(['45nm', '32nm', '22nm', '16nm'])
    axes_cnum.legend(axes_cnum.lines, legendList, loc='center',
                    bbox_to_anchor=(1.1, 1.17), ncol=4,
                    fancybox=True, shadow=True)

    axes_perf.set_xlim(0.5, len(cnumList)+0.5)
    axes_perf.set_title('Best Performance')
    axes_perf.xaxis.set_major_locator(majorLocator)
    axes_perf.set_xticklabels(['45nm', '32nm', '22nm', '16nm'])
    #axes_perf.legend(axes_perf.lines, legendList, loc='upper left')

    axes_util.set_xlim(0.5, len(cnumList)+0.5)
    axes_util.set_ylim(0,100)
    axes_util.set_title('Chip Utilization')
    axes_util.xaxis.set_major_locator(majorLocator)
    axes_util.set_xticklabels(['45nm', '32nm', '22nm', '16nm'])
    #axes_util.legend(axes_util.lines, legendList, loc='lower left')

    axes_vdd.set_xlim(0.5, len(cnumList)+0.5)
    axes_vdd.set_title('Supply Voltage')
    axes_vdd.xaxis.set_major_locator(majorLocator)
    axes_vdd.set_xticklabels(['45nm', '32nm', '22nm', '16nm'])
    #axes_vdd.legend(axes_vdd.lines, legendList, loc='lower left')
    
    ofn = 'vmin_%dmm_%dw_%s.%s' % (area, power, ctype, suffix)
    ofile = joinpath(FIG_DIR, ofn)
    fig.savefig(ofile)

def plotWithVminHPOnly(area, power, var, suffix):

    vminList = (model.system.VMIN, 1.3, 1.2, 1.1)
    ctechList = (45,32,22,16)
    var = False
    if var:
        varList = (False, True, False, True)
        cmechList = ('LP', 'LP', 'HKMGS', 'HKMGS')
    else:
        varList = (False, False, False, False)
        cmechList = ('HKMGS','HKMGS','HKMGS','HKMGS')
        vminList = (0, 1.1, 1.2, 1.3)
        legendList = ('HP-free', 'HP-1.1Vt', 'HP-1.2Vt', 'HP-1.3Vt')

    sys = HomogSys()
    sys.set_sys_prop(area=area, power=power, core=Core())

    lsList = ('o-', 's-', '*-', '^-')
    ctype='IO'
    fig = plt.figure(figsize=(8,6))
    #fig.subplots_adjust(left=0.05, right=0.95, top=0.9, bottom=0.05)
    #fig.suptitle(r'%d$mm^2$, %dw, %s' % (area, power, ctype))
    #axes_cnum = fig.add_subplot(221)
    #axes_perf = fig.add_subplot(222)
    axes_perf = fig.add_subplot(111)
    #axes_util = fig.add_subplot(223)
    #axes_vdd = fig.add_subplot(224)
    xList = range(1, len(ctechList)+1)
    for (var, mech, vminr, ls) in zip(varList, cmechList, vminList, lsList):
        #cnumList = []
        perfList = []
        #utilList = []
        #vddList = []
        for ctech in ctechList:

            sys.set_core_prop(tech=ctech, ctype=ctype, mech=mech)
            vmin = sys.core.vt * vminr
            result=sys.opt_core_num(vmin=vmin)
            #cnumList.append(result['cnum'])
            perfList.append(result['perf'])
            #utilList.append(result['util'])
            #vddList.append(result['vdd'])


        #axes_cnum.plot(xList, cnumList, ls)
        axes_perf.plot(xList, perfList, ls)
        #axes_util.plot(xList, utilList, ls)
        #axes_vdd.plot(xList, vddList, ls)

    majorLocator=MultipleLocator()

    #axes_cnum.set_xlim(0.5, len(cnumList)+0.5)
    #axes_cnum.set_title('Optimal Core Number')
    #axes_cnum.xaxis.set_major_locator(majorLocator)
    #axes_cnum.set_xticklabels(['45nm', '32nm', '22nm', '16nm'])
    #axes_cnum.legend(axes_cnum.lines, legendList, loc='center',
                    #bbox_to_anchor=(1.1, 1.17), ncol=4,
                    #fancybox=True, shadow=True)

    axes_perf.set_xlim(0.5, len(ctechList)+0.5)
    axes_perf.set_xlabel('Technology Nodes')
    axes_perf.set_ylabel('Normalized Speedup')
    axes_perf.xaxis.set_major_locator(majorLocator)
    axes_perf.set_xticklabels(['45nm', '32nm', '22nm', '16nm'])
    axes_perf.legend(axes_perf.lines, legendList, loc='upper left')

    #axes_util.set_xlim(0.5, len(cnumList)+0.5)
    #axes_util.set_ylim(0,100)
    #axes_util.set_title('Chip Utilization')
    #axes_util.xaxis.set_major_locator(majorLocator)
    #axes_util.set_xticklabels(['45nm', '32nm', '22nm', '16nm'])
    #axes_util.legend(axes_util.lines, legendList, loc='lower left')

    #axes_vdd.set_xlim(0.5, len(cnumList)+0.5)
    #axes_vdd.set_title('Supply Voltage')
    #axes_vdd.xaxis.set_major_locator(majorLocator)
    #axes_vdd.set_xticklabels(['45nm', '32nm', '22nm', '16nm'])
    #axes_vdd.legend(axes_vdd.lines, legendList, loc='lower left')
    
    ofn = 'vmin_hponly_%dmm_%dw_%s.%s' % (area, power, ctype, suffix)
    ofile = joinpath(FIG_DIR, ofn)
    fig.savefig(ofile)

def plotVminHPDark(area, power, var, suffix):

    vminList = (model.system.VMIN, 1.3, 1.2, 1.1)
    ctechList = (45,32,22,16)
    var = False
    if var:
        varList = (False, True, False, True)
        cmechList = ('LP', 'LP', 'HKMGS', 'HKMGS')
    else:
        varList = (False, False, False, False)
        cmechList = ('HKMGS','HKMGS','HKMGS','HKMGS')
        vminList = (0, 1.1, 1.2, 1.3)
        legendList = ('HP-dark', 'HP-free', 'HP-1.1Vt', 'HP-1.2Vt', 'HP-1.3Vt')

    sys = HomogSys()
    sys.set_sys_prop(area=area, power=power, core=Core())

    lsList = ('o-', 's-', '*-', '^-')
    ctype='IO'
    #fig = plt.figure(figsize=(16,6))
    #fig.subplots_adjust(left=0.05, right=0.95, top=0.9, bottom=0.05)
    #fig.suptitle(r'%d$mm^2$, %dw, %s' % (area, power, ctype))
    #axes_perf = fig.add_subplot(222)
    fig_perf = plt.figure(figsize=(8,6))
    axes_perf = fig_perf.add_subplot(111)
    fig_cnum = plt.figure(figsize=(8,6))
    axes_cnum = fig_cnum.add_subplot(111)
    fig_util = plt.figure(figsize=(8,6))
    axes_util = fig_util.add_subplot(111)
    #axes_vdd = fig.add_subplot(224)
    xList = range(1, len(ctechList)+1)
    perfList = []
    cnumList = []
    utilList = []
    for ctech in ctechList:
        sys.set_core_prop(tech=ctech, ctype=ctype, mech='HKMGS')
        result = sys.perf_by_dark()
        perfList.append(result['perf'])
        cnumList.append(result['active'])
        utilList.append(result['util'])
    axes_perf.plot(xList, perfList, 'd-')
    axes_cnum.plot(xList, cnumList, 'd-')
    axes_util.plot(xList, utilList, 'd-')
    
    for (var, mech, vminr, ls) in zip(varList, cmechList, vminList, lsList):
        perfList = []
        cnumList = []
        utilList = []
        #vddList = []
        for ctech in ctechList:

            sys.set_core_prop(tech=ctech, ctype=ctype, mech=mech)
            vmin = sys.core.vt * vminr
            result=sys.opt_core_num(vmin=vmin)
            cnumList.append(result['cnum'])
            perfList.append(result['perf'])
            utilList.append(result['util'])
            #vddList.append(result['vdd'])


        axes_cnum.plot(xList, cnumList, ls)
        axes_perf.plot(xList, perfList, ls)
        axes_util.plot(xList, utilList, ls)
        #axes_vdd.plot(xList, vddList, ls)

    majorLocator=MultipleLocator()

    axes_cnum.set_xlim(0.5, len(cnumList)+0.5)
    #axes_cnum.set_title('Optimal Core Number')
    axes_cnum.set_xlabel('Technology nodes')
    axes_cnum.set_ylabel('Number of active cores at optimal performance')
    axes_cnum.xaxis.set_major_locator(majorLocator)
    axes_cnum.set_xticklabels(['45nm', '32nm', '22nm', '16nm'])
    axes_cnum.legend(axes_cnum.lines, legendList, loc='upper left',
                    #bbox_to_anchor=(-0.1, 0.5), 
                     #ncol=5,
                    fancybox=True, shadow=True)

    axes_perf.set_xlim(0.5, len(ctechList)+0.5)
    axes_perf.set_xlabel('Technology nodes')
    axes_perf.set_ylabel('Normalized speedup')
    #axes_perf.set_title('Speedup')
    axes_perf.xaxis.set_major_locator(majorLocator)
    axes_perf.set_xticklabels(['45nm', '32nm', '22nm', '16nm'])
    axes_perf.legend(axes_perf.lines, legendList, loc='upper left', fancybox=True, shadow=True)

    axes_util.set_xlim(0.5, len(cnumList)+0.5)
    axes_util.set_ylim(0,105)
    #axes_util.set_title('Chip Utilization')
    axes_util.set_xlabel('Technology nodes')
    axes_util.set_ylabel('Chip utilization at optimal performance')
    axes_util.xaxis.set_major_locator(majorLocator)
    axes_util.set_xticklabels(['45nm', '32nm', '22nm', '16nm'])
    axes_util.legend(axes_util.lines, legendList, loc='center left', fancybox=True, shadow=True)

    #axes_vdd.set_xlim(0.5, len(cnumList)+0.5)
    #axes_vdd.set_title('Supply Voltage')
    #axes_vdd.xaxis.set_major_locator(majorLocator)
    #axes_vdd.set_xticklabels(['45nm', '32nm', '22nm', '16nm'])
    #axes_vdd.legend(axes_vdd.lines, legendList, loc='lower left')
    
    ofn = 'vmin_hp_dark_perf_%dmm_%dw_%s.%s' % (area, power, ctype, suffix)
    ofile = joinpath(FIG_DIR, ofn)
    fig_perf.savefig(ofile)

    ofn = 'vmin_hp_dark_cnum_%dmm_%dw_%s.%s' % (area, power, ctype, suffix)
    ofile = joinpath(FIG_DIR, ofn)
    fig_cnum.savefig(ofile)

    ofn = 'vmin_hp_dark_util_%dmm_%dw_%s.%s' % (area, power, ctype, suffix)
    ofile = joinpath(FIG_DIR, ofn)
    fig_util.savefig(ofile)

def plotMechWithTypeCombined(area, power, suffix):
    ctechList = (45,32,22,16)
    ctypeList = ('IO','O3')
    cmechList = ('LP','HKMGS')
    lsList = ('o-', 's-', '*-', '^-')
    legendList = []

    sys = HomogSys()
    sys.set_sys_prop(area=area, power=power, core=Core())

    fig = plt.figure(figsize=(16,6))
    #fig.suptitle(r'%d$mm^2$, %dw' % (area, power))
    axes_cnum = fig.add_subplot(121)
    axes_perf = fig.add_subplot(122)
    xList = range(1, len(ctechList)+1)
    series_idx = 0
    for ctype in ctypeList:
        for cmech in cmechList:
            legendList.append('%s-%s' % (ctype, cmech))

            cnumList = []
            perfList = []
            utilList = []
            vddList = []
            for ctech in ctechList:
                sys.set_core_prop(tech=ctech, ctype=ctype, mech=cmech)
                result=sys.opt_core_num()
                cnumList.append(result['cnum'])
                perfList.append(result['perf'])

            axes_cnum.plot(xList, cnumList, lsList[series_idx])
            axes_perf.plot(xList, perfList, lsList[series_idx])

            series_idx = series_idx + 1

    majorLocator=MultipleLocator()

    box = axes_cnum.get_position()
    axes_cnum.set_position([box.x0-box.width*0.1, box.y0, box.width, box.height])
    axes_cnum.set_xlim(0.5, len(cnumList)+0.5)
    axes_cnum.set_title('Optimal Core Number')
    axes_cnum.xaxis.set_major_locator(majorLocator)
    axes_cnum.set_xticklabels(['45nm', '32nm', '22nm', '16nm'])
    axes_cnum.legend(axes_cnum.lines, legendList, loc=(1.05,0))

    box = axes_perf.get_position()
    axes_perf.set_position([box.x0+box.width*0.15, box.y0, box.width, box.height])
    axes_perf.set_xlim(0.5, len(cnumList)+0.5)
    axes_perf.set_title('Best Performance')
    axes_perf.xaxis.set_major_locator(majorLocator)
    axes_perf.set_xticklabels(['45nm', '32nm', '22nm', '16nm'])
    #axes_perf.legend(axes_perf.lines, legendList, loc='upper left')

    ofn = 'mechcomb_%dmm_%dw.png' % (area, power)
    ofile = joinpath(FIG_DIR, ofn)
    fig.savefig(ofile)

def plotMechWithTypeCombinedDark(area, power, suffix):
    ctechList = (45,32,22,16)
    ctypeList = ('IO',)
    cmechList = ('LP','HKMGS')
    lsList = ('o-', 's-', '*-', '^-', 'p-', 'x-')
    legendList = []

    sys = HomogSys()
    sys.set_sys_prop(area=area, power=power, core=Core())

    fig = plt.figure(figsize=(14,6))
    #fig.suptitle(r'%d$mm^2$, %dw' % (area, power))
    axes_cnum = fig.add_subplot(121)
    axes_perf = fig.add_subplot(122)
    xList = range(1, len(ctechList)+1)
    series_idx = 0
    #for ctype in ctypeList:
    ctype = 'IO'
    # Series 1: Dark
    legendList.append('%s-dark' % (ctype,))
    maxnumList = []
    cnumList = []
    perfList = []
    utilList = []
    vddList = []
    for ctech in ctechList:
        sys.set_core_prop(tech=ctech, ctype=ctype, mech='HKMGS')
        result = sys.perf_by_dark()
        cnumList.append(result['active'])
        maxnumList.append(result['core'])
        perfList.append(result['perf'])
    axes_cnum.plot(xList, cnumList, lsList[series_idx])
    axes_perf.plot(xList, perfList, lsList[series_idx])
    series_idx = series_idx + 1
    
    # Series 2: HKMGS Dim
    legendList.append('%s' % (ctype,))

    cnumList = []
    perfList = []
    utilList = []
    vddList = []
    for ctech in ctechList:
        sys.set_core_prop(tech=ctech, ctype=ctype, mech='HKMGS')
        sys.set_sys_prop(area=area, power=power)
        result=sys.opt_core_num()
        cnumList.append(result['cnum'])
        perfList.append(result['perf'])

    axes_cnum.plot(xList, cnumList, lsList[series_idx])
    axes_perf.plot(xList, perfList, lsList[series_idx])

    series_idx = series_idx + 1
    # Series 3: C limit
    axes_cnum.plot(xList, maxnumList, '*--')

    
    majorLocator=MultipleLocator()

    box = axes_cnum.get_position()
    axes_cnum.set_position([box.x0-box.width*0.1, box.y0, box.width, box.height])
    axes_cnum.set_xlim(0.5, len(cnumList)+0.5)
    axes_cnum.set_title('Optimal Core Number')
    axes_cnum.xaxis.set_major_locator(majorLocator)
    axes_cnum.set_xticklabels(['45nm', '32nm', '22nm', '16nm'])
    axes_cnum.legend(axes_perf.lines, legendList, loc=(1.05,0))

    box = axes_perf.get_position()
    axes_perf.set_position([box.x0+box.width*0.15, box.y0, box.width, box.height])
    axes_perf.set_xlim(0.5, len(cnumList)+0.5)
    axes_perf.set_title('Best Performance')
    axes_perf.xaxis.set_major_locator(majorLocator)
    axes_perf.set_xticklabels(['45nm', '32nm', '22nm', '16nm'])
    #axes_perf.legend(axes_perf.lines, legendList, loc='upper left')

    ofn = 'mechcombdark_%dmm_%dw.%s' % (area, power, suffix)
    ofile = joinpath(FIG_DIR, ofn)
    fig.savefig(ofile)

def plotWithMechs(area, power, var, suffix):

    #areaList = (1000,)
    #powerList = (80,120,160)
    ctechList = (45,32,22,16)
    ctypeList = ('IO','O3')
    #cmechList = ('LP','HKMGS','ITRS','CONS')
    if var:
        cmechList = ('LP', 'LPVar', 'HKMGS', 'HKMGSVar')
    else:
        cmechList = ('LP','HKMGS')

    sys = HomogSys()
    sys.set_sys_prop(area=area, power=power, core=Core())

    lsList = ('o-', 's-', '*-', '^-')
    for ctype in ctypeList:
        fig = plt.figure(figsize=(12,9))
        fig.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.05)
        #fig.suptitle(r'%d$mm^2$, %dw, %s' % (area, power, ctype))
        axes_cnum = fig.add_subplot(221)
        axes_perf = fig.add_subplot(222)
        axes_util = fig.add_subplot(223)
        axes_vdd = fig.add_subplot(224)
        xList = range(1, len(ctechList)+1)
        for cmech in cmechList:
            idx = cmech.find('Var')
            if idx != -1:
                mech = cmech[:idx]
                variation = True
            else:
                mech = cmech
                variation = False
            cnumList = []
            perfList = []
            utilList = []
            vddList = []
            for (ctech,ls) in zip(ctechList,lsList):
                
                if var:
                    sys.set_core_prop(tech=ctech, ctype=ctype, mech=mech, variation=variation)
                else:

                    sys.set_core_prop(tech=ctech, ctype=ctype, mech=mech)
                result=sys.opt_core_num()
                cnumList.append(result['cnum'])
                perfList.append(result['perf'])
                utilList.append(result['util'])
                vddList.append(result['vdd'])


            axes_cnum.plot(xList, cnumList, ls)
            axes_perf.plot(xList, perfList, ls)
            axes_util.plot(xList, utilList, ls)
            axes_vdd.plot(xList, vddList, ls)

        majorLocator=MultipleLocator()

        axes_cnum.set_xlim(0.5, len(cnumList)+0.5)
        axes_cnum.set_title('Optimal Core Number')
        axes_cnum.xaxis.set_major_locator(majorLocator)
        axes_cnum.set_xticklabels(['45nm', '32nm', '22nm', '16nm'])
        axes_cnum.legend(axes_cnum.lines, cmechList, loc='upper left')

        axes_perf.set_xlim(0.5, len(cnumList)+0.5)
        axes_perf.set_title('Best Performance')
        axes_perf.xaxis.set_major_locator(majorLocator)
        axes_perf.set_xticklabels(['45nm', '32nm', '22nm', '16nm'])
        axes_perf.legend(axes_perf.lines, cmechList, loc='upper left')

        axes_util.set_xlim(0.5, len(cnumList)+0.5)
        axes_util.set_ylim(0,100)
        axes_util.set_title('Chip Utilization')
        axes_util.xaxis.set_major_locator(majorLocator)
        axes_util.set_xticklabels(['45nm', '32nm', '22nm', '16nm'])
        axes_util.legend(axes_util.lines, cmechList, loc='lower left')

        axes_vdd.set_xlim(0.5, len(cnumList)+0.5)
        axes_vdd.set_title('Supply Voltage')
        axes_vdd.xaxis.set_major_locator(majorLocator)
        axes_vdd.set_xticklabels(['45nm', '32nm', '22nm', '16nm'])
        axes_vdd.legend(axes_vdd.lines, cmechList, loc='lower left')
        
        ofn = 'mechs_%dmm_%dw_%s.%s' % (area, power, ctype, suffix)
        ofile = joinpath(FIG_DIR, ofn)
        fig.savefig(ofile)

def plotWithParaRatios(area, power, suffix):
    ctechList = (45,32,22,16)
    ctypeList = ('IO','O3')
    #ctypeList = ('IO',)
    cmechList = ('LP','HKMGS')
    fList = (0.1, 0.5, 0.9, 0.99, 1)
    legend_f = [ ('f=%g'%f) for f in fList]

    sys = HomogSys()
    sys.set_sys_prop(area=area, power=power, core=Core())

    lsList = ('o-', 's-', '*-', '^-', 'p-')
    for cmech in cmechList:
        for ctype in ctypeList:
            #fig = plt.figure(figsize=(16,12))
            fig = plt.figure(figsize=(16,6))
            fig.suptitle(r'%d$mm^2$, %dw, %s' % (area, power, ctype))
            axes_cnum = fig.add_subplot(121)
            axes_perf = fig.add_subplot(122)
            #axes_cnum = fig.add_subplot(221)
            #axes_perf = fig.add_subplot(222)
            #axes_util = fig.add_subplot(223)
            #axes_vdd = fig.add_subplot(224)
            xList = range(1, len(ctechList)+1)
            for f in fList:

                cnumList = []
                perfList = []
                #utilList = []
                #vddList = []
                for (ctech,ls) in zip(ctechList,lsList):
                    sys.set_core_prop(tech=ctech, ctype=ctype, mech=cmech)
                    result=sys.opt_core_num(app=App(f=f))
                    cnumList.append(result['cnum'])
                    perfList.append(result['perf'])
                    #utilList.append(result['util'])
                    #vddList.append(result['vdd'])


                axes_cnum.plot(xList, cnumList, ls)
                axes_perf.plot(xList, perfList, ls)
                #axes_util.plot(xList, utilList, ls)
                #axes_vdd.plot(xList, vddList, ls)

            majorLocator=MultipleLocator()

            axes_cnum.set_xlim(0.5, len(cnumList)+0.5)
            axes_cnum.set_title('Optimal Core Number')
            axes_cnum.xaxis.set_major_locator(majorLocator)
            axes_cnum.set_xticklabels(['45nm', '32nm', '22nm', '16nm'])
            axes_cnum.legend(axes_cnum.lines, legend_f, loc='upper left')

            axes_perf.set_xlim(0.5, len(cnumList)+0.5)
            axes_perf.set_title('Best Performance')
            axes_perf.xaxis.set_major_locator(majorLocator)
            axes_perf.set_xticklabels(['45nm', '32nm', '22nm', '16nm'])
            axes_perf.legend(axes_perf.lines, legend_f, loc='upper left')

            #axes_util.set_xlim(0.5, len(cnumList)+0.5)
            #axes_util.set_ylim(0,100)
            #axes_util.set_title('Chip Utilization')
            #axes_util.xaxis.set_major_locator(majorLocator)
            #axes_util.set_xticklabels(['45nm', '32nm', '22nm', '16nm'])
            #axes_util.legend(axes_util.lines, cmechList, loc='lower left')

            #axes_vdd.set_xlim(0.5, len(cnumList)+0.5)
            #axes_vdd.set_title('Supply Voltage')
            #axes_vdd.xaxis.set_major_locator(majorLocator)
            #axes_vdd.set_xticklabels(['45nm', '32nm', '22nm', '16nm'])
            #axes_vdd.legend(axes_vdd.lines, cmechList, loc='lower left')
            
            ofn = 'f_%dmm_%dw_%s_%s.%s' % (area, power, ctype, cmech, suffix)
            ofile = joinpath(FIG_DIR, ofn)
            fig.savefig(ofile)

def printWithParaRatios(area, power, suffix):
    ctechList = (45,32,22,16)
    #ctypeList = ('IO','O3')
    ctypeList = ('IO',)
    #cmechList = ('LP','HKMGS')
    cmechList = ('HKMGS',)
    fList = (0.1, 0.5, 0.9, 0.99, 1)
    legend_f = [ ('f=%g'%f) for f in fList]

    sys = HomogSys()
    sys.set_sys_prop(area=area, power=power, core=Core())

    for cmech in cmechList:
        mechtitle = 'mech=%s' % cmech
        print mechtitle.center(80).replace(' ', '%')
        for ctype in ctypeList:
            typetitle = 'type=%s' % ctype
            print typetitle.center(40).replace(' ', '+')
            for f in fList:
                ftitle = 'f=%g' % f
                print ftitle.center(20).replace(' ', '*')

                for ctech in ctechList:
                    sys.set_core_prop(tech=ctech, ctype=ctype, mech=cmech)
                    result=sys.opt_core_num(app=App(f=f))

                    print 'ctech: %d, cnum: %d, perf: %g' % (ctech, result['cnum'], result['perf'])


if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option('--plot-fmt', default='pub')
    parser.add_option('--plot-report', action='store_true', default=False)
    parser.add_option('--plot-f', action='store_true', default=False)
    parser.add_option('--print-f', action='store_true', default=False)
    parser.add_option('--plot-mech', action='store_true', default=False)
    parser.add_option('--plot-mech-comb', action='store_true', default=False)
    parser.add_option('--plot-mech-comb-dark', action='store_true', default=False)
    parser.add_option('--plot-vmin', action='store_true', default=False)
    parser.add_option('--plot-vmin-hponly', action='store_true', default=False)
    parser.add_option('--plot-vmin-dark', action='store_true', default=False)
    parser.add_option('--plot-hplp', action='store_true', default=True)
    parser.add_option('--sys-area', type='int', default=400)
    parser.add_option('--sys-power', type='int', default=100)
    parser.add_option('--var', action='store_true', default=False)
    (options,args) = parser.parse_args()

    if options.plot_fmt == 'view':
        suffix = 'png'
    elif options.plot_fmt == 'pub':
        suffix = 'pdf'
    else:
        print 'Unsupported plot format %s' % options.plot_fmt

    if options.plot_f:
        print 'Plot to the parallel ratio f'
        plotWithParaRatios(options.sys_area, options.sys_power, suffix)

    if options.print_f:
        printWithParaRatios(options.sys_area, options.sys_power, suffix)

    if options.plot_mech:
        print 'Plot to different mechanisms'
        plotWithMechs(options.sys_area, options.sys_power, options.var, suffix)

    if options.plot_mech_comb:
        print 'Plot to different mechanisms (combined core types)'
        plotMechWithTypeCombined(options.sys_area, options.sys_power, suffix)

    if options.plot_mech_comb_dark:
        print 'Plot to different mechanisms (combined core types, with dark)'
        plotMechWithTypeCombinedDark(options.sys_area, options.sys_power, suffix)

    if options.plot_report:
        #ece6332_report_mechs(options.sys_area, options.sys_power)
        ece6332_report_variation(options.sys_area, options.sys_power)

    if options.plot_vmin:
        plotWithVmin(options.sys_area, options.sys_power, options.var, suffix)

    if options.plot_vmin_hponly:
        plotWithVminHPOnly(options.sys_area, options.sys_power, options.var, suffix)

    if options.plot_vmin_dark:
        plotVminHPDark(options.sys_area, options.sys_power, options.var, suffix)

    if options.plot_hplp:
        plotHPLP(options.sys_area, options.sys_power, options.var, suffix)

