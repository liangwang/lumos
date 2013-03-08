#!/usr/bin/env python
# encoding: utf-8

import logging
import cPickle as pickle
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from model.system import HeterogSys
from model.app import App
from model import kernel
from model.budget import *
from model.kernel import UCoreParam

import analysis
from analysis import BaseAnalysis
from analysis import plot_data, plot_twinx, plot_series, plot_series2
from analysis import FIG_DIR as FIG_BASE, DATA_DIR as DATA_BASE

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
from mpl_toolkits.mplot3d import Axes3D

FIG_DIR,DATA_DIR = analysis.make_ws('dist-fpga')

class ASICAnalysis(BaseAnalysis):

    class Worker(multiprocessing.Process):

        def __init__(self, work_queue, result_queue, budget):

            multiprocessing.Process.__init__(self)

            self.work_queue = work_queue
            self.result_queue = result_queue
            self.kill_received = False

            self.asic_area_list = range(5, 91, 2) 
            self.budget = budget

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
            asic_area_list = []
            #cov_list = scipy.stats.norm.rvs(0.4, 0.1, size=100)
            #cov_list = self.cov_list
            kid,cov = job

            app = App(f=1)
            app.reg_kernel(kid, cov)

            sys = HeterogSys(self.budget)
            sys.set_mech('HKMGS')
            sys.set_tech(16)
            #sys.use_gpacc = True

            perf_opt = 0
            for asic_area in self.asic_area_list:
                sys.set_asic(kid, 0.01*asic_area)
                ret = sys.get_perf(app=app)
                if perf_opt < ret['perf']:
                    asic_area_opt = asic_area
                    perf_opt = ret['perf']


            return (asic_area_opt, kid, cov)


    def __init__(self, fmt, app_f, app_cfg, budget, pv=False):
        self.prefix = 'asic'
        self.fmt = fmt

        self.budget = budget

        self.pv = pv

        #self.fpga_area_list = (5, 10, 15, 20, 25, 30, 35, 40, 45, 50,
                #55, 60, 65, 70, 75, 80, 85, 90, 95)
        #self.fpga_area_list = range(5, 91) 
        #self.cov_list = (0.1, 0.2, 0.3, 0.4, 0.5, 0.6)

        self.app_f = app_f
        self.app_cfg = app_cfg

        self.id = self.prefix

        self.num_processes = 15
        self.num_samples = 1000


    def analyze(self):
        dfn = joinpath(DATA_DIR, ('%s.pypkl' % self.id))
        #kernels = kernel.gen_kernel_gauss(200,30)
        #cov_list = scipy.stats.uniform.rvs(0.1, 0.7, size=20)
        cov_list = scipy.stats.norm.rvs(0.3, 0.07)
        f = open(dfn, 'wb')
        asic_area_list = []
        kernel_miu_list = []
        cov_list = []

        work_queue = multiprocessing.Queue()
        for i in xrange(self.num_samples):
            uc_miu = scipy.stats.norm.rvs(200, 30)
            while uc_miu < 0:
                uc_miu = scipy.stats.norm.rvs(200, 30)
            cov = scipy.stats.norm.rvs(0.4, 0.1)
            while cov < 0:
                cov = scipy.stats.norm.rvs(0.4, 0.1)

            kid = 'gauss%d' % (len(kernel.kernel_pool) +1)
            kernel.kernel_pool[kid] = {'ASIC': UCoreParam(miu=uc_miu)}

            work_queue.put((kid, cov))

        result_queue = multiprocessing.Queue()

        workers = []
        for i in range(self.num_processes):
            worker = Worker(work_queue, result_queue, self.budget)
            worker.start()

        for i in xrange(self.num_samples):
            area,kid, cov = result_queue.get()
            asic_area_list.append(area)
            kernel_miu_list.append(kernel.kernel_pool[kid]['ASIC'].miu)
            cov_list.append(cov)

        pickle.dump(asic_area_list, f)
        pickle.dump(kernel_miu_list, f)
        pickle.dump(cov_list, f)
        f.close()

    def plot(self):
        dfn = joinpath(DATA_DIR, ('%s.pypkl' % self.id))
        with open(dfn, 'rb') as f:
            asic_area_list = pickle.load(f)
            kernel_miu_list = pickle.load(f)
            cov_list = pickle.load(f)
            x = np.array(kernel_miu_list)
            y = np.array(cov_list)
            z = np.array(asic_area_list)
            #X, Y = np.meshgrid(x,y)
            #Z = np.array(fpga_area_lists)
            fig = plt.figure(figsize=(12,9))
            #axes = fig.add_subplot(111, projection='3d')
            axes = fig.add_subplot(111)

            surf = axes.scatter(x, y, c=z)
            cb = fig.colorbar(surf, shrink=0.8)
            cb.set_label("Optimal ASIC allocation")
            #axes.colorbar()
            axes.set_xlabel('ASIC performance on kernel')
            axes.set_ylabel('Kernel coverage (%)')
            #axes.set_xlim(0.05, 0.65)
            #axes.set_ylim(0, 35)
            ofn = joinpath(FIG_DIR, 'asic.png')
            fig.savefig(ofn, bbox_inches='tight')


