#!/usr/bin/env python
# encoding: utf-8

import logging
import cPickle as pickle
#import matplotlib
#matplotlib.use('Agg')
import matplotlib.pyplot as plt

from model.system import HeteroSys
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

ANALYSIS_NAME = 'asicinc'
HOME = joinpath(analysis.HOME, ANALYSIS_NAME)
FIG_DIR,DATA_DIR = analysis.make_ws_dirs(ANALYSIS_NAME)


class ASICInc(object):
    """ Single ASIC accelerator with incremental area allocation """

    class Worker(multiprocessing.Process):

        def __init__(self, work_queue, result_queue,
                budget, workload, asic_ratio):

            multiprocessing.Process.__init__(self)

            self.work_queue = work_queue
            self.result_queue = result_queue
            self.kill_received = False

            self.budget = budget
            self.workload = workload
            self.asic_ratio = asic_ratio

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
            ker, ker_ratio = job

            #debug
            #if ker_ratio != 0 and ker_ratio != 1:
                #return (ker, ker_ratio, 0,0,0,0)
            #end of debug

            asic_alloc = self.asic_ratio * 0.01
            ker_alloc = ker_ratio * 0.01
            dummy_alloc = (self.asic_ratio - ker_ratio) * 0.01

            sys = HeteroSys(self.budget)
            sys.set_mech('HKMGS')
            sys.set_tech(16)
            sys.set_asic(ker, ker_alloc)
            sys.set_asic('dummy', dummy_alloc)
            #sys.use_gpacc = True

            perfs = numpy.array([ sys.get_perf(app)['perf'] for app in self.workload ])

            #debug
            #perf_list = []
            #for app in self.workload:
                #perf = sys.get_perf(app)['perf']
                #perf_list.append(perf)
                #if ker == '_gen_fixednorm_001' and perf > 106 and perf < 107:
                    #print app.name, perf
            #perfs = numpy.array(perf_list)
            #print ker, ker_ratio
            #print perfs

            #end of debug

            mean = perfs.mean()
            std = perfs.std()
            gmean = scipy.stats.gmean(perfs)
            hmean = scipy.stats.hmean(perfs)

            return (ker, ker_ratio, mean, std, gmean, hmean)


    def __init__(self, options, budget):
        self.prefix = ANALYSIS_NAME

        self.fmt = options.fmt

        self.budget = budget

        self.id = self.prefix

        self.nprocs = int(options.nprocs)

        self.options = options

        kernels = kernel.load_xml(options.kernels)
        self.accelerators = [k for k in kernels if k != 'dummy']
        self.workload = workload.load_xml(options.workload)

        self.asic_ratio = int(options.asic_ratio)
        ker_ratio_max = int(options.ker_ratio_max)
        self.asic_ratio_eff = min(self.asic_ratio, ker_ratio_max)

        if options.series:
            self.FIG_DIR = analysis.mk_dir(FIG_DIR, options.series)
            self.DATA_DIR = analysis.mk_dir(DATA_DIR, options.series)
        else:
            self.FIG_DIR = FIG_DIR
            self.DATA_DIR = DATA_DIR



    def analyze(self):
        dfn = joinpath(self.DATA_DIR, ('%s-%d.pypkl' % (self.id, self.asic_ratio)))
        f = open(dfn, 'wb')

        work_queue = multiprocessing.Queue()
        work_count = 0
        for ker in self.accelerators:
            for ker_ratio in xrange(self.asic_ratio_eff+1):
                work_queue.put( (ker, ker_ratio) )
                work_count = work_count + 1


        result_queue = multiprocessing.Queue()

        for i in xrange(self.nprocs):
            worker = ASICInc.Worker(work_queue, result_queue,
                    self.budget, self.workload, self.asic_ratio)
            worker.start()

        # Initialize result lists
        mean_dict = dict()
        for ker in self.accelerators:
            mean_dict[ker] = [-1 for x in xrange(self.asic_ratio_eff+1)]

        # Collect all results
        for i in xrange(work_count):
            ker, ker_alloc, mean, std, gmean, hmean = result_queue.get()
            mean_dict[ker][ker_alloc] = mean

        pickle.dump(mean_dict, f)
        f.close()

    def plot(self):
        self.plot_speedup()
        self.plot_derivative()


    def plot_speedup(self):
        dfn = joinpath(self.DATA_DIR, ('%s-%d.pypkl' % (self.id, self.asic_ratio)))
        with open(dfn, 'rb') as f:
            mean_dict = pickle.load(f)

            mean_lists = []
            for ker in self.accelerators:
                mean_lists.append(mean_dict[ker][:self.asic_ratio_eff+1])

            x_lists = [x for x in xrange(self.asic_ratio_eff+1)]
            analysis.plot_data(x_lists, mean_lists,
                    xlabel='Total ASIC allocation',
                    ylabel='Speedup (mean)',
                    legend_labels=[ accl[-1:] for accl in self.accelerators ],
                    title='%d%% ASIC allocation'%self.asic_ratio,
                    xlim=(0, self.asic_ratio_eff+1),
                    figdir=self.FIG_DIR,
                    ofn='%s-%d.%s' % (self.id, self.asic_ratio, self.fmt)
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
        dfn = joinpath(self.DATA_DIR, ('%s-%d.pypkl' % (self.id, self.asic_ratio)))
        with open(dfn, 'rb') as f:
            mean_dict = pickle.load(f)

            mean_lists = []
            for ker in self.accelerators:
                mean_lists.append(mean_dict[ker])

            deriv_lists = []
            for mean_list in mean_lists:
                #deriv_list = [ (mean_list[i+1]-mean_list[i]) for i in xrange(self.asic_ratio) ][:10]
                deriv_list = [ (mean_list[i+1]-mean_list[i]) for i in xrange(self.asic_ratio_eff) ][:self.asic_ratio_eff]
                deriv_lists.append(deriv_list)

            #x_lists = [x+1 for x in xrange(self.asic_ratio)][:10]
            x_lists = [x+1 for x in xrange(self.asic_ratio_eff)]
            analysis.plot_data(x_lists, deriv_lists,
                    xlabel='Total ASIC allocation',
                    ylabel='Speedup (derivative)',
                    legend_labels=[ accl[-1:] for accl in self.accelerators ],
                    title='%d%% ASIC allocation'%self.asic_ratio,
                    xlim=(0, self.asic_ratio_eff+1),
                    #xlim=(0, 11),
                    figdir=self.FIG_DIR,
                    ofn='%s-deriv-%d.%s' % (self.id, self.asic_ratio, self.fmt)
                    )

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
        try_update(config, options, section, 'asic_ratio')
        try_update(config, options, section, 'ker_ratio_max')

    section = 'app'
    if config.has_section(section):
        try_update(config, options, section, 'workload')
        try_update(config, options, section, 'kernels')

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
    section_choices = ('asicinc',)
    anal_options.add_option('--sec', default='asicinc',
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

    if options.sec == 'asicinc':
        anl = ASICInc(options,budget=budget)
        if 'analysis' in actions:
            anl.analyze()
        if 'plot' in actions:
            anl.plot()

if __name__ == '__main__':
    main()
