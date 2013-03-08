#!/usr/bin/env python
# encoding: utf-8

import logging
import cPickle as pickle
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from model.system import HeterogSys
from model.app import App
from model import kernel, workload
from model.budget import *

import analyses.analysis as analysis
from analyses.analysis import plot_data, plot_twinx, plot_series, plot_series2
from analyses.analysis import try_update, parse_bw

from optparse import OptionParser, OptionGroup
import ConfigParser
from os.path import join as joinpath

import multiprocessing
import Queue
import scipy.stats
import numpy

ANALYSIS_NAME = 'multiopt'
HOME = joinpath(analysis.HOME, ANALYSIS_NAME)
FIG_DIR,DATA_DIR = analysis.make_ws_dirs(ANALYSIS_NAME)


def ratio_dim2ucore(dim_ratio):
    if dim_ratio <= 10:
        return 85

    if dim_ratio > 90:
        return 10

    a, b = divmod( dim_ratio, 5)
    return ( (20-a) * 5 )


def init_with_dim_alloc(init_alloc, asic_perf, fpga_perf, dim_perf):
    alloc = dict()
    area_unalloc = 100
    alloc['dim'] = init_alloc
    area_unalloc = area_unalloc - init_alloc

    dimp = dim_perf[init_alloc]

    ucore_ratio = ratio_dim2ucore(init_alloc)
    fpga_perf_list = fpga_perf[ucore_ratio]
    listlen = len(fpga_perf_list)
    for i in xrange(1, listlen):
        if fpga_perf_list[i] > dimp:
            alloc['fpga'] = i
            area_unalloc = area_unalloc - i
            break

    asic_perf_dict = asic_perf[ucore_ratio]
    for ker in asic_perf_dict:
        alloc[ker] = 0

    return alloc, area_unalloc

def optimize_alloc(alloc, area_unalloc, asic_deriv,
        fpga_deriv, dim_deriv):

    while area_unalloc > 0:
        ucore_ratio = ratio_dim2ucore(alloc['dim'])

        dim_delta = dim_deriv[alloc['dim']]
        debug_info = [ 'dim:%.2f' % dim_delta ]

        if 'fpga' in alloc:
            fpga_delta = fpga_deriv[ucore_ratio][alloc['fpga']]

            debug_info.append( 'fpga:%.2f' % fpga_delta)

            if dim_delta > fpga_delta:
                key_max = 'dim'
                val_max = dim_delta
            else:
                key_max = 'fpga'
                val_max = fpga_delta
        else:
            key_max = 'dim'
            val_max = dim_delta

        asic_deriv_dict = asic_deriv[ucore_ratio]
        for ker in asic_deriv_dict:
            if ker in alloc:
                asic_delta = asic_deriv_dict[ker][alloc[ker]]

                debug_info.append( '[%s]:%.2f' % (ker[-1], asic_delta))

                if asic_delta > val_max:
                    key_max = ker
                    val_max = asic_delta

        alloc[key_max] = alloc[key_max] + 1

        area_unalloc = area_unalloc - 1

    return alloc


