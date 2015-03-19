#!/usr/bin/env python
from lumos.analysis import LumosAnalysisError
from lumos.model.ptm_new.system import MPSoC, HetSys
# from lumos.model.ptm_new.application import Application
from lumos.model.ptm_new import IOCore_CMOS, O3Core_CMOS, IOCore_TFET, O3Core_TFET
from lumos.model.ptm_new import Accelerator, Budget, CMOSTechModel, TFETTechModel
from lumos.model.ptm_new import Sys_L, Sys_M, Sys_S
from lumos.model.ptm_new.kernel import load_kernels
from lumos.model.ptm_new.workload import load_workload
from lumos.model.ptm_new.plot import plot_data, plot_twinx, plot_series, plot_series2
from lumos.model.ptm_new.misc import try_update, parse_bw, make_ws_dirs, mk_dir

import time
import csv
import logging
from itertools import product
from optparse import OptionParser, OptionGroup
import configparser
from os.path import join as joinpath
import os


import multiprocessing as mp
import queue

ANALYSIS_NAME = os.path.basename(os.path.dirname(__file__))
HOME = os.path.abspath(os.path.dirname(__file__))
_logger = logging.getLogger(ANALYSIS_NAME)
_logger.setLevel(logging.INFO)


def worker_func(work_queue, result_queue, options, workload, kernels):
    start = time.time()
    jobs_processed = 0
    if options.budget == 'large':
        budget = Sys_L
    elif options.budget == 'medium':
        budget = Sys_M
    elif options.budget == 'small':
        budget = Sys_S
    elif options.budget == 'custom':
        budget = Budget(
            area=float(options.sys_area),
            power=float(options.sys_power),
            bw=parse_bw(options.sys_bw))
    else:
        _logger.error('unknwon budget')

    while True:
        try:
            job = work_queue.get_nowait()
            asic_perf, asic_alloc = job
        except queue.Empty:
            break

        if options.thru_core == 'IOCore_CMOS':
            tput_core = IOCore_CMOS(tech=22)
        elif options.thru_core == 'IOCore_TFET':
            tput_core = IOCore_TFET(tech=22)
        else:
            raise LumosAnalysisError(
                'Unknown throughput core type {0}'.format(options.thru_core))
            break

        sys = MPSoC(budget, tech=22, tput_core=tput_core)

        alloc = int(asic_alloc) * 0.01
        aid = 'asic_{0}x'.format(asic_perf)
        kernel = kernels['ker']
        sys.set_asic(kernel, aid, alloc, CMOSTechModel('hp'))

        asic_cov_list = parse_num_list(options.asic_cov)
        if not asic_cov_list:
            print('Failed to parse number list from '
                  'options.asic_cov: {0}'.format(options.asic_cov))
            break

        for cov in asic_cov_list:
            for f_parallel in options.f_parallel.split(','):
                app_name = 'app_f{0}_c{1}'.format(f_parallel, cov)
                perf = sys.get_perf(workload[app_name])['perf']
                result_queue.put((f_parallel, cov, asic_alloc, asic_perf, perf))
        jobs_processed += 1
        work_queue.task_done()
    end = time.time()
    print('worker finishes {0} jobs in {1} seconds, exit'.format(jobs_processed, end-start))


