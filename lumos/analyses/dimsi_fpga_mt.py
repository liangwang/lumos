#!/usr/bin/env python
# encoding: utf-8
"""
    An analysis of dim cores and one single FPGA.
"""

import logging
import cPickle as pickle
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator

from lumos.model.system import HeteroSys
from lumos.model import kernel, workload
from lumos.model.budget import *

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

ANALYSIS_NAME = 'dimsi_fpga'
HOME = joinpath(analysis.HOME, ANALYSIS_NAME)
FIG_DIR,DATA_DIR = analysis.make_ws_dirs(ANALYSIS_NAME)


class DimsiFPGA(object):
    """ Single ASIC accelerator with incremental area allocation """

    class Worker(multiprocessing.Process):

        def __init__(self, work_queue, result_queue,
                budget):

            multiprocessing.Process.__init__(self)

            self.work_queue = work_queue
            self.result_queue = result_queue
            self.kill_received = False

            self.budget = budget
            self.fpga_area_list = range(5, 91, 2)

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
            app = job

            #debug
            #if ker_ratio != 0 and ker_ratio != 1:
                #return (ker, ker_ratio, 0,0,0,0)
            #end of debug

            sys = HeteroSys(self.budget)
            sys.set_mech('HKMGS')
            sys.set_tech(16)
            sys.use_gpacc = True

            perf_opt = 0
            for fpga_area in self.fpga_area_list:
                sys.realloc_gpacc(0.01*fpga_area)
                ret = sys.get_perf(app=app)
                if perf_opt < ret['perf']:
                    fpga_area_opt = fpga_area
                    perf_opt = ret['perf']

            return (fpga_area_opt, app)


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

        if options.series:
            self.FIG_DIR = analysis.mk_dir(FIG_DIR, options.series)
            self.DATA_DIR = analysis.mk_dir(DATA_DIR, options.series)
        else:
            self.FIG_DIR = FIG_DIR
            self.DATA_DIR = DATA_DIR



    def analyze(self):

        work_queue = multiprocessing.Queue()
        for app in self.workload:
            work_queue.put(app)

        work_count = len(self.workload)

        result_queue = multiprocessing.Queue()

        for i in xrange(self.nprocs):
            worker = DimsiFPGA.Worker(work_queue, result_queue,
                    self.budget)
            worker.start()


        # Collect all results
        fpga_area_opt_list = []
        kernel_miu_list = []
        cov_list = []
        for i in xrange(work_count):
            area_opt, app = result_queue.get()
            fpga_area_opt_list.append(area_opt)

            kid = app.get_kernel()
            kernel_miu_list.append(kernel.kernel_pool[kid]['FPGA'].miu)

            cov = app.get_cov(kid)
            cov_list.append(cov)

        dfn = joinpath(self.DATA_DIR, ('%s.pypkl' % (self.id)))
        with open(dfn, 'wb') as f:
            pickle.dump(fpga_area_opt_list, f)
            pickle.dump(kernel_miu_list, f)
            pickle.dump(cov_list, f)

    def plot(self):
        self.plot_scatter_and_pie()


    def plot_scatter_and_pie(self):
        dfn = joinpath(self.DATA_DIR, ('%s.pypkl' % self.id))
        with open(dfn, 'rb') as f:
            fpga_area_opt_list = pickle.load(f)
            kernel_miu_list = pickle.load(f)
            cov_list = pickle.load(f)

        x = numpy.array(kernel_miu_list)
        y = numpy.array(cov_list)
        z = numpy.array(fpga_area_opt_list)

        style.use('ggplot')

        fig = plt.figure(figsize=(6, 4.5))
        axes_scatter = fig.add_subplot(111)
        surf = axes_scatter.scatter(x, y, c=z, cmap=plt.cm.gist_heat_r)
        #surf = axes_scatter.scatter(x, y, c=z)
        cb = fig.colorbar(surf, shrink=0.8)
        cb.set_label("Optimal FPGA alloation (%)")
        axes_scatter.set_xlabel('FPGA performance on kernel')
        axes_scatter.set_ylabel('Kernel coverage (%)')
        #axes_scatter.set_xlim(0,80)

        ofn = joinpath(self.FIG_DIR,
                '{id}_scatter.{fmt}'.format(id=self.id, fmt=self.fmt))
        fig.savefig(ofn, bbox_inches='tight')

        fig = plt.figure(figsize=(4.5, 4.5))
        axes_pie = fig.add_subplot(111)

        area_cluster = [ 0 for x in xrange(6) ]
        for area_opt in fpga_area_opt_list:
            if area_opt < 15:
                idx = 0
            elif area_opt > 35:
                idx = 5
            else:
                idx = int(area_opt / 5) - 2

            area_cluster[idx] = area_cluster[idx] + 1

        labels = ['< 15%', '15% ~ 20%', '20% ~ 25%', '25% ~ 30%', '30% ~ 35%', '> 30%']

        colors = plt.rcParams['axes.color_cycle']
        axes_pie.pie(area_cluster, labels=labels, colors=colors)

        ofn = joinpath(self.FIG_DIR,
                '{id}_pie.{fmt}'.format(id=self.id, fmt=self.fmt))
        fig.savefig(ofn, bbox_inches='tight')


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