def optimize_alloc2(alloc, area_unalloc, asic_perf,
        fpga_perf, dim_perf):

    asic_allocable = True
    unalloc_accl = [ ker for ker in alloc if ker != 'dim' and ker != 'fpga' and alloc[ker] == 0 ]
    allocated_accl = []

    while area_unalloc > 0:
        ucore_ratio = ratio_dim2ucore(alloc['dim'])

        # try add new accelerator
        dim_alloc = alloc['dim']
        fpga_alloc = alloc['fpga']
        fpga_dict = fpga_perf[ucore_ratio]
        asic_perf_dict = asic_perf[ucore_ratio]

        new_accl_added = False
        step = alloc['fpga']/(kernel.ASIC_PERF_RATIO-1) + 1
        if step <= area_unalloc:
            dim_delta = dim_perf[dim_alloc+step] - dim_perf[dim_alloc]
            fpga_delta = fpga_dict[fpga_alloc+step] - fpga_dict[fpga_alloc]
            if dim_delta > fpga_delta:
                key_max = 'dim'
                val_max = dim_delta
            else:
                key_max = 'fpga'
                val_max = fpga_delta

            for ker in unalloc_accl:
                ker_perf_dict = asic_perf_dict[ker]
                ker_alloc = alloc[ker]
                asic_delta = ker_perf_dict[ker_alloc+step] - ker_perf_dict[ker_alloc]
                if asic_delta > val_max:
                    key_max = ker
                    val_max = asic_delta
                    new_accl_added = True

        if new_accl_added:
            alloc[key_max] = step
            area_unalloc = area_unalloc - step
            allocated_accl.append(key_max)
            unalloc_accl.remove(key_max)
        else:
            step = 1

            dim_delta = dim_perf[dim_alloc+step] - dim_perf[dim_alloc]
            debug_info = [ 'dim:%.2f' % dim_delta ]

            fpga_delta = fpga_dict[fpga_alloc+step] - fpga_dict[fpga_alloc]
            debug_info.append( 'fpga:%.2f' % fpga_delta)

            if dim_delta > fpga_delta:
                key_max = 'dim'
                val_max = dim_delta
            else:
                key_max = 'fpga'
                val_max = fpga_delta

            for ker in allocated_accl:
                ker_perf_dict = asic_perf_dict[ker]
                ker_alloc = alloc[ker]
                asic_delta = ker_perf_dict[ker_alloc+step] - ker_perf_dict[ker_alloc]
                debug_info.append( '[%s]:%.2f' % (ker[-1], asic_delta))

                if asic_delta > val_max:
                    key_max = ker
                    val_max = asic_delta

            alloc[key_max] = alloc[key_max] + step
            area_unalloc = area_unalloc - step


        # post-alloc check
        fpga_alloc = alloc['fpga']
        newstep = fpga_alloc/(kernel.ASIC_PERF_RATIO-1)
        allocated_accl_copy = list(allocated_accl)
        for ker in allocated_accl_copy:
            ker_alloc = alloc[ker]
            if ker_alloc <= newstep:
                alloc[ker] = 0
                area_unalloc = area_unalloc + ker_alloc
                allocated_accl.remove(ker)
                unalloc_accl.append(ker)


    return alloc

def optimize_fpgaonly(alloc, area_unalloc, dim_deriv, fpga_deriv):
    while area_unalloc > 0:
        ucore_ratio = ratio_dim2ucore(alloc['dim'])
        dim_delta = dim_deriv[alloc['dim']]
        key_max = 'dim'
        val_max = dim_delta

        fpga_delta=fpga_deriv[ucore_ratio][alloc['fpga']]
        if fpga_delta > val_max:
            key_max = 'fpga'
            val_max = fpga_delta

        alloc[key_max] = alloc[key_max] + 1
        area_unalloc = area_unalloc - 1

        print ucore_ratio, alloc['fpga']

    return alloc


def init_asiconly(init_alloc, asic_perf, dim_perf):
    alloc = dict()
    area_unalloc = 100
    alloc['dim'] = init_alloc
    area_unalloc = area_unalloc - init_alloc

    dimp = dim_perf[init_alloc]

    ucore_ratio = ratio_dim2ucore(init_alloc)

    asic_perf_dict = asic_perf[ucore_ratio]
    for ker in asic_perf_dict:
        asic_perf_list = asic_perf_dict[ker]
        listlen = len(asic_perf_list)
        for i in xrange(1, listlen):
            if asic_perf_list[i] > dimp:
                alloc[ker] = i
                area_unalloc = area_unalloc - i
                break

    return alloc, area_unalloc