class FPGAAnalysis(BaseAnalysis):

    class Worker(multiprocessing.Process):

        def __init__(self, work_queue, result_queue, budget):

            multiprocessing.Process.__init__(self)

            self.work_queue = work_queue
            self.result_queue = result_queue
            self.kill_received = False

            self.fpga_area_list = range(5, 91, 2) 
            self.budget = budget

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
            fpga_area_list = []
            #cov_list = scipy.stats.norm.rvs(0.4, 0.1, size=100)
            #cov_list = self.cov_list
            kid,cov = job

            app = App(f=1)
            app.reg_kernel(kid, cov)

            sys = HeterogSys(self.budget)
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


            return (fpga_area_opt, kid, cov)

    def __init__(self, fmt, budget, options, pv=False):
        self.prefix = 'fpga'
        self.fmt = fmt

        self.budget = budget

        self.pv = pv

        #self.fpga_area_list = (5, 10, 15, 20, 25, 30, 35, 40, 45, 50,
                #55, 60, 65, 70, 75, 80, 85, 90, 95)
        #self.fpga_area_list = range(5, 91) 
        #self.cov_list = (0.1, 0.2, 0.3, 0.4, 0.5, 0.6)

        self.app_f = float(options.app_f)

        self.id = self.prefix

        self.num_processes = int(options.nprocs)
        self.num_samples = int(options.samples)

        self.options = options

    def random_uc_perf(self):
        options = self.options
        if options.kernel_perf_dist == 'norm':
            mean = float(options.kernel_perf_dist_norm_mean)
            std = float(options.kernel_perf_dist_norm_std)
            r = scipy.stats.norm.rvs(mean, std)
            while r < 0:
                r = scipy.stats.norm.rvs(mean, std)
        elif options.kernel_perf_dist == 'lognorm':
            mean = float(options.kernel_perf_dist_lognorm_mean)
            std = float(options.kernel_perf_dist_lognorm_std)
            r = numpy.random.lognormal(mean, std)
        elif options.kernel_perf_dist == 'uniform':
            rmin = float(options.kernel_perf_dist_uniform_min)
            rmax = float(options.kernel_perf_dist_uniform_max)
            r = scipy.stats.uniform.rvs(rmin, rmax)
            while r < 0:
                r = scipy.stats.uniform.rvs(rmin,rmax)
        return r

    def random_uc_cov(self):
        options = self.options
        if options.kernel_cov_dist == 'norm':
            mean = float(options.kernel_cov_dist_norm_mean)
            std = float(options.kernel_cov_dist_norm_std)
            r = scipy.stats.norm.rvs(mean, std)
            while r < 0:
                r = scipy.stats.norm.rvs(mean, std)
        elif options.kernel_cov_dist == 'lognorm':
            mean = float(options.kernel_cov_dist_lognorm_mean)
            std = float(options.kernel_cov_dist_lognorm_std)
            r = numpy.random.lognormal(mean, std)
        elif options.kernel_cov_dist == 'uniform':
            rmin = float(options.kernel_cov_dist_uniform_min)
            rmax = float(options.kernel_cov_dist_uniform_max)
            r = scipy.stats.uniform.rvs(rmin, rmax)
            while r < 0:
                r = scipy.stats.uniform.rvs(rmin,rmax)
        return r

    def analyze(self):
        dfn = joinpath(DATA_DIR, ('%s.pypkl' % self.id))
        #kernels = kernel.gen_kernel_gauss(80,10)
        #cov_list = scipy.stats.uniform.rvs(0.1, 0.7, size=20)
        #cov_list = scipy.stats.norm.rvs(0.4, 0.1)
        f = open(dfn, 'wb')
        fpga_area_list = []
        kernel_miu_list = []
        cov_list = []

        work_queue = multiprocessing.Queue()
        for i in xrange(self.num_samples):
            uc_perf = self.random_uc_perf()
            uc_cov = self.random_uc_cov()

            kid = 'gauss%d' % (len(kernel.kernel_pool) +1)
            kernel.kernel_pool[kid] = {'FPGA': UCoreParam(miu=uc_perf)}

            work_queue.put((kid, uc_cov))

        result_queue = multiprocessing.Queue()

        workers = []
        for i in range(self.num_processes):
            worker = FPGAAnalysis.Worker(work_queue, result_queue, self.budget)
            worker.start()

        for i in xrange(self.num_samples):
            area,kid,cov = result_queue.get()
            fpga_area_list.append(area)
            kernel_miu_list.append(kernel.kernel_pool[kid]['FPGA'].miu)
            cov_list.append(cov)

        pickle.dump(fpga_area_list, f)
        pickle.dump(kernel_miu_list, f)
        pickle.dump(cov_list, f)
        f.close()

    def plot(self):
        dfn = joinpath(DATA_DIR, ('%s.pypkl' % self.id))
        with open(dfn, 'rb') as f:
            fpga_area_list = pickle.load(f)
            kernel_miu_list = pickle.load(f)
            cov_list = pickle.load(f)
            x = numpy.array(kernel_miu_list)
            y = numpy.array(cov_list)
            z = numpy.array(fpga_area_list)
            #X, Y = np.meshgrid(x,y)
            #Z = np.array(fpga_area_lists)
            fig = plt.figure(figsize=(12,9))
            #axes = fig.add_subplot(111, projection='3d')
            axes = fig.add_subplot(111)

            surf = axes.scatter(x, y, c=z)
            cb = fig.colorbar(surf, shrink=0.8)
            cb.set_label("Optimal FPGA allocation")
            #axes.colorbar()
            axes.set_xlabel('FPGA performance on kernel')
            axes.set_ylabel('Kernel coverage (%)')
            #if self.options.kernel_perf_dist == 'lognorm':
                #axes.set_xscale('log')
            #axes.set_xlim(0.05, 0.65)
            #axes.set_ylim(0, 35)
            ofn = joinpath(FIG_DIR, 'fpga.png')
            fig.savefig(ofn, bbox_inches='tight')


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
        if config.has_option(section, 'ucore_ratio'):
            options.ucore_ratio = config.get(section, 'ucore_ratio')
        if config.has_option(section, 'ucore_type'):
            options.ucore_type = config.get(section, 'ucore_type')
        if config.has_option(section, 'budget'):
            options.budget = config.get(section, 'budget')
        if config.has_option(section, 'asic_config'):
            options.asic_config = config.get(section, 'asic_config')
        if config.has_option(section, 'fpga_config'):
            options.fpga_config = config.get(section, 'fpga_config')

    section = 'app'
    if config.has_section(section):
        try_update(config, options, section, 'app_f')
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
        if config.has_option(section, 'sec'):
            options.sec = config.get('analysis', 'sec')
        if config.has_option(section, 'mode'):
            options.mode=config.get('analysis', 'mode')
        if config.has_option(section, 'fmt'):
            options.fmt=config.get('analysis', 'fmt')
        try_update(config, options, section, 'nprocs')