class ASICQuad(object):
    """ only one accelerators per system """
    def __init__(self, options):
        self.prefix = ANALYSIS_NAME
        self.fmt = options.fmt

        self.id = self.prefix

        self.num_processes = int(options.nprocs)

        self.options = options

        self.kernels = load_kernels(os.path.join(
            os.path.abspath(os.path.dirname(__file__)), options.kernels))
        self.workload = load_workload(self.kernels, os.path.join(
            os.path.abspath(os.path.dirname(__file__)), options.workload))

    def run(self):
        job_q = mp.JoinableQueue()
        result_q = mp.Queue()

        asic_alloc_list = parse_num_list(self.options.asic_alloc)
        if not asic_alloc_list:
            print('Failed to parse number list from options.asic_alloc: {0}'.format(
                self.options.asic_alloc))
            return

        asic_cov_list = parse_num_list(self.options.asic_cov)
        if not asic_cov_list:
            print('Failed to parse number list from options.asic_cov: {0}'.format(
                self.options.asic_cov))

        for asic_alloc in asic_alloc_list:
            for asic_perf in self.options.asic_perf.split(','):
                job_q.put((asic_perf, asic_alloc))

        num_procs = min(len(asic_alloc_list), self.num_processes)

        for _ in range(num_procs):
            mp.Process(target=worker_func, args=(
                job_q, result_q, self.options, self.workload, self.kernels)).start()

        job_q.join()

        results_dict = dict()
        while True:
            try:
                f, cov, alloc, asic_perf, perf = result_q.get_nowait()
                results_dict[(f, cov, alloc, asic_perf)] = perf
            except queue.Empty:
                break

        resultf = open(os.path.join(
            os.path.abspath(os.path.dirname(__file__)), 'results.csv'), 'w')
        fieldnames = ('f_parallel', 'asic_cov', 'asic_alloc', 'asic_perf', 'sys_perf')
        csvwriter = csv.DictWriter(resultf, fieldnames=fieldnames)
        csvwriter.writerow(dict((fn, fn) for fn in fieldnames))

        for f, cov, alloc, asic_perf in product(self.options.f_parallel.split(','),
                                                asic_cov_list, asic_alloc_list,
                                                self.options.asic_perf.split(',')):
            perf = results_dict[(f, cov, alloc, asic_perf)]
            row = {'f_parallel': f,
                   'asic_cov': cov,
                   'asic_alloc': alloc,
                   'asic_perf': asic_perf,
                   'sys_perf': perf}
            csvwriter.writerow(row)

        resultf.close()


def option_override(options):
    """Override cmd options by using values from configconfiguration file

    :options: option parser (already parsed from cmd line) to be overrided
    :returns: @todo

    """
    if not options.config_file:
        _logger.warning('config file {0} not found'.format(options.config_file))
        return

    config = configparser.RawConfigParser()
    config.read(options.config_file)

    section = 'system'
    if config.has_section(section):
        try_update(config, options, section, 'budget')
        try_update(config, options, section, 'sys_area')
        try_update(config, options, section, 'sys_power')
        try_update(config, options, section, 'sys_bw')
        try_update(config, options, section, 'thru_core')

    section = 'app'
    if config.has_section(section):
        try_update(config, options, section, 'workload')
        try_update(config, options, section, 'kernels')

    section = 'explore-variables'
    if config.has_section(section):
        try_update(config, options, section, 'f_parallel')
        try_update(config, options, section, 'asic_cov')
        try_update(config, options, section, 'asic_perf')
        try_update(config, options, section, 'asic_alloc')

    section = 'analysis'
    if config.has_section(section):
        try_update(config, options, section, 'series')
        try_update(config, options, section, 'action')
        try_update(config, options, section, 'fmt')
        try_update(config, options, section, 'nprocs')


def parse_num_list(line):
    """ A number list can be specified as:

    1. enumeration: 1,2,3,4
    2. range: 1:5 -> 1,2,3,4,5
    3. range with step: 1:5:2 -> 1,3,5
    4. a mix of the above three, the mix should keep the orders, so
       1,2,3:10,12:20:2,30 is legitimate, while 1,2,3,1:10 is not.

    Args:
        line (str):
            input string

    Return:
        list, a list of numbers (numbers are encoded as string)
    """
    num_list = []
    for s in line.split(','):
        if ':' in s:
            range_params = s.split(':')
            num_params = len(range_params)
            if num_params == 2:
                start = int(range_params[0])
                end = int(range_params[1])
                step = 1
            elif num_params == 3:
                start = int(range_params[0])
                end = int(range_params[1])
                step = int(range_params[2])
            else:
                print('Unknown range pattern {0}'.format(s))
                return None
            num_list.extend([str(x) for x in range(start, end+step, step)])
        else:
            try:
                dummy = int(s)
            except ValueError:
                print('Unknown number, expect integer, but given {0}'.format(s))
                return None
            num_list.append(s)

    return num_list


