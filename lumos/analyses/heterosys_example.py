#!/usr/bin/env python
# encoding: utf-8
"""
An exmaple on using :class:`~lumos.model.system.HeterogSys`.

"""
import logging
import cPickle as pickle
import itertools
import matplotlib.pyplot as plt

from lumos.model.system import HeterogSys
from lumos.model.application import App
from lumos.model import kernel, workload
from lumos.model.budget import *
from lumos.model.kernel import UCoreParam

import analysis
from analysis import BaseAnalysis
from analysis import plot_data, plot_twinx, plot_series, plot_series2

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

ANALYSIS_NAME = 'heterosys_example'
HOME = joinpath(analysis.HOME, ANALYSIS_NAME)
FIG_DIR,DATA_DIR = analysis.make_ws_dirs(ANALYSIS_NAME)


class HeterosysExample(BaseAnalysis):
    """
    A heterogeneous many-core system with in-order cores, reconfigurable logic, and dedicated ASICs.
    """

    class Worker(multiprocessing.Process):

        def __init__(self, work_queue, result_queue, budget, workload):

            multiprocessing.Process.__init__(self)

            self.work_queue = work_queue
            self.result_queue = result_queue
            self.kill_received = False

            self.asic_area_list = range(5, 91, 2)
            self.budget = budget
            self.workload = workload

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
            a, k= job
            alloc = a * 0.01
            kfirst = k * 0.01

            sys = HeterogSys(self.budget)
            sys.set_mech('HKMGS')
            sys.set_tech(16)
            if kfirst != 0:
                sys.set_asic('_gen_fixednorm_004', alloc*kfirst*0.33)
                sys.set_asic('_gen_fixednorm_005', alloc*kfirst*0.33)
                sys.set_asic('_gen_fixednorm_006', alloc*kfirst*0.34)
            sys.realloc_gpacc(alloc*(1-kfirst))
            sys.use_gpacc = True

            perfs = numpy.array([ sys.get_perf(app)['perf'] for app in self.workload ])
            mean = perfs.mean()
            std = perfs.std()
            gmean = scipy.stats.gmean(perfs)
            hmean = scipy.stats.hmean(perfs)

            return (a, k, mean, std, gmean, hmean)


    def __init__(self, options, budget, pv=False):
        self.prefix = 'hybrid'
        self.fmt = options.fmt

        self.budget = budget

        self.pv = pv

        #self.fpga_area_list = (5, 10, 15, 20, 25, 30, 35, 40, 45, 50,
                #55, 60, 65, 70, 75, 80, 85, 90, 95)
        #self.fpga_area_list = range(5, 91)
        #self.cov_list = (0.1, 0.2, 0.3, 0.4, 0.5, 0.6)

        kernels = kernel.load_xml(options.kernels)
        self.accelerators = [k for k in kernels if k != 'dummy']
        self.workload = workload.load_xml(options.workload)

        self.id = self.prefix

        self.num_processes = int(options.nprocs)

        self.asic_alloc = (10, 20, 30, 40, 50, 60)
        #self.asic_alloc = (0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.1)
        self.kfirst_alloc = (0, 10, 30, 50, 70, 90)

        self.options = options

        if options.series:
            self.FIG_DIR = analysis.mk_dir(FIG_DIR, options.series)
            self.DATA_DIR = analysis.mk_dir(DATA_DIR, options.series)
        else:
            self.FIG_DIR = FIG_DIR
            self.DATA_DIR = DATA_DIR

    def analyze(self):
        dfn = joinpath(self.DATA_DIR, ('%s.pypkl' % self.id))
        f = open(dfn, 'wb')

        asic_area_list = []
        kernel_miu_list = []
        cov_list = []

        work_queue = multiprocessing.Queue()
        for alloc in self.asic_alloc:
            for kfirst in self.kfirst_alloc:
                work_queue.put((alloc,kfirst))

        result_queue = multiprocessing.Queue()

        for i in range(self.num_processes):
            worker = self.Worker(work_queue, result_queue,
                    self.budget, self.workload)
            worker.start()

        alloc_list = []
        acc_list = []
        mean_list = []
        std_list = []
        meandict = dict()
        stddict = dict()
        gmeandict = dict()
        hmeandict = dict()
        for i in xrange(len(self.asic_alloc)*len(self.kfirst_alloc)):
            alloc, kfirst, mean, std, gmean, hmean = result_queue.get()
            if kfirst not in meandict:
                meandict[kfirst] = dict()
                stddict[kfirst] = dict()
                gmeandict[kfirst] = dict()
                hmeandict[kfirst] = dict()
            meandict[kfirst][alloc] = mean
            stddict[kfirst][alloc] = std
            gmeandict[kfirst][alloc] = gmean
            hmeandict[kfirst][alloc] = hmean

        mean_lists = []
        std_lists = []
        gmean_lists = []
        hmean_lists = []
        for kfirst in self.kfirst_alloc:
            mean_lists.append( [ meandict[kfirst][alloc] for alloc in self.asic_alloc ])
            std_lists.append( [ stddict[kfirst][alloc] for alloc in self.asic_alloc ])
            gmean_lists.append( [ gmeandict[kfirst][alloc] for alloc in self.asic_alloc ])
            hmean_lists.append( [ hmeandict[kfirst][alloc] for alloc in self.asic_alloc ])


        pickle.dump(mean_lists, f)
        pickle.dump(std_lists, f)
        pickle.dump(gmean_lists, f)
        pickle.dump(hmean_lists, f)
        f.close()

    def plot(self):
        if use_mpl_style:
            style.use('ggplot')

        dfn = joinpath(self.DATA_DIR, ('%s.pypkl' % self.id))
        with open(dfn, 'rb') as f:
            mean_lists = pickle.load(f)
            std_lists = pickle.load(f)
            gmean_lists = pickle.load(f)
            hmean_lists = pickle.load(f)

            legend_labels=['%d%% U-Cores' % kfirst for kfirst in self.kfirst_alloc]
            legend_labels[0] = '0 (FPGA only)'
            x_list = numpy.array(self.asic_alloc) * 0.01

            fig = plt.figure(figsize=(6,4.5))
            axes = fig.add_subplot(111)

            for y, marker in itertools.izip(mean_lists, itertools.cycle(analysis.marker_cycle)):
                axes.plot(x_list, y, marker=marker, ms=8)

            axes.set_ylim(95, 165)
            axes.set_xlim(0, 0.65)
            axes.legend(axes.lines, legend_labels, loc='lower right',
                    title='Total ASIC out of Total U-Core',
                    ncol=2,
                    prop=dict(size='medium')
                    )
            axes.set_xlabel('Total U-Cores allocation')
            axes.set_ylabel('Speedup (mean)')

            ofn = '{id}_amean.{fmt}'.format(id=self.id, fmt=self.fmt)
            ofile = joinpath(self.FIG_DIR, ofn)
            fig.savefig(ofile, bbox_inches='tight')