def optimize_asiconly(alloc, area_unalloc, asic_deriv, dim_deriv,
        dim_max=100, asic_max=100):
    dim_allocated = alloc['dim']
    dim_allocable = True
    asic_allocated = sum([alloc[c] for c in alloc]) - dim_allocated
    asic_allocable = True

    while area_unalloc > 0:
        ucore_ratio = ratio_dim2ucore(alloc['dim'])
        key_max = None
        val_max = 0

        if dim_allocable:
            dim_delta = dim_deriv[alloc['dim']]

            key_max = 'dim'
            val_max = dim_delta

        if asic_allocable:
            asic_deriv_dict = asic_deriv[ucore_ratio]
            for ker in asic_deriv_dict:
                if ker in alloc:
                    asic_delta = asic_deriv_dict[ker][alloc[ker]]

                    if not key_max:
                        key_max = ker
                        val_max = asic_delta
                    elif asic_delta > val_max:
                        key_max = ker
                        val_max = asic_delta

        alloc[key_max] = alloc[key_max] + 1
        area_unalloc = area_unalloc - 1
        if key_max == 'dim':
            dim_allocated = dim_allocated + 1
        else:
            asic_allocated = asic_allocated + 1

        if dim_allocated >= dim_max:
            dim_allocable = False
        if asic_allocated >= asic_max:
            asic_allocable = False

        if not dim_allocable and not asic_allocable:
            break

    return alloc





