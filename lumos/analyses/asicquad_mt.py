#!/usr/bin/env python
# encoding: utf-8

import logging
import cPickle as pickle
import itertools
import matplotlib

from lumos.model.system import HeteroSys
from lumos.model import kernel, workload
from lumos.model.budget import *
from lumos.model.kernel import UCoreParam

import analysis
from analysis import plot_data, plot_twinx, plot_series, plot_series2
from analysis import try_update, parse_bw

from optparse import OptionParser, OptionGroup
import ConfigParser
from os.path import join as joinpath
import os
import string

import multiprocessing
import Queue
import scipy.stats
import numpy
import numpy.random

try:
    from mpltools import style
    use_mpl_style = True
except ImportError:
    use_mpl_style = False

ANALYSIS_NAME = 'asicquad'
HOME = joinpath(analysis.HOME, ANALYSIS_NAME)
FIG_DIR,DATA_DIR = analysis.make_ws_dirs(ANALYSIS_NAME)


class ASICQuad(object):
    """ only one accelerators per system """

    class Worker(multiprocessing.Process):

        def __init__(self, work_queue, result_queue, budget, workload, kids):

            multiprocessing.Process.__init__(self)

            self.work_queue = work_queue
            self.result_queue = result_queue
            self.kill_received = False

            #self.asic_area_list = range(5, 91, 2)
            self.budget = budget
            self.workload = workload
            self.kids = kids

        def run(self):
            while not self.kill_received:

                try:
                    job = self.work_queue.get_nowait()
                except Queue.Empty:
                    break

                # the actual processing
                result = self.process(job)

                self.result_queue.put(result)

        def process(self, job):
            cid, config, asic_area = job
            alloc = asic_area * 0.01
            kids = self.kids
            #kfirst = k * 0.01

            sys = HeteroSys(self.budget)
            sys.set_mech('HKMGS')
            sys.set_tech(16)
            for idx,kid in enumerate(kids):
                sys.set_asic(kid, alloc*config[idx]*0.01)

            perfs = numpy.array([ sys.get_perf(app)['perf'] for app in self.workload ])
            mean = perfs.mean()
            std = perfs.std()
            gmean = scipy.stats.gmean(perfs)
            hmean = scipy.stats.hmean(perfs)

            #print '{cid}, {asic}, {perf}, {config}'.format(
                    #cid=cid,
                    #asic=asic_area,
                    #perf=mean,
                    #config=config)

            return (cid, asic_area, mean, std, gmean, hmean)


    def __init__(self, options, budget, pv=False):
        self.prefix = ANALYSIS_NAME
        self.fmt = options.fmt

        self.budget = budget

        self.pv = pv

        #self.fpga_area_list = (5, 10, 15, 20, 25, 30, 35, 40, 45, 50,
                #55, 60, 65, 70, 75, 80, 85, 90, 95)
        #self.fpga_area_list = range(5, 91)
        #self.cov_list = (0.1, 0.2, 0.3, 0.4, 0.5, 0.6)


        self.id = self.prefix

        self.num_processes = int(options.nprocs)

        #self.asic_alloc = (5, 10, 15, 20, 25, 30, 35, 40, 45)
        #self.asic_alloc = (0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.1)
        #self.kfirst_alloc = (10, 30, 50, 70, 90)
        self.asic_area_list = (5, 10, 15, 20, 30, 40)

        #self.kalloc1 = 0.1
        #self.kalloc2 = 0.3
        #self.kalloc3 = 0.6
        self.kalloc = (10, 20, 30, 40)

        #self.kid1 = '_gen_fixednorm_004'
        #self.kid2 = '_gen_fixednorm_005'
        #self.kid3 = '_gen_fixednorm_006'
        #self.kids = ('_gen_fixednorm_004','_gen_fixednorm_005','_gen_fixednorm_006')
        self.kids = ['_gen_fixednorm_00%s' % kid for kid in options.kids.split(',')]

        self.alloc_configs = (
                (10, 30, 40, 20),
                (20, 30, 40, 10),
                (10, 40, 30, 20),
                (20, 40, 30, 10),
                (25, 25, 25, 25)
                )

        self.options = options

        kernels = kernel.load_xml(options.kernels)
        self.accelerators = [k for k in kernels if k != 'dummy']
        self.workload = workload.load_xml(options.workload)

        if options.series:
            self.FIG_DIR = analysis.mk_dir(FIG_DIR, options.series)
            self.DATA_DIR = analysis.mk_dir(DATA_DIR, options.series)
        else:
            self.FIG_DIR = FIG_DIR
            self.DATA_DIR = DATA_DIR


    def analyze(self):
        asic_area_list = self.asic_area_list
        kernel_miu_list = []
        cov_list = []

        kids = self.kids
        alloc_configs = self.alloc_configs
        n_alloc_configs = len(alloc_configs)

        work_queue = multiprocessing.Queue()
        for cid in range(n_alloc_configs):
            for asic_area in asic_area_list:
                work_queue.put( (cid, alloc_configs[cid], asic_area) )

        result_queue = multiprocessing.Queue()

        for i in range(self.num_processes):
            worker = self.Worker(work_queue, result_queue, self.budget, self.workload, kids)
            worker.start()

        alloc_list = []
        acc_list = []
        mean_list = []
        std_list = []
        meandict = dict()
        stddict = dict()
        gmeandict = dict()
        hmeandict = dict()
        for i in xrange(n_alloc_configs*len(self.asic_area_list)):
            cid, asic_area, mean, std, gmean, hmean = result_queue.get()
            if cid not in meandict:
                meandict[cid] = dict()
                stddict[cid] = dict()
                gmeandict[cid] = dict()
                hmeandict[cid] = dict()
            meandict[cid][asic_area] = mean
            stddict[cid][asic_area] = std
            gmeandict[cid][asic_area] = gmean
            hmeandict[cid][asic_area] = hmean

        mean_lists = []
        std_lists = []
        gmean_lists = []
        hmean_lists = []
        for cid in xrange(n_alloc_configs):
            mean_lists.append( [ meandict[cid][asic_area] for asic_area in self.asic_area_list ])
            std_lists.append( [ stddict[cid][asic_area] for asic_area in self.asic_area_list ])
            gmean_lists.append( [ gmeandict[cid][asic_area] for asic_area in self.asic_area_list ])
            hmean_lists.append( [ hmeandict[cid][asic_area] for asic_area in self.asic_area_list ])


        #pickle.dump(self.accelerators, f)
        #pickle.dump(self.asic_alloc, f)
        dfn = joinpath(self.DATA_DIR, ('%s.pypkl' % self.id))
        with open(dfn, 'wb') as f:
            pickle.dump(mean_lists, f)
            pickle.dump(std_lists, f)
            pickle.dump(gmean_lists, f)
            pickle.dump(hmean_lists, f)

    def plot(self):
        dfn = joinpath(DATA_DIR, ('%s.pypkl' % self.id))
        with open(dfn, 'rb') as f:
            mean_lists = pickle.load(f)
            std_lists = pickle.load(f)
            gmean_lists = pickle.load(f)
            hmean_lists = pickle.load(f)

        if use_mpl_style:
            style.use('ggplot')

        x_lists = numpy.array(self.asic_area_list) * 0.01
        legend_labels=['-'.join(['%d'%a for a in alloc_config]) for alloc_config in self.alloc_configs]
        def cb_func(axes,fig):
            matplotlib.rc('xtick', labelsize=8)
            matplotlib.rc('ytick', labelsize=8)
            matplotlib.rc('legend', fontsize=8)
            axes.legend(axes.lines, legend_labels, loc='upper right',
                    title='Acc3, 4, 5, 6 alloc', bbox_to_anchor=(0.85,0.55,0.2,0.45))

        analysis.plot_data(x_lists, mean_lists,
                xlabel='Total ASIC allocation',
                ylabel='Speedup (mean)',
                xlim=(0, 0.5),
                #ylim=(127, 160),
                figsize=(4, 3),
                ms_list=(8,),
                #xlim=(0, 0.11),
                cb_func=cb_func,
                figdir=FIG_DIR,
                ofn='%s-%s.%s' % (self.id,
                    '-'.join([s[-1:] for s in self.kids]), self.fmt)
                )


