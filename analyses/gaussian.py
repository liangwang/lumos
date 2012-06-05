#!/usr/bin/env python
# encoding: utf-8

import logging
import cPickle as pickle
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from model.system import HeteroSys
from model.app import App
from model import kernel
from model.budget import *

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
import numpy as np
from mpl_toolkits.mplot3d import Axes3D

FIG_DIR,DATA_DIR = analysis.make_ws('dist')

class Worker(multiprocessing.Process):

    def __init__(self, work_queue, result_queue, budget, cov_list):

        multiprocessing.Process.__init__(self)

        self.work_queue = work_queue
        self.result_queue = result_queue
        self.kill_received = False

        self.fpga_area_list = range(5, 91, 2) 
        self.budget = budget
        self.cov_list = cov_list

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
        cov_list = self.cov_list
        kid,jid = job
        for cov in cov_list:
            app = App(f=1)
            app.reg_kernel(kid, cov)

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

            fpga_area_list.append(fpga_area_opt)

        return (fpga_area_list, jid)


class FPGAAnalysis(BaseAnalysis):
    def __init__(self, fmt, app_f, app_cfg, budget, pv=False):
        self.prefix = 'fpga'
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


    def analyze(self):
        dfn = joinpath(DATA_DIR, ('%s.pypkl' % self.id))
        kernels = kernel.gen_kernel_gauss(80,20,50)
        #cov_list = scipy.stats.uniform.rvs(0.1, 0.7, size=20)
        cov_list = scipy.stats.norm.rvs(0.4, 0.1, size=20)
        f = open(dfn, 'wb')
        fpga_area_lists = []
        kernel_miu_list = []
        cov_lists = []

        work_queue = multiprocessing.Queue()
        id = 0
        for kid in kernels:
            work_queue.put((kid, id))
            id = id + 1
            fpga_area_lists.append([])
            k = kernels[kid]
            kernel_miu_list.append(k['FPGA'].miu)

        result_queue = multiprocessing.Queue()

        workers = []
        for i in range(self.num_processes):
            worker = Worker(work_queue, result_queue, self.budget, cov_list)
            worker.start()
            workers.append(worker)

        #for worker in workers:
            #worker.join()

        for kid in kernels:
            area,jid = result_queue.get()
            fpga_area_lists[jid]=area

        pickle.dump(fpga_area_lists, f)
        pickle.dump(kernel_miu_list, f)
        pickle.dump(cov_list, f)
        f.close()

    def plot(self):
        dfn = joinpath(DATA_DIR, ('%s.pypkl' % self.id))
        with open(dfn, 'rb') as f:
            fpga_area_lists = pickle.load(f)
            kernel_miu_list = pickle.load(f)
            cov_list = pickle.load(f)
            x = np.array(kernel_miu_list)
            y = np.array(cov_list)
            X, Y = np.meshgrid(x,y)
            Z = np.array(fpga_area_lists)
            fig = plt.figure(figsize=(12,9))
            #axes = fig.add_subplot(111, projection='3d')
            axes = fig.add_subplot(111)

            surf = axes.scatter(X.flatten(),Y.flatten(),c=Z.flatten())
            cb = fig.colorbar(surf, shrink=0.8)
            cb.set_label("Optimal FPGA allocation")
            #axes.colorbar()
            axes.set_xlabel('FPGA performance on kernel')
            axes.set_ylabel('Kernel coverage (%)')
            #axes.set_xlim(0.05, 0.65)
            #axes.set_ylim(0, 35)
            ofn = joinpath(FIG_DIR, 'fpga.png')
            fig.savefig(ofn, bbox_inches='tight')


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
        if config.has_option(section, 'app_f'):
            options.app_f = config.getint(section, 'app_f')
        if config.has_option(section, 'kernels'):
            options.kernels = config.get(section, 'kernels')
        if config.has_option(section, 'app_cfg'):
            options.app_cfg = config.get(section, 'app_cfg')

    section = 'analysis'
    if config.has_section(section):
        if config.has_option(section, 'sec'):
            options.sec = config.get('analysis', 'sec')
        if config.has_option(section, 'mode'):
            options.mode=config.get('analysis', 'mode')
        if config.has_option(section, 'fmt'):
            options.fmt=config.get('analysis', 'fmt')

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
    section_choices = ('type', 'area')
    anal_options.add_option('--sec', default='area', choices=section_choices,
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
    parser.add_option('-f', '--config-file', default='hetero.cfg',
            help='Use configurations in the specified file')


    (options, args) = parser.parse_args()
    option_override(options)

    logging_level = LOGGING_LEVELS.get(options.logging_level, logging.NOTSET)
    logging.basicConfig(level=logging_level)

    uratio_list = [ (float(r)) for r in options.ucore_ratio.split(',')]
    utype_list = [ (string.upper(r)) for r in options.ucore_type.split(',')]

    if options.budget == 'large':
        budget = SysLarge
    elif options.budget == 'medium':
        budget = SysMedium
    elif options.budget == 'small':
        budget = SysSmall
    else:
        logging.error('unknwon budget')

    #app = App(f=(options.app_f/100))
    #for kernel in options.kernels.split(','):
        #k0,k1 = kernel.split(':')
        #kid = k0
        #cov = 0.01 * int(k1)
        #app.reg_kernel(kid, cov)


    if options.sec == 'fpga':
        anl = FPGAAnalysis(fmt=options.fmt, pv=False, budget=budget, app_f=options.app_f, app_cfg=options.app_cfg)
        anl.do(options.mode)


if __name__ == '__main__':
    main()