def build_optparser():
    # Init command line arguments parser
    parser = OptionParser()

    sys_options = OptionGroup(parser, "System Configurations")
    budget_choices = ('large', 'medium', 'small', 'custom')
    sys_options.add_option(
        '--budget', default='large', choices=budget_choices,
        help="choose the budget from pre-defined (" + ",".join(budget_choices[:-1]) +
        "), or 'custom' for customized budget by specifying AREA, POWER, and BANDWIDTH")
    sys_options.add_option(
        '--sys-area', type='int', default=400, metavar='AREA',
        help='Area budget in mm^2, default: %default. '
        'This option will be discarded when budget is NOT custom')
    sys_options.add_option(
        '--sys-power', type='int', default=100, metavar='POWER',
        help='Power budget in Watts, default: %default. '
        'This option will be discarded when budget is NOT custom')
    sys_options.add_option(
        '--sys-bw', metavar='BANDWIDTH', default='45:180,32:198,22:234,16:252',
        help='Power budget in Watts, default: {%default}. '
        'This option will be discarded when budget is NOT custom')
    thru_core_choices = ('IOCore', 'IOCore_TFET')
    sys_options.add_option(
        '--thru-core', default='IOCore', choices=thru_core_choices,
        help='The core type of throughput cores, options are (' +
        ",".join(thru_core_choices[:-1]) + ")")
    parser.add_option_group(sys_options)

    app_options = OptionGroup(parser, "Application Configurations")
    app_options.add_option(
        '--workload', metavar='FILE', help='workload configuration file, e.g. workload.xml')
    app_options.add_option(
        '--kernels', metavar='FILE', help='kernels configuration file, e.g. kernels.xml')
    parser.add_option_group(app_options)

    expl_options = OptionGroup(parser, "Explore Variables")
    expl_options.add_option('--f-parallel', help='list of values for f_parallel')
    # expl_options.add_option('--asic-cov', help='list of values for ASIC coverage')
    # expl_options.add_option('--asic-perf', help='list of values for ASIC performance')
    # expl_options.add_option('--asic-alloc', help='list of values for ASIC allocation')
    parser.add_option_group(expl_options)

    anal_options = OptionGroup(parser, "Analysis options")
    # action_choices = ('analysis', 'plot')
    # anal_options.add_option(
    #     '-a', '--action', choices=action_choices, help='choose the running mode, choose from (' +
    #     ','.join(action_choices) + '), or combine actions seperated by ",". default: N/A.')
    fmt_choices = ('png', 'pdf', 'eps')
    anal_options.add_option(
        '--fmt', default='pdf', choices=fmt_choices, metavar='FORMAT',
        help='choose the format of output, choose from (' +
        ','.join(fmt_choices) + '), default: %default')
    anal_options.add_option('--series', help='Select series')
    anal_options.add_option('--kids', default='3,4,5,6')
    parser.add_option_group(anal_options)

    llevel_choices = ('info', 'debug', 'error')
    parser.add_option(
        '-l', '--logging-level', default='info', choices=llevel_choices, metavar='LEVEL',
        help='Logging level of LEVEL, choose from (' +
        ','.join(llevel_choices) + '), default: %default')

    default_cfg = joinpath(HOME, 'default.cfg')
    parser.add_option(
        '-f', '--config-file', default=default_cfg, metavar='FILE',
        help='Use configurations in FILE, default: %default')
    parser.add_option(
        '-n', action='store_false', dest='override', default=True,
        help='DONOT override command line options with the same one in the configuration file. '
        'By default, this option is NOT set, so the configuration file will override command '
        'line options.')

    return parser


if __name__ == '__main__':
    # Init command line arguments parser
    parser = build_optparser()

    (options, args) = parser.parse_args()
    option_override(options)

    LOGGING_LEVELS = {
        'critical': logging.CRITICAL,
        'error': logging.ERROR,
        'warning': logging.WARNING,
        'info': logging.INFO,
        'debug': logging.DEBUG}
    logging_level = LOGGING_LEVELS.get(options.logging_level, logging.NOTSET)
    _logger.setLevel(logging_level)

    # if options.action:
    #     actions=options.action.split(',')
    # else:
    #     _logger.error("No action specified")

    anl = ASICQuad(options).run()

    # if 'analysis' in actions:
    # anl.analyze()
    # if 'plot' in actions:
    #     anl.plot()