LOGGING_LEVELS = {'critical': logging.CRITICAL,
        'error': logging.ERROR,
        'warning': logging.WARNING,
        'info': logging.INFO,
        'debug': logging.DEBUG}



def option_override(options):
    """Override cmd options by using values from configconfiguration file

    :options: option parser (already parsed from cmd line) to be overrided
    :returns: @todo

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
        try_update(config, options, section, 'asic_ratio')
        try_update(config, options, section, 'ker_ratio_max')

    section = 'app'
    if config.has_section(section):
        try_update(config, options, section, 'workload')
        try_update(config, options, section, 'kernels')

    section = 'analysis'
    if config.has_section(section):
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
    sys_options.add_option('--asic-ratio', type='int',
            help='The percentage value of die area allocated to ASIC accelerators. For example, --asic-raito=50 means 50% of total area budget is allocated to ASIC accelerators')
    sys_options.add_option('--ker-ratio-max', type='int',
            help='The maximum allocation for a single accelerator')
    parser.add_option_group(sys_options)

    app_options = OptionGroup(parser, "Application Configurations")
    app_options.add_option('--workload', metavar='FILE',
            help='workload configuration file, e.g. workload.xml')
    app_options.add_option('--kernels', metavar='FILE',
            help='kernels configuration file, e.g. kernels.xml')
    parser.add_option_group(app_options)

    anal_options = OptionGroup(parser, "Analysis options")
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
    anal_options.add_option('--kids', default='3,4,5,6')
    parser.add_option_group(anal_options)

    llevel_choices = ('info', 'debug', 'error')
    parser.add_option('-l', '--logging-level', default='info',
            choices=llevel_choices, metavar='LEVEL',
            help='Logging level of LEVEL, choose from ('
            + ','.join(llevel_choices)
            + '), default: %default')

    default_cfg = joinpath(HOME, '%s.cfg' % ANALYSIS_NAME)
    parser.add_option('-f', '--config-file', default=default_cfg,
            metavar='FILE', help='Use configurations in FILE, default: %default')
    parser.add_option('-n', action='store_false', dest='override', default=True,
            help='DONOT override command line options with the same one in the configuration file. '
            + 'By default, this option is NOT set, so the configuration file will override command line options.')

    return parser

def main():
    # Init command line arguments parser
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
        actions=options.action.split(',')
    else:
        logging.error("No action specified")

    anl = ASICQuad(options,budget=budget)

    if 'analysis' in actions:
        anl.analyze()
    if 'plot' in actions:
        anl.plot()

if __name__ == '__main__':
    main()