def main():
    # Init command line arguments parser
    parser = OptionParser()

    sys_options = OptionGroup(parser, "System Configurations")
    sys_options.add_option('--sys-area', type='int', default=400)
    sys_options.add_option('--sys-power', type='int', default=100)
    sys_options.add_option('--ucore-ratio', default='0.1,0.3,0.5,0.7,0.9')
    sys_options.add_option('--ucore-type', default = 'GPU,FPGA,ASIC')
    sys_options.add_option('--asic-config', default = 'MMM:0.05')
    sys_options.add_option('--fpga-config', default = '20,30')
    sys_options.add_option('--budget', default='large')
    parser.add_option_group(sys_options)

    app_options = OptionGroup(parser, "Application Configurations")
    ###### obsolete options #####
    #app_choices = ('MMM', 'BS', 'FFT')
    #app_options.add_option('--app', default='MMM', choices=app_choices,
            #help='choose the workload, choose from ('
            #+ ','.join(app_choices)
            #+ '), default: %default')
    #app_options.add_option('--fratio', default='0,90,10')
    #############################

    app_options.add_option('--app-f', type='int', default=90)
    app_options.add_option('--kernels', default='MMM:5,BS:5')
    parser.add_option_group(app_options)

    anal_options = OptionGroup(parser, "Analysis options")
    section_choices = ('fpga', 'asic')
    anal_options.add_option('--sec', default='fpga', choices=section_choices,
            help='choose the secitons of plotting, choose from ('
            + ','.join(section_choices)
            + '), default: %default')
    mode_choices = ('a', 'p', 'ap')
    anal_options.add_option('--mode', default='p', choices=mode_choices,
            help='choose the running mode, choose from ('
            + ','.join(mode_choices)
            + '), default: %default')
    fmt_choices = ('png', 'pdf', 'eps')
    anal_options.add_option('--fmt', default='pdf', choices=fmt_choices,
            help='choose the format of output, choose from ('
            + ','.join(fmt_choices)
            + '), default: %default')
    parser.add_option_group(anal_options)

    parser.add_option('-l', '--logging-level', default='info', help='Logging level')
    parser.add_option('-f', '--config-file', default='dist-fpga.cfg',
            help='Use configurations in the specified file')


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
    else:
        logging.error('unknwon budget')


    if options.sec == 'fpga':
        anl = FPGAAnalysis(fmt=options.fmt, pv=False, budget=budget, options=options)
        anl.do(options.mode)
    elif options.sec == 'asic':
        anl = ASICAnalysis(options, budget=budget, pv=False)
        anl.do(options.mode)


if __name__ == '__main__':
    main()