LOGGING_LEVELS = {'critical': logging.CRITICAL,
        'error': logging.ERROR,
        'warning': logging.WARNING,
        'info': logging.INFO,
        'debug': logging.DEBUG}

def try_update(config, options, section, name):
    if config.has_option(section, name):
        setattr(options, name, config.get(section, name))


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
        if config.has_option(section, 'ucore_ratio'):
            options.ucore_ratio = config.get(section, 'ucore_ratio')
        if config.has_option(section, 'ucore_type'):
            options.ucore_type = config.get(section, 'ucore_type')
        if config.has_option(section, 'asic_config'):
            options.asic_config = config.get(section, 'asic_config')
        if config.has_option(section, 'fpga_config'):
            options.fpga_config = config.get(section, 'fpga_config')

    section = 'app'
    if config.has_section(section):
        try_update(config, options, section, 'workload')
        try_update(config, options, section, 'kernels')
        try_update(config, options, section, 'app_f')
        try_update(config, options, section, 'kernels_cfg')
        try_update(config, options, section, 'app_total_count')
        try_update(config, options, section, 'kernel_total_count')
        try_update(config, options, section, 'kernel_count_per_app')
        try_update(config, options, section, 'kernel_perf_dist')
        try_update(config, options, section, 'kernel_perf_dist_norm_mean')
        try_update(config, options, section, 'kernel_perf_dist_norm_std')
        try_update(config, options, section, 'kernel_perf_dist_lognorm_mean')
        try_update(config, options, section, 'kernel_perf_dist_lognorm_std')
        try_update(config, options, section, 'kernel_perf_dist_uniform_min')
        try_update(config, options, section, 'kernel_perf_dist_uniform_max')
        try_update(config, options, section, 'kernel_cov_dist')
        try_update(config, options, section, 'kernel_cov_dist_norm_mean')
        try_update(config, options, section, 'kernel_cov_dist_norm_std')
        try_update(config, options, section, 'kernel_cov_dist_lognorm_mean')
        try_update(config, options, section, 'kernel_cov_dist_lognorm_std')
        try_update(config, options, section, 'kernel_cov_dist_uniform_min')
        try_update(config, options, section, 'kernel_cov_dist_uniform_max')
        try_update(config, options, section, 'samples')

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
    sys_options.add_option('--ucore-ratio', default='0.1,0.3,0.5,0.7,0.9')
    sys_options.add_option('--ucore-type', default = 'GPU,FPGA,ASIC')
    sys_options.add_option('--asic-config', default = 'MMM:0.05')
    sys_options.add_option('--fpga-config', default = '20,30')
    parser.add_option_group(sys_options)

    app_options = OptionGroup(parser, "Application Configurations")

    app_options.add_option('--workload', metavar='FILE',
            help='workload configuration file, e.g. workload.xml')
    app_options.add_option('--kernels', metavar='FILE',
            help='kernels configuration file, e.g. kernels.xml')
    parser.add_option_group(app_options)

    anal_options = OptionGroup(parser, "Analysis options")
    section_choices = ('fpga', 'asic', 'hybrid')
    anal_options.add_option('--sec', default='hybrid', choices=section_choices,
            help='choose the secitons of plotting, choose from ('
            + ','.join(section_choices)
            + '), default: %default')
    action_choices = ('analysis', 'plot')
    anal_options.add_option('-a', '--action', choices=action_choices,
            help='choose the running mode, choose from ('
            + ','.join(action_choices)
            + '), or combine actions seperated by ",". default: N/A.')
    fmt_choices = ('png', 'pdf', 'eps')
    anal_options.add_option('--fmt', default='pdf', choices=fmt_choices,
            help='choose the format of output, choose from ('
            + ','.join(fmt_choices)
            + '), default: %default')
    anal_options.add_option('--kids', default='4,5,6')
    parser.add_option_group(anal_options)

    parser.add_option('-l', '--logging-level', default='info', help='Logging level')
    default_cfg = joinpath(HOME, '%s.cfg' % ANALYSIS_NAME)
    parser.add_option('-f', '--config-file', default=default_cfg,
            metavar='FILE', help='Use configurations in FILE, default: %default')

    return parser



if __name__ == '__main__':

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


    anl = HeterosysExample(options,budget=budget)


    if options.action:
        actions = options.action.split(',')
    else:
        logging.error('No action specified')

    for a in actions:
        try:
            do_func = getattr(anl, a)
            do_func()
        except AttributeError as ae:
            logging.warning("No action %s supported by this analysis" % a)
