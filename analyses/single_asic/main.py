#!/usr/bin/env python

from lumos.model.ptm_new.system import HetSys
from lumos.model.ptm_new.application import Application
from lumos.model.ptm_new.core import *
from lumos.model.ptm_new.budget import *
from lumos.model.ptm_new.kernel import UCoreParam, Kernel
from lumos.model.ptm_new.plot import plot_data, plot_twinx, plot_series, plot_series2
from lumos.model.ptm_new.misc import try_update, parse_bw, make_ws_dirs, mk_dir

from lxml import etree
import csv

import logging


from optparse import OptionParser, OptionGroup
import ConfigParser
from os.path import join as joinpath
import os


import multiprocessing
import Queue

# from configobj import ConfigObj
# from validate import Validator
# def integer_list_ext(value, length):
#     """ A number list can be specified as:

#     1. enumeration: 1,2,3,4
#     2. range: 1:5 -> 1,2,3,4,5
#     3. range with step: 1:5:2 -> 1,3,5
#     4. a mix of the above three, the mix should keep the orders, so 1,2,3:10,12:20:2,30 is legitimate, while
#        1,2,3,1:10 is not.

#     Args:
#         line (str):
#             input string

#     Return:
#         list, a list of numbers (numbers are encoded as string)
#     """
#     num_list = []
#     for s in line.split(','):
#         if ':' in s:
#             range_params = s.split(':')
#             num_params = len(range_params)
#             if num_params == 2:
#                 start = int(range_params[0])
#                 end = int(range_params[1])
#                 step = 1
#             elif num_params == 3:
#                 start = int(range_params[0])
#                 end = int(range_params[1])
#                 step = int(range_params[2])
#             else:
#                 print 'Unknown range pattern {0}'.format(s)
#                 return None
#             num_list.extend([str(x) for x in xrange(start, end+step, step)])
#         else:
#             try:
#                 dummy = int(s)
#             except ValueError:
#                 print 'Unknown number, expect integer, but given {0}'.format(s)
#                 return None
#             num_list.append(s)

#     return num_list


ANALYSIS_NAME = os.path.basename(os.path.dirname(__file__))
HOME = os.path.abspath(os.path.dirname(__file__))
_logger = logging.getLogger(ANALYSIS_NAME)
_logger.setLevel(logging.INFO)


def load_kernel(fname='norm.xml'):
    """
    Load kernels from an XML file. 

    Args:
       fname (str):
          The file to be loaded

    Returns:
       kernels (list):
          A sorted (by name) list of kernels that have been loaded.
    """
    tree = etree.parse(fname)
    kernels = dict()
    for k_root in tree.iter('kernel'):
        k_name = k_root.get('name')
        k = Kernel(k_name)

        accelerator_root = k_root.find('accelerator')
        for ele in accelerator_root.getchildren():
            acc_id = ele.tag
            ucore_param = UCoreParam()
            for attr,val in ele.items():
                try:
                    setattr(ucore_param, attr, float(val))
                except ValueError:
                    print '(attr, val): {0}, {1}, val is not a float'.format(attr, val)
                except TypeError as te:
                    print te

            k.add_acc(acc_id, ucore_param)

        kernels[k_name] = k
    return kernels


def load_workload(kernels, fname='workload.xml'):
    """
    Load a workload from an XML file

    Args:
       fname (str):
          The XML file to be loaded

    Returns:
       workload (dict):
          A dict of applications this workload contains, indexed by application name
    """
    workload = dict()
    tree = etree.parse(fname)
    for app_root in tree.iter('app'):
        app_name = app_root.get('name')

        ele = app_root.find('f_parallel')
        f_parallel = float(ele.text)
        app = Application(f=f_parallel, name=app_name)

        kcfg_root = app_root.find('kernel_config')
        for k_ele in kcfg_root.iter('kernel'):
            kid = k_ele.get('name')
            kernel = kernels[kid]
            cov = float(k_ele.get('cov'))
            app.add_kernel(kernel, cov)

        workload[app_name] = app

    return workload