class MultiOpt(object):
    """ Single ASIC accelerator with incremental area allocation """

    def __init__(self, options, budget):
        self.prefix = ANALYSIS_NAME

        self.fmt = options.fmt

        self.budget = budget

        self.id = self.prefix

        self.options = options

        self.series = options.series
        if options.series:
            self.FIG_DIR = analysis.mk_dir(FIG_DIR, options.series)
            self.DATA_DIR = analysis.mk_dir(DATA_DIR, options.series)
        else:
            self.FIG_DIR = FIG_DIR
            self.DATA_DIR = DATA_DIR

    def analyze(self):
        ucore_ratio_list = range(10, 90, 5)
        asic_perf = dict()
        asic_deriv = dict()
        fpga_perf = dict()
        fpga_deriv = dict()
        kernel_list = None
        for ucore_ratio in ucore_ratio_list:
            asic_dfn = joinpath(HOME, '..', 'asicinc', 'data', self.series,
                    'asicinc-%d.pypkl' % ucore_ratio)
            with open(asic_dfn, 'rb') as f:
                pickle_data = pickle.load(f)
            asic_perf[ucore_ratio] = pickle_data
            listlen = 0
            asic_deriv[ucore_ratio] = dict()

            if not kernel_list:
               kernel_list = pickle_data.keys()

            for ker in pickle_data:
                if listlen == 0:
                    listlen = len(pickle_data[ker])
                deriv_list = [ (pickle_data[ker][i+1]-pickle_data[ker][i])
                        for i in xrange(listlen-1) ]
                asic_deriv[ucore_ratio][ker] = deriv_list

            fpga_dfn = joinpath(HOME, '..', 'fpgainc', 'data', self.series,
                    'fpgainc-%d.pypkl' % ucore_ratio)
            with open(fpga_dfn, 'rb') as f:
                pickle_data = pickle.load(f)
            fpga_perf[ucore_ratio] = pickle_data
            listlen = len(pickle_data)
            deriv_list = [ (pickle_data[i+1]-pickle_data[i]) for i in
                    xrange(listlen-1) ]
            fpga_deriv[ucore_ratio] = deriv_list

        dim_dfn = joinpath(HOME, '..', 'diminc', 'data', 'diminc-10.pypkl')
        with open(dim_dfn, 'rb') as f:
            pickle_data = pickle.load(f)
        dim_perf = pickle_data
        listlen = len(dim_perf)
        dim_deriv = [ (dim_perf[i+1]-dim_perf[i]) for i in xrange(listlen-1) ]

        dim_alloc_seed = 70
        alloc, area_unalloc = init_with_dim_alloc(dim_alloc_seed, asic_perf,
                fpga_perf, dim_perf)

        alloc_init = alloc.copy()

        #alloc_opt = optimize_fpgaonly(alloc, area_unalloc, dim_deriv, fpga_deriv)

        #alloc_opt = optimize_alloc(alloc, area_unalloc,
                #asic_deriv, fpga_deriv, dim_deriv)
        alloc_opt = optimize_alloc2(alloc, area_unalloc,
                asic_perf, fpga_perf, dim_perf)

        #area_unalloc = 0
        #alloc_justify = dict()
        #for k in kernel_list:
            #if k in alloc_opt:
                #if alloc_opt[k] == alloc_init[k]:
                    #area_unalloc = area_unalloc + alloc_opt[k]
                #else:
                    #alloc_justify[k] = alloc_opt[k]
        #alloc_justify['dim'] = alloc_opt['dim']
        #if 'fpga' in alloc_opt:
            #alloc_justify['fpga'] = alloc_opt['fpga']

        #alloc_opt = optimize_alloc(alloc_justify, area_unalloc,
                #asic_deriv, fpga_deriv, dim_deriv)
        #alloc_opt = optimize_alloc2(alloc_justify, area_unalloc,
                #asic_perf, fpga_perf, dim_perf)

        print alloc_opt



    def optimize_asic(self):
        ucore_ratio_list = range(10, 90, 5)
        asic_perf = dict()
        asic_deriv = dict()
        kernel_list = None
        for ucore_ratio in ucore_ratio_list:
            asic_dfn = joinpath(HOME, '..', 'asicinc', 'data', self.series,
                    'asicinc-%d.pypkl' % ucore_ratio)
            with open(asic_dfn, 'rb') as f:
                pickle_data = pickle.load(f)
            asic_perf[ucore_ratio] = pickle_data
            listlen = 0
            asic_deriv[ucore_ratio] = dict()

            if not kernel_list:
               kernel_list = pickle_data.keys()

            for ker in pickle_data:
                if listlen == 0:
                    listlen = len(pickle_data[ker])
                deriv_list = [ (pickle_data[ker][i+1]-pickle_data[ker][i])
                        for i in xrange(listlen-1) ]
                asic_deriv[ucore_ratio][ker] = deriv_list


        dim_dfn = joinpath(HOME, '..', 'diminc', 'data', 'diminc-10.pypkl')
        with open(dim_dfn, 'rb') as f:
            pickle_data = pickle.load(f)
        dim_perf = pickle_data
        listlen = len(dim_perf)
        dim_deriv = [ (dim_perf[i+1]-dim_perf[i]) for i in xrange(listlen-1) ]

        dim_alloc_seed = 80
        alloc, area_unalloc = init_asiconly(dim_alloc_seed,
                asic_perf, dim_perf)

        alloc_init = alloc.copy()

        #alloc_opt = optimize_asiconly(alloc, area_unalloc,
                #asic_deriv, dim_deriv, dim_max=60, asic_max=20)
        alloc_opt = optimize_asiconly(alloc, area_unalloc,
                asic_deriv, dim_deriv)
        #alloc_opt = optimize_alloc2(alloc, area_unalloc,
                #asic_perf, fpga_perf, dim_perf)


        area_unalloc = 0
        alloc_justify = dict()
        for k in kernel_list:
            if k in alloc_opt:
                if alloc_opt[k] == alloc_init[k]:
                    area_unalloc = area_unalloc + alloc_opt[k]
                else:
                    alloc_justify[k] = alloc_opt[k]
        alloc_justify['dim'] = alloc_opt['dim']

        alloc_opt = optimize_asiconly(alloc_justify, area_unalloc,
                asic_deriv, dim_deriv)
        #alloc_opt = optimize_asiconly(alloc_justify, area_unalloc,
                #asic_deriv, dim_deriv, dim_max=60, asic_max=20)
        #alloc_opt = optimize_alloc2(alloc_justify, area_unalloc,
                #asic_perf, fpga_perf, dim_perf)

        print alloc_opt


    def plot(self):
        self.plot_speedup()
        self.plot_derivative()


    def plot_speedup(self):
        dfn = joinpath(self.DATA_DIR, ('%s-%d.pypkl' % (self.id, self.ucore_ratio)))
        with open(dfn, 'rb') as f:
            mean_list = pickle.load(f)

            mean_lists = []
            mean_lists.append(mean_list)

            x_lists = [x for x in xrange(self.fpga_ratio_eff+1)]
            analysis.plot_data(x_lists, mean_lists,
                    xlabel='Total ASIC allocation',
                    ylabel='Speedup (mean)',
                    title='%d%% U-core allocation'%self.ucore_ratio,
                    xlim=(0, self.fpga_ratio_eff+1),
                    figdir=self.FIG_DIR,
                    ofn='%s-%d.%s' % (self.id, self.ucore_ratio, self.fmt)
                    )

            #analysis.plot_data(self.asic_alloc, gmean_lists,
                    #xlabel='ASIC allocation in percentage',
                    #ylabel='Speedup (gmean)',
                    #legend_labels=self.accelerators,
                    #xlim=(0, 0.5),
                    #figdir=FIG_DIR,
                    #ofn='%s-gmean.png'%self.id)

            #analysis.plot_data(self.asic_alloc, hmean_lists,
                    #xlabel='ASIC allocation in percentage',
                    #ylabel='Speedup (hmean)',
                    #legend_labels=self.accelerators,
                    #xlim=(0, 0.5),
                    #figdir=FIG_DIR,
                    #ofn='%s-hmean.png'%self.id)


    def plot_derivative(self):
        dfn = joinpath(self.DATA_DIR, ('%s-%d.pypkl' % (self.id, self.ucore_ratio)))
        with open(dfn, 'rb') as f:
            mean_list = pickle.load(f)

            deriv_lists = []
            mean_len = len(mean_list)
            deriv_list = [ (mean_list[i+1]-mean_list[i]) for i in xrange(mean_len-1) ]
            deriv_lists.append(deriv_list)

            x_lists = [x+1 for x in xrange(self.fpga_ratio_eff)]
            analysis.plot_data(x_lists, deriv_lists,
                    xlabel='Total ASIC allocation',
                    ylabel='Speedup (derivative)',
                    title='%d%% U-core allocation'%self.ucore_ratio,
                    xlim=(0, self.fpga_ratio_eff+1),
                    figdir=self.FIG_DIR,
                    ofn='%s-deriv-%d.%s' % (self.id, self.ucore_ratio, self.fmt)
                    )