class FixedArea(object):

    OPT_FPGA_AREA_MIN = 5
    OPT_FPGA_AREA_MAX = 50

    class Worker(multiprocessing.Process):

        def __init__(self, work_queue, result_queue,
                budget, fixed_area):

            multiprocessing.Process.__init__(self)

            self.work_queue = work_queue
            self.result_queue = result_queue
            self.kill_received = False

            self.budget = budget
            self.fpga_area_list = range(FixedArea.OPT_FPGA_AREA_MIN,
                    FixedArea.OPT_FPGA_AREA_MAX)
            self.fixed_area = fixed_area

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
            app = job

            sys = HeteroSys(self.budget)
            sys.set_mech('HKMGS')
            sys.set_tech(16)
            sys.use_gpacc = True

            perf_opt = 0
            perf_fixed = dict()
            for fpga_area in self.fpga_area_list:
                sys.realloc_gpacc(0.01*fpga_area)
                ret = sys.get_perf(app=app)
                if perf_opt < ret['perf']:
                    fpga_area_opt = fpga_area
                    perf_opt = ret['perf']
                for area in self.fixed_area:
                    if fpga_area == area:
                        perf_fixed[area] = ret['perf']

            perf_penalty = [ perf_fixed[area]/perf_opt for area in self.fixed_area ]

            if fpga_area_opt == FixedArea.OPT_FPGA_AREA_MAX:
                logging.warning('opt equals to the max, optimization may fail due to too small MAX')

            return (fpga_area_opt, app, perf_penalty)


    def __init__(self, options, budget):
        self.prefix = ANALYSIS_NAME

        self.fmt = options.fmt

        self.budget = budget

        self.id = self.prefix + 'fixedarea'

        self.nprocs = int(options.nprocs)

        self.options = options

        self.fixed_area = (15, 20, 25, 30)

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

        work_queue = multiprocessing.Queue()
        for app in self.workload:
            work_queue.put(app)

        work_count = len(self.workload)

        result_queue = multiprocessing.Queue()

        for i in xrange(self.nprocs):
            worker = self.Worker(work_queue, result_queue,
                    self.budget, self.fixed_area)
            worker.start()


        # Collect all results
        fpga_area_opt_list = []
        kernel_miu_list = []
        cov_list = []
        penalty_lists = dict([(area, []) for area in self.fixed_area])
        for i in xrange(work_count):
            area_opt, app, penalties = result_queue.get()
            fpga_area_opt_list.append(area_opt)

            kid = app.get_kernel()
            kernel_miu_list.append(kernel.kernel_pool[kid]['FPGA'].miu)

            cov = app.get_cov(kid)
            cov_list.append(cov)

            for area, penalty in zip(self.fixed_area, penalties):
                penalty_lists[area].append(penalty)

        dfn = joinpath(self.DATA_DIR, ('%s.pypkl' % (self.id)))
        with open(dfn, 'wb') as f:
            pickle.dump(fpga_area_opt_list, f)
            pickle.dump(kernel_miu_list, f)
            pickle.dump(cov_list, f)
            pickle.dump(penalty_lists, f)

    def plot(self):
        self.plot_scatter()

    def plot_scatter(self):
        dfn = joinpath(self.DATA_DIR, ('%s.pypkl' % self.id))
        with open(dfn, 'rb') as f:
            fpga_area_opt_list = pickle.load(f)
            kernel_miu_list = pickle.load(f)
            cov_list = pickle.load(f)
            penalty_lists = pickle.load(f)

        for area in self.fixed_area:
            fig = plt.figure(figsize=(6,4.5))
            axes = fig.add_subplot(111)
            x = numpy.arange(len(self.workload))
            axes.plot(x, penalty_lists[area], 'o')

            ofn = joinpath(self.FIG_DIR,
                    '{id}_{area}.{fmt}'.format(id=self.id,
                        area=area, fmt=self.fmt))
            fig.savefig(ofn, bbox_inches='tight')




