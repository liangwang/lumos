#!/usr/bin/env python
# encoding: utf-8

import logging
import cPickle as pickle
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator

from model.system import HeteroSys
from model.core import O3Core
from model.application import App
from model import kernel, workload
from model.budget import *

import analysis
from analysis import plot_data, plot_twinx, plot_series, plot_series2
from analysis import try_update, parse_bw

from optparse import OptionParser, OptionGroup
import ConfigParser
from os.path import join as joinpath

import multiprocessing
import Queue
import scipy.stats
import numpy
from mpltools import style
import itertools

ANALYSIS_NAME = 'ioo3'
HOME = joinpath(analysis.HOME, ANALYSIS_NAME)
FIG_DIR,DATA_DIR = analysis.make_ws_dirs(ANALYSIS_NAME)


class IOO3(object):
    """ Single ASIC accelerator with incremental area allocation """

    def __init__(self, options, budget):
        self.prefix = ANALYSIS_NAME

        self.fmt = options.fmt

        self.budget = budget

        self.id = self.prefix

        self.options = options

        self.tech = options.tech

        self.appf_list = (0.1, 0.5, 0.9, 0.95, 0.99, 1)

        if options.series:
            self.FIG_DIR = analysis.mk_dir(FIG_DIR, options.series)
            self.DATA_DIR = analysis.mk_dir(DATA_DIR, options.series)
        else:
            self.FIG_DIR = FIG_DIR
            self.DATA_DIR = DATA_DIR


    def analyze(self):

        tech = self.tech
        sys_o3 = HeteroSys(self.budget, mech='HKMGS',
                           tech=tech,
                           serial_core=O3Core(mech='HKMGS',tech=tech))

        sel_core = O3Core(mech='HKMGS', tech=tech)
        area = sel_core.base_area * 2
        perf = sel_core.base_perf * 1.1
        sel_core.set_base(area=area, perf=perf)
        sys_sel = HeteroSys(self.budget, mech='HKMGS', tech=tech,
                serial_core=sel_core)

        sys_io = HeteroSys(self.budget, mech='HKMGS', tech=tech)

        apps = [ App(f=f) for f in self.appf_list ]

        sys_o3_perfs = [ sys_o3.get_perf(app)['perf'] for app in apps ]
        sys_io_perfs = [ sys_io.get_perf(app)['perf'] for app in apps ]
        sys_sel_perfs = [sys_sel.get_perf(app)['perf'] for app in apps ]

        dfn = joinpath(self.DATA_DIR, ('%s_%d.pypkl' % (self.id, self.tech)))
        with open(dfn, 'wb') as f:
            pickle.dump(sys_o3_perfs, f)
            pickle.dump(sys_io_perfs, f)
            pickle.dump(self.appf_list, f)
            pickle.dump(sys_sel_perfs, f)


    def plot(self):
        #self.plot_series()
        self.plot_relative()


    def plot_series(self):
        dfn = joinpath(self.DATA_DIR, ('%s_%d.pypkl' % (self.id, self.tech)))
        with open(dfn, 'rb') as f:
            sys_o3_perfs = pickle.load(f)
            sys_io_perfs = pickle.load(f)
            appf_list = pickle.load(f)
            sys_sel_perfs = pickle.load(f)

        style.use('ggplot')

        y_lists = [sys_o3_perfs, sys_sel_perfs, sys_io_perfs]

        ofn = joinpath(self.FIG_DIR,
                       '{id}_{tech}.{fmt}'.format(id=self.id, fmt=self.fmt,tech=self.tech))

        analysis.plot_series(appf_list, y_lists,
                xlabel='Parallel fraction',
                ylabel='Normalized performance',
                figsize=(6,4.5),
                legend_labels=['O3', 'Sel', 'IO'],
                legend_loc='lower right',
                ofn = ofn)

    def plot_relative(self):
        tech_list = (45, 32, 22, 16)
        y_lists = []
        for tech in tech_list:
            dfn = joinpath(self.DATA_DIR, ('{id}_{tech}.pypkl'.format(id=self.id, tech=tech)))
            with open(dfn, 'rb') as f:
                sys_o3_perfs = pickle.load(f)
                sys_io_perfs = pickle.load(f)
                appf_list = pickle.load(f)

            relative_perfs = [ o3_perf/io_perf for (o3_perf,io_perf) in zip(sys_o3_perfs, sys_io_perfs) ]
            y_lists.append(relative_perfs)

        ofn = joinpath(self.FIG_DIR,
                '{id}_relative.{fmt}'.format(id=self.id, fmt=self.fmt))

        style.use('ggplot')
        matplotlib.rc('legend', fontsize=10)
        matplotlib.rc('axes', labelsize=10)

        print zip(*y_lists)

        def cb_func(axes, figure):
            axes.legend(axes.lines, appf_list, loc='upper center', ncol=3,
                    title='Parallel ratio',
                    bbox_to_anchor=(0.4, 0.97, 0.2, 0.1))

        analysis.plot_series(tech_list, zip(*y_lists),
                xlabel='Technology node',
                ylabel='Normalized performance',
                ylim=(0,5),
                cb_func=cb_func,
                figsize=(4,3),
                ms_list=(6,),
                ofn=ofn)


    def plot_o3_sel(self):
        dfn = joinpath(self.DATA_DIR, ('{id}_{tech}.pypkl'.format(id=self.id, tech=self.tech)))
        with open(dfn, 'rb') as f:
            sys_o3_perfs = pickle.load(f)
            sys_io_perfs = pickle.load(f)
            appf_list = pickle.load(f)
            sys_sel_perfs = pickle.load(f)

        rel_o3 = [ o3_perf/io_perf for (o3_perf,io_perf) in zip(sys_o3_perfs, sys_io_perfs) ]
        rel_sel = [ sel_perf/io_perf for (sel_perf,io_perf) in zip(sys_sel_perfs, sys_io_perfs) ]
        y_lists = [rel_o3, rel_sel]


        style.use('ggplot')
        matplotlib.rc('legend', fontsize=10)
        matplotlib.rc('axes', labelsize=10)


        ofn = joinpath(self.FIG_DIR,
                       '{id}_o3sel_{tech}.{fmt}'.format(id=self.id, fmt=self.fmt,tech=self.tech))

        analysis.plot_series(appf_list, y_lists,
                xlabel='Technology node',
                ylabel='Normalized performance',
                #ylim=(0,5),
                legend_labels=['O3','Sel'],
                legend_loc='upper right',
                figsize=(4,3),
                ms_list=(6,),
                ofn=ofn)

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
    sys_options.add_option('--tech', type='int',
            help='Tecnology node')
    parser.add_option_group(sys_options)

    app_options = OptionGroup(parser, "Application Configurations")
    app_options.add_option('--workload', metavar='FILE',
            help='workload configuration file, e.g. workload.xml')
    app_options.add_option('--kernels', metavar='FILE',
            help='kernels configuration file, e.g. kernels.xml')
    parser.add_option_group(app_options)

    anal_options = OptionGroup(parser, "Analysis options")
    section_choices = ('ioo3',)
    anal_options.add_option('--sec', default='ioo3',
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

    default_cfg = joinpath(HOME, '%s.cfg' % ANALYSIS_NAME)
    parser.add_option('-f', '--config-file', default=default_cfg,
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

    if options.sec == 'ioo3':
        anl = IOO3(options,budget=budget)
    else:
        anl = FPGASensitivity(options, budget=budget)

    for a in actions:
        try:
            do_func = getattr(anl, a)
            do_func()
        except AttributeError as ae:
            logging.warning("No action %s supported in this analysis" % a)


if __name__ == '__main__':
    main()