def verify(budget, kfn, wfn):
    kernels = kernel.load_xml(kfn)
    wld = workload.load_xml(wfn)
    #sys1 = HeterogSys(budget)
    #sys1.set_mech('HKMGS')
    #sys1.set_tech(16)
    #sys1.set_asic('_gen_fixednorm_003', 0.03)
    #sys1.set_asic('_gen_fixednorm_002', 0.02)
    #sys1.set_asic('_gen_fixednorm_005', 0.03)
    #sys1.set_asic('_gen_fixednorm_004', 0.03)
    #sys1.set_asic('_gen_fixednorm_006', 0.03)
    #sys1.realloc_gpacc(0.16)
    #sys1.use_gpacc = True

    #perfs = numpy.array([ sys1.get_perf(app)['perf'] for app in wld ])
    #mean = perfs.mean()
    #print mean

    #sys1 = HeterogSys(budget)
    #sys1.set_mech('HKMGS')
    #sys1.set_tech(16)
    ##sys1.set_asic('_gen_fixednorm_005', 0.05)
    ##sys1.set_asic('_gen_fixednorm_004', 0.05)
    #sys1.realloc_gpacc(0.30)
    #sys1.use_gpacc = True

    #perfs = numpy.array([ sys1.get_perf(app)['perf'] for app in wld ])
    #mean = perfs.mean()
    #print mean

    # seed = 80
    sys1 = HeterogSys(budget)
    sys1.set_mech('HKMGS')
    sys1.set_tech(16)
    sys1.set_asic('_gen_fixednorm_003', 0.04)
    sys1.set_asic('_gen_fixednorm_004', 0.06)
    sys1.set_asic('_gen_fixednorm_005', 0.05)
    sys1.set_asic('_gen_fixednorm_006', 0.04)
    sys1.realloc_gpacc(0.19)
    sys1.use_gpacc = True

    perfs = numpy.array([ sys1.get_perf(app)['perf'] for app in wld ])
    mean = perfs.mean()
    print '80: {mean}'.format(mean=mean)

    # seed = 70
    sys1 = HeterogSys(budget)
    sys1.set_mech('HKMGS')
    sys1.set_tech(16)
    sys1.set_asic('_gen_fixednorm_002', 0.03)
    sys1.set_asic('_gen_fixednorm_003', 0.05)
    sys1.set_asic('_gen_fixednorm_004', 0.06)
    sys1.set_asic('_gen_fixednorm_005', 0.05)
    sys1.set_asic('_gen_fixednorm_006', 0.04)
    sys1.set_asic('_gen_fixednorm_007', 0.02)
    sys1.realloc_gpacc(0.19)
    sys1.use_gpacc = True

    perfs = numpy.array([ sys1.get_perf(app)['perf'] for app in wld ])
    mean = perfs.mean()
    print '70: {mean}'.format(mean=mean)

    # seed = 60
    sys1 = HeterogSys(budget)
    sys1.set_mech('HKMGS')
    sys1.set_tech(16)
    sys1.set_asic('_gen_fixednorm_002', 0.04)
    sys1.set_asic('_gen_fixednorm_003', 0.06)
    sys1.set_asic('_gen_fixednorm_004', 0.07)
    sys1.set_asic('_gen_fixednorm_005', 0.06)
    sys1.set_asic('_gen_fixednorm_006', 0.05)
    sys1.set_asic('_gen_fixednorm_007', 0.03)
    sys1.realloc_gpacc(0.19)
    sys1.use_gpacc = True

    perfs = numpy.array([ sys1.get_perf(app)['perf'] for app in wld ])
    mean = perfs.mean()
    print '60: {mean}'.format(mean=mean)