class FPGASensitivity(object):
    """ Single ASIC accelerator with incremental area allocation """

    class Worker(multiprocessing.Process):

        def __init__(self, work_queue, result_queue,
                budget):

            multiprocessing.Process.__init__(self)

            self.work_queue = work_queue
            self.result_queue = result_queue
            self.kill_received = False

            self.budget = budget
            self.fpga_area_list = range(5, 91, 2)

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
            app = job

            #debug
            #if ker_ratio != 0 and ker_ratio != 1:
                #return (ker, ker_ratio, 0,0,0,0)
            #end of debug

            sys = HeteroSys(self.budget)
            sys.set_mech('HKMGS')
            sys.set_tech(16)
            sys.use_gpacc = True

            perf_opt = 0
            for fpga_area in self.fpga_area_list:
                sys.realloc_gpacc(0.01*fpga_area)
                ret = sys.get_perf(app=app)
                if perf_opt < ret['perf']:
                    fpga_area_opt = fpga_area
                    perf_opt = ret['perf']

            return (fpga_area_opt, app)


    def __init__(self, options, budget):
        self.prefix = ANALYSIS_NAME

        self.fmt = options.fmt

        self.budget = budget

        self.id = self.prefix

        self.nprocs = int(options.nprocs)

        self.options = options

        if options.series:
            self.FIG_DIR = analysis.mk_dir(FIG_DIR, options.series)
            self.DATA_DIR = analysis.mk_dir(DATA_DIR, options.series)
        else:
            self.FIG_DIR = FIG_DIR
            self.DATA_DIR = DATA_DIR



    def analyze(self):

        for k_tag in ('norm80x20', 'norm40x10', 'norm20x5'):
            kernels = kernel.load_xml('config/kernels_{k_tag}.xml'.format(k_tag=k_tag))

            for c_tag in ('cov40x10', 'cov20x5'):

                wld = workload.load_xml('config/workload_{k_tag}_{c_tag}.xml'.format(k_tag=k_tag, c_tag=c_tag))

                work_queue = multiprocessing.Queue()
                for app in wld:
                    work_queue.put(app)

                work_count = len(wld)

                result_queue = multiprocessing.Queue()

                for i in xrange(self.nprocs):
                    worker = self.Worker(work_queue, result_queue,
                            self.budget)
                    worker.start()


                # Collect all results
                fpga_area_opt_list = []
                kernel_miu_list = []
                cov_list = []
                for i in xrange(work_count):
                    area_opt, app = result_queue.get()
                    fpga_area_opt_list.append(area_opt)

                    kid = app.get_kernel()
                    kernel_miu_list.append(kernel.kernel_pool[kid]['FPGA'].miu)

                    cov = app.get_cov(kid)
                    cov_list.append(cov)

                dfn = joinpath(self.DATA_DIR,
                        ('{id}_{k_tag}_{c_tag}.pypkl'.format(id=self.id,
                            k_tag=k_tag, c_tag=c_tag)))

                with open(dfn, 'wb') as f:
                    pickle.dump(fpga_area_opt_list, f)
                    pickle.dump(kernel_miu_list, f)
                    pickle.dump(cov_list, f)

    def plot(self):
        self.plot_stack()


    def plot_stack(self):
        style.use('ggplot')
        ktag_list = ('norm80x20', 'norm40x10', 'norm20x5')
        ctag_list = ('cov40x10', 'cov20x5')
        series = [ '{k_tag}_{c_tag}'.format(k_tag=k_tag,c_tag=c_tag) for k_tag in ktag_list for c_tag in ctag_list ]
        xtick_labels = [ '', 'F-H', 'F-L', 'M-H',
                'M-L', 'S-H', 'S-L']
        #legend_labels = ['< 10%', '10% ~ 15%', '15% ~ 20%',
                #'20% ~ 25%', '25% ~ 30%', '30% ~ 35%',
                #'35% ~ 40%', '> 40%']
        legend_labels = ['< 10%', '10% ~ 15%', '15% ~ 20%',
                '20% ~ 25%', '25% ~ 30%', '30% ~ 35%', '> 35%']

        data = [ ]
        for s in series:
            k_tag, c_tag = s.split('_')

            dfn = joinpath(self.DATA_DIR, ('{id}_{k_tag}_{c_tag}.pypkl'.format(
                id=self.id, k_tag=k_tag, c_tag=c_tag)))

            with open(dfn, 'rb') as f:
                fpga_area_opt_list = pickle.load(f)

            area_cluster = [ 0 for x in xrange(7) ]
            for area_opt in fpga_area_opt_list:
                if area_opt < 10:
                    idx = 0
                elif area_opt > 35:
                    idx = 6
                else:
                    idx = int(area_opt / 5) - 1

                area_cluster[idx] = area_cluster[idx] + 1

            data.append(area_cluster)

        plot_data = zip(*data)
        #print data
        #print plot_data

        fig = plt.figure(figsize=(6,4.5))
        axes = fig.add_subplot(111)
        bottom = numpy.array([ 0 for x in series ])
        x = numpy.arange(0, len(series)) + 0.7
        colors = plt.rcParams['axes.color_cycle']
        bar_list=[]
        for d,c in itertools.izip(plot_data, itertools.cycle(colors)):
            b_patch = axes.bar(x, d, 0.6, bottom=bottom,color=c)
            bottom = bottom + d
            bar_list.append(b_patch)


        legend = axes.legend(bar_list, legend_labels, bbox_to_anchor=(0,1,1,.102),
                loc = 'lower left', ncol=4, prop={'size':'small'})
        #ltext = legend.get_texts()
        #plt.setp(ltext, fontsize='x-small')
        majorLocator = MultipleLocator()
        axes.xaxis.set_major_locator(majorLocator)
        #axes.set_xticklabels(xtick_labels, rotation=30)
        axes.set_xticklabels(xtick_labels)
        axes.set_ylabel('Number of Applications')

        ofn = joinpath(self.FIG_DIR,
                '{id}_stack.{fmt}'.format(
                    id=self.id, k_tag=k_tag, c_tag=c_tag, fmt=self.fmt))
        fig.savefig(ofn, bbox_inches='tight')


    def plot_scatter_and_pie(self):
        style.use('ggplot')

        for k_tag in ('norm80x20', 'norm40x10', 'norm20x5'):
            for c_tag in ('cov40x10', 'cov20x5'):
                dfn = joinpath(self.DATA_DIR, ('{id}_{k_tag}_{c_tag}.pypkl'.format(
                    id=self.id, k_tag=k_tag, c_tag=c_tag)))
                with open(dfn, 'rb') as f:
                    fpga_area_opt_list = pickle.load(f)
                    kernel_miu_list = pickle.load(f)
                    cov_list = pickle.load(f)

                x = numpy.array(kernel_miu_list)
                y = numpy.array(cov_list)
                z = numpy.array(fpga_area_opt_list)


                fig = plt.figure(figsize=(6, 4.5))
                axes_scatter = fig.add_subplot(111)
                surf = axes_scatter.scatter(x, y, c=z, cmap=plt.cm.gist_heat_r)
                #surf = axes_scatter.scatter(x, y, c=z)
                cb = fig.colorbar(surf, shrink=0.8)
                cb.set_label("Optimal FPGA alloation (%)")
                axes_scatter.set_xlabel('FPGA performance on kernel')
                axes_scatter.set_ylabel('Kernel coverage (%)')
                #axes_scatter.set_xlim(0,80)

                ofn = joinpath(self.FIG_DIR,
                        '{id}_{k_tag}_{c_tag}_scatter.{fmt}'.format(
                            id=self.id, k_tag=k_tag, c_tag=c_tag, fmt=self.fmt))
                fig.savefig(ofn, bbox_inches='tight')

                fig = plt.figure(figsize=(4.5, 4.5))
                axes_pie = fig.add_subplot(111)

                area_cluster = [ 0 for x in xrange(6) ]
                for area_opt in fpga_area_opt_list:
                    if area_opt < 15:
                        idx = 0
                    elif area_opt > 35:
                        idx = 5
                    else:
                        idx = int(area_opt / 5) - 2

                    area_cluster[idx] = area_cluster[idx] + 1

                labels = ['< 15%', '15% ~ 20%', '20% ~ 25%', '25% ~ 30%', '30% ~ 35%', '> 30%']

                colors = plt.rcParams['axes.color_cycle']
                axes_pie.pie(area_cluster, labels=labels, colors=colors)

                ofn = joinpath(self.FIG_DIR,
                        '{id}_{k_tag}_{c_tag}_pie.{fmt}'.format(
                            id=self.id, k_tag=k_tag, c_tag=c_tag, fmt=self.fmt))
                fig.savefig(ofn, bbox_inches='tight')



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

    if options.sec == 'dimsi_fpga':
        anl = DimsiFPGA(options,budget=budget)
    elif options.sec == 'fixedarea':
        anl = FixedArea(options,budget=budget)
    #elif options.sec == 'sens':
    else:
        anl = FPGASensitivity(options, budget=budget)

    if 'analysis' in actions:
        anl.analyze()
    if 'plot' in actions:
        anl.plot()


if __name__ == '__main__':
    main()