class ASICQuad(object):
    """ only one accelerators per system """

    class Worker(multiprocessing.Process):

        def __init__(self, work_queue, result_queue, options, workload, kernels):

            multiprocessing.Process.__init__(self)

            self.work_queue = work_queue
            self.result_queue = result_queue
            self.kill_received = False

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
                _logger.error('unknwon budget')

            self.budget = budget
            self.options = options
            self.workload = workload
            self.kernels = kernels

        def run(self):
            while not self.kill_received:
                try:
                    job = self.work_queue.get_nowait()
                except Queue.Empty:
                    break

                if self.options.thru_core == 'IOCore':
                    tput_core = IOCore(tech=22)
                    print 'CMOS IOCore as throughput cores'
                elif self.options.thru_core == 'IOCore_TFET':
                    tput_core = IOCore_TFET(tech=22)
                    print 'TFET IOCore as throughput cores'
                else:
                    print 'Unknown throughput core type {0}'.format(self.options.thru_core)
                    break

                sys = HetSys(self.budget, tech=22, tput_core=tput_core)
                asic_perf, asic_alloc = job
                alloc = int(asic_alloc) * 0.01
                aid = 'asic_{0}x'.format(asic_perf)
                kernel = self.kernels['ker']
                sys.set_asic(kernel, aid, alloc)

                asic_cov_list = parse_num_list(self.options.asic_cov)
                if not asic_cov_list:
                    print 'Failed to parse number list from options.asic_cov: {0}'.format(self.options.asic_cov)
                    break

                for cov in asic_cov_list:
                    for f_parallel in self.options.f_parallel.split(','):
                        app_name = 'app_f{0}_c{1}'.format(f_parallel, cov)
                        perf = sys.get_perf(self.workload[app_name])['perf']
                        self.result_queue.put((f_parallel, cov, asic_alloc, asic_perf, perf))


    def __init__(self, options):
        self.prefix = ANALYSIS_NAME
        self.fmt = options.fmt

        self.id = self.prefix

        self.num_processes = int(options.nprocs)

        self.options = options

        self.kernels = load_kernel(os.path.join(
            os.path.abspath(os.path.dirname(__file__)), options.kernels))
        self.workload = load_workload(self.kernels, os.path.join(
            os.path.abspath(os.path.dirname(__file__)), options.workload))


    def analyze(self):
        work_queue = multiprocessing.Queue()

        asic_alloc_list = parse_num_list(self.options.asic_alloc)
        if not asic_alloc_list:
            print 'Failed to parse number list from options.asic_alloc: {0}'.format(self.options.asic_alloc)
            return

        asic_cov_list = parse_num_list(self.options.asic_cov)
        if not asic_cov_list:
            print 'Failed to parse number list from options.asic_cov: {0}'.format(self.options.asic_cov)


        for asic_alloc in asic_alloc_list:
            for asic_perf in self.options.asic_perf.split(','):
                work_queue.put((asic_perf, asic_alloc))

        result_queue = multiprocessing.Queue()
        num_procs = min(len(asic_alloc_list), self.num_processes)

        for i in xrange(num_procs):
            worker = self.Worker(work_queue, result_queue, self.options, self.workload, self.kernels)
            worker.start()


        for i in range(num_procs):
            worker.join()

        resultf = open(os.path.join(
            os.path.abspath(os.path.dirname(__file__)),'results.csv'), 'wb')
        fieldnames = ('f_parallel', 'asic_cov', 'asic_alloc', 'asic_perf', 'sys_perf')
        csvwriter = csv.DictWriter(resultf, fieldnames=fieldnames)
        csvwriter.writerow(dict((fn, fn) for fn in fieldnames))
        results_dict = dict()
        while True:
            try:
                result = result_queue.get_nowait()
            except Queue.Empty:
                break

            f_parallel, cov, asic_alloc, asic_perf, perf = result
            results_dict[(f_parallel, cov, asic_alloc, asic_perf)] = perf

        for f_parallel in self.options.f_parallel.split(','):
            for cov in asic_cov_list:
                for asic_alloc in asic_alloc_list:
                    for asic_perf in self.options.asic_perf.split(','):
                        perf = results_dict[(f_parallel, cov, asic_alloc, asic_perf)]
                        row = {'f_parallel': f_parallel,
                               'asic_cov': cov,
                               'asic_alloc': asic_alloc,
                               'asic_perf': asic_perf,
                               'sys_perf': perf}
                        csvwriter.writerow(row)

        resultf.close()


    def plot(self):
        pass
        # dfn = joinpath(DATA_DIR, ('%s.pypkl' % self.id))
        # with open(dfn, 'rb') as f:
        #     mean_lists = pickle.load(f)
        #     std_lists = pickle.load(f)
        #     gmean_lists = pickle.load(f)
        #     hmean_lists = pickle.load(f)

        # x_lists = numpy.array(self.asic_area_list) * 0.01
        # # legend_labels=['-'.join(['%d'%a for a in alloc_config]) for alloc_config in self.alloc_configs]
        # def cb_func(axes,fig):
        #     matplotlib.rc('xtick', labelsize=8)
        #     matplotlib.rc('ytick', labelsize=8)
        #     matplotlib.rc('legend', fontsize=8)
        #     axes.legend(axes.lines, legend_labels, loc='upper right',
        #             title='Acc3, 4, 5, 6 alloc', bbox_to_anchor=(0.85,0.55,0.2,0.45))

        # plot_data(x_lists, mean_lists,
        #         xlabel='Total ASIC allocation',
        #         ylabel='Speedup (mean)',
        #         xlim=(0, 0.5),
        #         #ylim=(127, 160),
        #         figsize=(4, 3),
        #         ms_list=(8,),
        #         #xlim=(0, 0.11),
        #         cb_func=cb_func,
        #         figdir=FIG_DIR,
        #         ofn='%s-%s.%s' % (self.id,
        #             '-'.join([s[-1:] for s in self.kids]), self.fmt)
        #         )


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
        _logger.warning('config file {0} not found'.format(options.config_file))
        return

    config = ConfigParser.RawConfigParser()
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
    4. a mix of the above three, the mix should keep the orders, so 1,2,3:10,12:20:2,30 is legitimate, while
       1,2,3,1:10 is not.

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
                print 'Unknown range pattern {0}'.format(s)
                return None
            num_list.extend([str(x) for x in xrange(start, end+step, step)])
        else:
            try:
                dummy = int(s)
            except ValueError:
                print 'Unknown number, expect integer, but given {0}'.format(s)
                return None
            num_list.append(s)

    return num_list

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
    thru_core_choices = ('IOCore', 'IOCore_TFET')
    sys_options.add_option('--thru-core', default='IOCore', choices=thru_core_choices,
            help='The core type of throughput cores, options are ('
            + ",".join(thru_core_choices[:-1]) + ")")
    parser.add_option_group(sys_options)

    app_options = OptionGroup(parser, "Application Configurations")
    app_options.add_option('--workload', metavar='FILE',
            help='workload configuration file, e.g. workload.xml')
    app_options.add_option('--kernels', metavar='FILE',
            help='kernels configuration file, e.g. kernels.xml')
    parser.add_option_group(app_options)

    expl_options = OptionGroup(parser, "Explore Variables")
    expl_options.add_option('--f-parallel', help='list of values for f_parallel')
    # expl_options.add_option('--asic-cov', help='list of values for ASIC coverage')
    # expl_options.add_option('--asic-perf', help='list of values for ASIC performance')
    # expl_options.add_option('--asic-alloc', help='list of values for ASIC allocation')
    parser.add_option_group(expl_options)

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

    default_cfg = joinpath(HOME, 'default.cfg')
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
    _logger.setLevel(logging_level)



    if options.action:
        actions=options.action.split(',')
    else:
        _logger.error("No action specified")

    anl = ASICQuad(options)

    if 'analysis' in actions:
        anl.analyze()
    if 'plot' in actions:
        anl.plot()

if __name__ == '__main__':
    main()