LOGGING_LEVELS = {'critical': logging.CRITICAL,
        'error': logging.ERROR,
        'warning': logging.WARNING,
        'info': logging.INFO,
        'debug': logging.DEBUG}

def option_override(options):
    """Override cmd options by using values from configconfiguration file

    :options: option parser (already parsed from cmd line) to be overrided
    :returns: N/A

    """
    if not options.config_file:
        return

    config = ConfigParser.RawConfigParser()
    config.read(options.config_file)

    section = 'system'
    if config.has_section(section):
        try_update(config, options, section, 'budget')
        try_update(config, options, section, 'sys_area')
        try_update(config, options, section, 'sys_power')
        try_update(config, options, section, 'sys_bw')

    section = 'app'
    if config.has_section(section):
        try_update(config, options, section, 'kernels')
        try_update(config, options, section, 'workload')

    section = 'analysis'
    if config.has_section(section):
        try_update(config, options, section, 'sec')
        try_update(config, options, section, 'series')
        try_update(config, options, section, 'action')
        try_update(config, options, section, 'fmt')
        try_update(config, options, section, 'nprocs')

def build_optparser():
    # Init command line arguments parser
    parser = OptionParser()

    sys_options = OptionGroup(parser, "System Configurations")
    budget_choices = ('large', 'medium', 'small', 'custom')
    sys_options.add_option('--budget', default='large', choices=budget_choices,
            help="choose the budget from pre-defined ("
            + ",".join(budget_choices[:-1])
            + "), or 'custom' for customized budget by specifying AREA, POWER, and BANDWIDTH")
    sys_options.add_option('--sys-area', type='int', default=400, metavar='AREA',
            help='Area budget in mm^2, default: %default. This option will be discarded when budget is NOT custom')
    sys_options.add_option('--sys-power', type='int', default=100, metavar='POWER',
            help='Power budget in Watts, default: %default. This option will be discarded when budget is NOT custom')
    sys_options.add_option('--sys-bw', metavar='BANDWIDTH',
            default='45:180,32:198,22:234,16:252',
            help='Power budget in Watts, default: {%default}. This option will be discarded when budget is NOT custom')
    sys_options.add_option('--ucore-ratio', type='int',
            help='The percentage value of die area allocated to ASIC accelerators. For example, --ucore-raito=50 means 50% of total area budget is allocated to ASIC accelerators')
    parser.add_option_group(sys_options)

    app_options = OptionGroup(parser, "Application Configurations")
    app_options.add_option('--workload', metavar='FILE',
            help='workload configuration file, e.g. workload.xml')
    app_options.add_option('--kernels', metavar='FILE',
            help='kernels configuration file, e.g. kernels.xml')
    parser.add_option_group(app_options)

    anal_options = OptionGroup(parser, "Analysis options")
    section_choices = ('fpgainc',)
    anal_options.add_option('--sec', default='fpgainc',
            choices=section_choices, metavar='SECTION',
            help='choose the secitons of plotting, choose from ('
            + ','.join(section_choices)
            + '), default: %default')
    action_choices = ('analysis', 'plot')
    anal_options.add_option('-a', '--action', choices=action_choices,
            help='choose the running mode, choose from ('
            + ','.join(action_choices)
            + '), or combine actions seperated by ",". default: N/A.')
    fmt_choices = ('png', 'pdf', 'eps')
    anal_options.add_option('--fmt', default='pdf',
            choices=fmt_choices, metavar='FORMAT',
            help='choose the format of output, choose from ('
            + ','.join(fmt_choices)
            + '), default: %default')
    anal_options.add_option('--series', help='Select series')
    parser.add_option_group(anal_options)

    llevel_choices = ('info', 'debug', 'error')
    parser.add_option('-l', '--logging-level', default='info',
            choices=llevel_choices, metavar='LEVEL',
            help='Logging level of LEVEL, choose from ('
            + ','.join(llevel_choices)
            + '), default: %default')
    parser.add_option('-f', '--config-file', default='config/%s.cfg'%ANALYSIS_NAME,
            metavar='FILE', help='Use configurations in FILE, default: %default')
    parser.add_option('-n', action='store_false', dest='override', default=True,
            help='DONOT override command line options with the same one in the configuration file. '
            + 'By default, this option is NOT set, so the configuration file will override command line options.')

    return parser


def main():
    parser = build_optparser()
    (options, args) = parser.parse_args()
    option_override(options)

    logging_level = LOGGING_LEVELS.get(options.logging_level, logging.NOTSET)
    logging.basicConfig(level=logging_level)

    if options.budget == 'large':
        budget = SysLarge
    elif options.budget == 'medium':
        budget = SysMedium
    elif options.budget == 'small':
        budget = SysSmall
    elif options.budget == 'custom':
        budget = Budget(area=float(options.sys_area),
                power=float(options.sys_power),
                bw=parse_bw(options.sys_bw))
    else:
        logging.error('unknwon budget')

    if options.action:
        actions = options.action.split(',')
    else:
        logging.error('No action specified')

    if options.sec == 'multiopt':
        anl = MultiOpt(options,budget=budget)

        if 'analysis' in actions:
            anl.analyze()

        if 'plot' in actions:
            anl.plot()

        if 'verify' in actions:
            verify(budget, options.kernels, options.workload)

        if 'asiconly' in actions:
            anl.optimize_asic()



if __name__ == '__main__':
    main()
