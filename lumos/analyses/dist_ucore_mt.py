#!/usr/bin/env python
# encoding: utf-8

import logging
import cPickle as pickle
import itertools
#import matplotlib
#matplotlib.use('Agg')
import matplotlib.pyplot as plt

from lumos.model.system import HeteroSys
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
from mpl_toolkits.mplot3d import Axes3D

try:
    from mpltools import style
    use_mpl_style = True
except ImportError:
    use_mpl_style = False

ANALYSIS_NAME = 'dist_ucore'
HOME = joinpath(analysis.HOME, ANALYSIS_NAME)
FIG_DIR,DATA_DIR = analysis.make_ws_dirs(ANALYSIS_NAME)


class Hybrid(BaseAnalysis):
    """ only one accelerators per system """

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

            sys = HeteroSys(self.budget)
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


        #pickle.dump(self.accelerators, f)
        #pickle.dump(self.asic_alloc, f)
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

            #fig = plt.figure(figsize=(12,9))
            #axes = fig.add_subplot(111)

            #x = numpy.array(self.asic_alloc)
            #for mean, std in zip(mean_lists, std_lists):
            #for mean, std in zip(mean_lists[0:1], std_lists[0:1]):
                #y = numpy.array(mean)
                #err = numpy.array(std)

                #axes.errorbar(x, y, yerr=err)
                #axes.plot(x, y)
            #y = numpy.array(cov_list)
            #z = numpy.array(asic_area_list)
            #X, Y = np.meshgrid(x,y)
            #Z = np.array(fpga_area_lists)
            #axes = fig.add_subplot(111, projection='3d')

            #surf = axes.scatter(x, y, c=z)
            #cb = fig.colorbar(surf, shrink=0.8)
            #cb.set_label("Optimal ASIC allocation")
            #axes.set_xlabel('ASIC allocation in percentage')
            #axes.set_ylabel('Speedup (mean)')
            #axes.set_xlim(0, 0.11)
            #axes.legend(axes.lines, self.accelerators)
            #axes.set_ylim(0, 35)
            #ofn = joinpath(FIG_DIR, '%s.png'%self.id)
            #fig.savefig(ofn, bbox_inches='tight')
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
            #analysis.plot_data(x_lists, mean_lists,
                    #xlabel='Total U-Cores allocation',
                    #ylabel='Speedup (mean)',
                    #legend_labels=['%d%% U-Cores' % kfirst for kfirst in self.kfirst_alloc],
                    #legend_title='Total ASIC out\nof Total U-Core',
                    #legend_loc='lower center',
                    #xlim=(0, 0.65),
                    #ylim=(95, 160),
                    ##xlim=(0, 0.11),
                    ##title = 'ASICs: acc4(50%) + acc5(50%)',
                    #figdir=FIG_DIR,
                    #ofn='%s-amean.%s'%(self.id,self.fmt))

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

class ASICQuad(BaseAnalysis):
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
            print job
            alloc = asic_area * 0.01
            kids = self.kids
            #kfirst = k * 0.01

            sys = HeteroSys(self.budget)
            sys.set_mech('HKMGS')
            sys.set_tech(16)
            for idx in xrange(3):
                sys.set_asic(kids[idx], alloc*config[idx]*0.01)
            #sys.set_asic('_gen_fixednorm_004', alloc*kfirst)
            #sys.set_asic('_gen_fixednorm_005', alloc*(1-kfirst))
            #sys.use_gpacc = True

            perfs = numpy.array([ sys.get_perf(app)['perf'] for app in self.workload ])
            mean = perfs.mean()
            std = perfs.std()
            gmean = scipy.stats.gmean(perfs)
            hmean = scipy.stats.hmean(perfs)

            return (cid, asic_area, mean, std, gmean, hmean)


    def __init__(self, options, budget, pv=False):
        self.prefix = 'asictriple'
        self.fmt = options.fmt

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

        #self.asic_alloc = (5, 10, 15, 20, 25, 30, 35, 40, 45)
        #self.asic_alloc = (0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.1)
        #self.kfirst_alloc = (10, 30, 50, 70, 90)
        self.asic_area_list = (5, 10, 20, 30, 40)

        #self.kalloc1 = 0.1
        #self.kalloc2 = 0.3
        #self.kalloc3 = 0.6
        self.kalloc = (10, 30, 60)

        #self.kid1 = '_gen_fixednorm_004'
        #self.kid2 = '_gen_fixednorm_005'
        #self.kid3 = '_gen_fixednorm_006'
        #self.kids = ('_gen_fixednorm_004','_gen_fixednorm_005','_gen_fixednorm_006')
        self.kids = ['_gen_fixednorm_00%s' % kid for kid in options.kids.split(',')]

        self.alloc_configs = ( (self.kalloc[0],self.kalloc[1],self.kalloc[2]),
                (self.kalloc[0],self.kalloc[2],self.kalloc[1]),
                (self.kalloc[1],self.kalloc[0],self.kalloc[2]),
                (self.kalloc[1],self.kalloc[2],self.kalloc[0]),
                (self.kalloc[2],self.kalloc[1],self.kalloc[0]),
                (self.kalloc[2],self.kalloc[0],self.kalloc[1]),
                (33, 33, 34))

        self.ker_perf_mean = float(options.kernel_perf_dist_norm_mean)
        self.ker_perf_std = float(options.kernel_perf_dist_norm_std)
        self.ker_num = int(options.kernel_total_count)
        self.app_num = int(options.app_total_count)
        self.ker_count_per_app = float(options.kernel_count_per_app)
        self.options = options

        kernel_cfg = options.kernels_cfg
        self.accelerators = kernel.load(kernel_cfg)


    def analyze(self):
        dfn = joinpath(self.DATA_DIR, ('%s.pypkl' % self.id))
        f = open(dfn, 'wb')

        self.workload = workload.load_xml(self.options.workload)
        asic_area_list = self.asic_area_list
        kernel_miu_list = []
        cov_list = []

        kalloc = self.kalloc
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

            #fig = plt.figure(figsize=(12,9))
            #axes = fig.add_subplot(111)

            #x = numpy.array(self.asic_alloc)
            #for mean, std in zip(mean_lists, std_lists):
            #for mean, std in zip(mean_lists[0:1], std_lists[0:1]):
                #y = numpy.array(mean)
                #err = numpy.array(std)

                #axes.errorbar(x, y, yerr=err)
                #axes.plot(x, y)
            #y = numpy.array(cov_list)
            #z = numpy.array(asic_area_list)
            #X, Y = np.meshgrid(x,y)
            #Z = np.array(fpga_area_lists)
            #axes = fig.add_subplot(111, projection='3d')

            #surf = axes.scatter(x, y, c=z)
            #cb = fig.colorbar(surf, shrink=0.8)
            #cb.set_label("Optimal ASIC allocation")
            #axes.set_xlabel('ASIC allocation in percentage')
            #axes.set_ylabel('Speedup (mean)')
            #axes.set_xlim(0, 0.11)
            #axes.legend(axes.lines, self.accelerators)
            #axes.set_ylim(0, 35)
            #ofn = joinpath(FIG_DIR, '%s.png'%self.id)
            #fig.savefig(ofn, bbox_inches='tight')
            x_lists = numpy.array(self.asic_area_list) * 0.01
            analysis.plot_data(x_lists, mean_lists,
                    xlabel='Total ASIC allocation',
                    ylabel='Speedup (mean)',
                    legend_labels=['-'.join(['%d'%a for a in alloc_config]) for alloc_config in self.alloc_configs],
                    title=','.join([s[-3:] for s in self.kids]),
                    xlim=(0, 0.42),
                    ylim=(127, 155),
                    figsize=(6, 4.5),
                    #xlim=(0, 0.11),
                    figdir=self.FIG_DIR,
                    ofn='%s-%s.%s' % (self.id,
                        '-'.join([s[-1:] for s in self.kids]), self.fmt)
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




class ASICTriple(BaseAnalysis):
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
            print job
            alloc = asic_area * 0.01
            kids = self.kids
            #kfirst = k * 0.01

            sys = HeteroSys(self.budget)
            sys.set_mech('HKMGS')
            sys.set_tech(16)
            for idx in xrange(3):
                sys.set_asic(kids[idx], alloc*config[idx]*0.01)
            #sys.set_asic('_gen_fixednorm_004', alloc*kfirst)
            #sys.set_asic('_gen_fixednorm_005', alloc*(1-kfirst))
            #sys.use_gpacc = True

            perfs = numpy.array([ sys.get_perf(app)['perf'] for app in self.workload ])
            mean = perfs.mean()
            std = perfs.std()
            gmean = scipy.stats.gmean(perfs)
            hmean = scipy.stats.hmean(perfs)

            return (cid, asic_area, mean, std, gmean, hmean)


    def __init__(self, options, budget, pv=False):
        self.prefix = 'asictriple'
        self.fmt = options.fmt

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

        #self.asic_alloc = (5, 10, 15, 20, 25, 30, 35, 40, 45)
        #self.asic_alloc = (0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.1)
        #self.kfirst_alloc = (10, 30, 50, 70, 90)
        self.asic_area_list = (5, 10, 20, 30, 40)

        #self.kalloc1 = 0.1
        #self.kalloc2 = 0.3
        #self.kalloc3 = 0.6
        self.kalloc = (10, 30, 60)

        #self.kid1 = '_gen_fixednorm_004'
        #self.kid2 = '_gen_fixednorm_005'
        #self.kid3 = '_gen_fixednorm_006'
        #self.kids = ('_gen_fixednorm_004','_gen_fixednorm_005','_gen_fixednorm_006')
        self.kids = ['_gen_fixednorm_00%s' % kid for kid in options.kids.split(',')]

        self.alloc_configs = ( (self.kalloc[0],self.kalloc[1],self.kalloc[2]),
                (self.kalloc[0],self.kalloc[2],self.kalloc[1]),
                (self.kalloc[1],self.kalloc[0],self.kalloc[2]),
                (self.kalloc[1],self.kalloc[2],self.kalloc[0]),
                (self.kalloc[2],self.kalloc[1],self.kalloc[0]),
                (self.kalloc[2],self.kalloc[0],self.kalloc[1]),
                (33, 33, 34))

        self.ker_perf_mean = float(options.kernel_perf_dist_norm_mean)
        self.ker_perf_std = float(options.kernel_perf_dist_norm_std)
        self.ker_num = int(options.kernel_total_count)
        self.app_num = int(options.app_total_count)
        self.ker_count_per_app = float(options.kernel_count_per_app)
        self.options = options

        kernel_cfg = options.kernels_cfg
        self.accelerators = kernel.load(kernel_cfg)

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
            r = numpy.random.uniform(rmin, rmax)
            while r < 0:
                r = numpy.random.uniform(rmin,rmax)
        return r

    def build_app(self, cov, occ, probs):
        active_kernels = dict()
        psum=0
        for o,p,acc in zip(occ, probs, self.accelerators):
            if o:
                active_kernels[p] = acc
                psum = psum + p

        ksorted = sorted(active_kernels.items())
        krever = ksorted[:]
        krever.reverse()
        app = App(f=1)

        for (p,acc),(prv,acc2) in zip(ksorted, krever):
            kcov = cov * prv / psum
            app.reg_kernel(acc, kcov)

        return app


    def build_workload(self):
        """Build workload composed by apps

        :size: @todo
        :returns: @todo

        """

        workload = []

        #options = self.options
        #ker_perf_mean = self.ker_perf_mean
        #ker_perf_std = self.ker_perf_std
        app_num = self.app_num
        #ker_num = self.ker_num
        #ker_count_per_app = self.ker_count_per_app

        #rvs = numpy.linspace(0.5*ker_perf_mean, 1.5*ker_perf_mean, ker_num-1)
        #cdfs = scipy.stats.norm.cdf(rvs, ker_perf_mean, ker_perf_std)
        #probs1 = numpy.insert(cdfs,0,0)
        #probs2 = numpy.append(cdfs, 1)
        #probs = (probs2-probs1) * ker_count_per_app

        #probs = numpy.linspace(0.9, 0.1, ker_num)

        probs = [ kernel.kernel_pool[kid]['occur'] for kid in self.accelerators ]
        kernel_occ_probs = [ scipy.stats.bernoulli.rvs(p, size=app_num) for p in probs ]
        for occ in zip(*kernel_occ_probs):
            if occ.count(1) > 0:
                cov = self.random_uc_cov()
                workload.append(self.build_app(cov, occ, probs))

        self.workload = workload

    def analyze(self):
        dfn = joinpath(self.DATA_DIR, ('%s.pypkl' % self.id))
        f = open(dfn, 'wb')

        #self.build_workload()
        self.workload = workload.load_xml(self.options.workload)
        asic_area_list = self.asic_area_list
        kernel_miu_list = []
        cov_list = []

        kalloc = self.kalloc
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

            #fig = plt.figure(figsize=(12,9))
            #axes = fig.add_subplot(111)

            #x = numpy.array(self.asic_alloc)
            #for mean, std in zip(mean_lists, std_lists):
            #for mean, std in zip(mean_lists[0:1], std_lists[0:1]):
                #y = numpy.array(mean)
                #err = numpy.array(std)

                #axes.errorbar(x, y, yerr=err)
                #axes.plot(x, y)
            #y = numpy.array(cov_list)
            #z = numpy.array(asic_area_list)
            #X, Y = np.meshgrid(x,y)
            #Z = np.array(fpga_area_lists)
            #axes = fig.add_subplot(111, projection='3d')

            #surf = axes.scatter(x, y, c=z)
            #cb = fig.colorbar(surf, shrink=0.8)
            #cb.set_label("Optimal ASIC allocation")
            #axes.set_xlabel('ASIC allocation in percentage')
            #axes.set_ylabel('Speedup (mean)')
            #axes.set_xlim(0, 0.11)
            #axes.legend(axes.lines, self.accelerators)
            #axes.set_ylim(0, 35)
            #ofn = joinpath(FIG_DIR, '%s.png'%self.id)
            #fig.savefig(ofn, bbox_inches='tight')
            x_lists = numpy.array(self.asic_area_list) * 0.01
            analysis.plot_data(x_lists, mean_lists,
                    xlabel='Total ASIC allocation',
                    ylabel='Speedup (mean)',
                    legend_labels=['-'.join(['%d'%a for a in alloc_config]) for alloc_config in self.alloc_configs],
                    title=','.join([s[-3:] for s in self.kids]),
                    xlim=(0, 0.42),
                    ylim=(127, 155),
                    figsize=(6, 4.5),
                    #xlim=(0, 0.11),
                    figdir=self.FIG_DIR,
                    ofn='%s-%s.%s' % (self.id,
                        '-'.join([s[-1:] for s in self.kids]), self.fmt)
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




class ASICDual(BaseAnalysis):
    """ only one accelerators per system """

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

            sys = HeteroSys(self.budget)
            sys.set_mech('HKMGS')
            sys.set_tech(16)
            sys.set_asic('_gen_fixednorm_004', alloc*kfirst)
            sys.set_asic('_gen_fixednorm_005', alloc*(1-kfirst))
            #sys.use_gpacc = True

            perfs = numpy.array([ sys.get_perf(app)['perf'] for app in self.workload ])
            mean = perfs.mean()
            std = perfs.std()
            gmean = scipy.stats.gmean(perfs)
            hmean = scipy.stats.hmean(perfs)

            return (a, k, mean, std, gmean, hmean)


    def __init__(self, options, budget, pv=False):
        self.prefix = 'asicdual'
        self.fmt = options.fmt

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

        self.asic_alloc = (5, 10, 15, 20, 25, 30, 35, 40, 45)
        #self.asic_alloc = (0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.1)
        self.kfirst_alloc = (10, 30, 50, 70, 90)

        self.ker_perf_mean = float(options.kernel_perf_dist_norm_mean)
        self.ker_perf_std = float(options.kernel_perf_dist_norm_std)
        self.ker_num = int(options.kernel_total_count)
        self.app_num = int(options.app_total_count)
        self.ker_count_per_app = float(options.kernel_count_per_app)
        self.options = options

        kernel_cfg = options.kernels_cfg
        self.accelerators = kernel.load(kernel_cfg)

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
            r = numpy.random.uniform(rmin, rmax)
            while r < 0:
                r = numpy.random.uniform(rmin,rmax)
        return r

    def build_app(self, cov, occ, probs):
        active_kernels = dict()
        psum=0
        for o,p,acc in zip(occ, probs, self.accelerators):
            if o:
                active_kernels[p] = acc
                psum = psum + p

        ksorted = sorted(active_kernels.items())
        krever = ksorted[:]
        krever.reverse()
        app = App(f=1)

        for (p,acc),(prv,acc2) in zip(ksorted, krever):
            kcov = cov * prv / psum
            app.reg_kernel(acc, kcov)

        return app


    def build_workload(self):
        """Build workload composed by apps

        :size: @todo
        :returns: @todo

        """

        workload = []

        #options = self.options
        #ker_perf_mean = self.ker_perf_mean
        #ker_perf_std = self.ker_perf_std
        app_num = self.app_num
        #ker_num = self.ker_num
        #ker_count_per_app = self.ker_count_per_app

        #rvs = numpy.linspace(0.5*ker_perf_mean, 1.5*ker_perf_mean, ker_num-1)
        #cdfs = scipy.stats.norm.cdf(rvs, ker_perf_mean, ker_perf_std)
        #probs1 = numpy.insert(cdfs,0,0)
        #probs2 = numpy.append(cdfs, 1)
        #probs = (probs2-probs1) * ker_count_per_app

        #probs = numpy.linspace(0.9, 0.1, ker_num)

        probs = [ kernel.kernel_pool[kid]['occur'] for kid in self.accelerators ]
        kernel_occ_probs = [ scipy.stats.bernoulli.rvs(p, size=app_num) for p in probs ]
        for occ in zip(*kernel_occ_probs):
            if occ.count(1) > 0:
                cov = self.random_uc_cov()
                workload.append(self.build_app(cov, occ, probs))

        self.workload = workload

    def analyze(self):
        dfn = joinpath(self.DATA_DIR, ('%s.pypkl' % self.id))
        f = open(dfn, 'wb')

        self.build_workload()
        asic_area_list = []
        kernel_miu_list = []
        cov_list = []

        work_queue = multiprocessing.Queue()
        for alloc in self.asic_alloc:
            for kfirst in self.kfirst_alloc:
                work_queue.put((alloc,kfirst))

        result_queue = multiprocessing.Queue()

        for i in range(self.num_processes):
            worker = self.Worker(work_queue, result_queue, self.budget, self.workload)
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


        #pickle.dump(self.accelerators, f)
        #pickle.dump(self.asic_alloc, f)
        pickle.dump(mean_lists, f)
        pickle.dump(std_lists, f)
        pickle.dump(gmean_lists, f)
        pickle.dump(hmean_lists, f)
        f.close()

    def plot(self):
        dfn = joinpath(self.DATA_DIR, ('%s.pypkl' % self.id))
        with open(dfn, 'rb') as f:
            mean_lists = pickle.load(f)
            std_lists = pickle.load(f)
            gmean_lists = pickle.load(f)
            hmean_lists = pickle.load(f)

            #fig = plt.figure(figsize=(12,9))
            #axes = fig.add_subplot(111)

            #x = numpy.array(self.asic_alloc)
            #for mean, std in zip(mean_lists, std_lists):
            #for mean, std in zip(mean_lists[0:1], std_lists[0:1]):
                #y = numpy.array(mean)
                #err = numpy.array(std)

                #axes.errorbar(x, y, yerr=err)
                #axes.plot(x, y)
            #y = numpy.array(cov_list)
            #z = numpy.array(asic_area_list)
            #X, Y = np.meshgrid(x,y)
            #Z = np.array(fpga_area_lists)
            #axes = fig.add_subplot(111, projection='3d')

            #surf = axes.scatter(x, y, c=z)
            #cb = fig.colorbar(surf, shrink=0.8)
            #cb.set_label("Optimal ASIC allocation")
            #axes.set_xlabel('ASIC allocation in percentage')
            #axes.set_ylabel('Speedup (mean)')
            #axes.set_xlim(0, 0.11)
            #axes.legend(axes.lines, self.accelerators)
            #axes.set_ylim(0, 35)
            #ofn = joinpath(FIG_DIR, '%s.png'%self.id)
            #fig.savefig(ofn, bbox_inches='tight')
            x_lists = numpy.array(self.asic_alloc) * 0.01
            analysis.plot_data(x_lists, mean_lists,
                    xlabel='Total ASIC allocation',
                    ylabel='Speedup (mean)',
                    legend_labels=['%d%%' % alloc for alloc in self.kfirst_alloc],
                    legend_title='Acc4 area out\nof total ASIC',
                    xlim=(0, 0.5),
                    #xlim=(0, 0.11),
                    figdir=self.FIG_DIR,
                    ofn='%s-amean.%s'%(self.id, self.fmt))

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



class ASICSingle(BaseAnalysis):
    """ only one accelerators per system """

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
            alloc, acc = job

            sys = HeteroSys(self.budget)
            sys.set_mech('HKMGS')
            sys.set_tech(16)
            sys.set_asic(acc, alloc)
            #sys.use_gpacc = True

            perfs = numpy.array([ sys.get_perf(app)['perf'] for app in self.workload ])
            mean = perfs.mean()
            std = perfs.std()
            gmean = scipy.stats.gmean(perfs)
            hmean = scipy.stats.hmean(perfs)


            return (alloc, acc, mean, std, gmean, hmean)


    def __init__(self, options, budget, pv=False):
        self.prefix = 'asicsingle'
        self.fmt = options.fmt

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

        #self.ker_alloc = (0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45)
        self.ker_alloc = (0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.1)

        self.ker_perf_mean = float(options.kernel_perf_dist_norm_mean)
        self.ker_perf_std = float(options.kernel_perf_dist_norm_std)
        self.ker_num = int(options.kernel_total_count)
        self.app_num = int(options.app_total_count)
        self.ker_count_per_app = float(options.kernel_count_per_app)
        self.options = options

        kernel_cfg = options.kernels_cfg
        self.accelerators = kernel.load(kernel_cfg)

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
            r = numpy.random.uniform(rmin, rmax)
            while r < 0:
                r = numpy.random.uniform(rmin,rmax)
        return r

    def build_app(self, cov, occ, probs):
        active_kernels = dict()
        psum=0
        for o,p,acc in zip(occ, probs, self.accelerators):
            if o:
                active_kernels[p] = acc
                psum = psum + p

        ksorted = sorted(active_kernels.items())
        krever = ksorted[:]
        krever.reverse()
        app = App(f=1)

        for (p,acc),(prv,acc2) in zip(ksorted, krever):
            kcov = cov * prv / psum
            app.reg_kernel(acc, kcov)

        return app


    def build_workload(self):
        """Build workload composed by apps

        :size: @todo
        :returns: @todo

        """

        workload = []

        #options = self.options
        #ker_perf_mean = self.ker_perf_mean
        #ker_perf_std = self.ker_perf_std
        app_num = self.app_num
        #ker_num = self.ker_num
        #ker_count_per_app = self.ker_count_per_app

        #rvs = numpy.linspace(0.5*ker_perf_mean, 1.5*ker_perf_mean, ker_num-1)
        #cdfs = scipy.stats.norm.cdf(rvs, ker_perf_mean, ker_perf_std)
        #probs1 = numpy.insert(cdfs,0,0)
        #probs2 = numpy.append(cdfs, 1)
        #probs = (probs2-probs1) * ker_count_per_app

        #probs = numpy.linspace(0.9, 0.1, ker_num)

        probs = [ kernel.kernel_pool[kid]['occur'] for kid in self.accelerators ]
        kernel_occ_probs = [ scipy.stats.bernoulli.rvs(p, size=app_num) for p in probs ]
        for occ in zip(*kernel_occ_probs):
            if occ.count(1) > 0:
                cov = self.random_uc_cov()
                workload.append(self.build_app(cov, occ, probs))

        self.workload = workload

    def analyze(self):
        dfn = joinpath(self.DATA_DIR, ('%s.pypkl' % self.id))
        f = open(dfn, 'wb')

        self.build_workload()
        asic_area_list = []
        kernel_miu_list = []
        cov_list = []

        work_queue = multiprocessing.Queue()
        for alloc in self.ker_alloc:
            for acc in self.accelerators:
                work_queue.put((alloc,acc))

        result_queue = multiprocessing.Queue()

        for i in range(self.num_processes):
            worker = self.Worker(work_queue, result_queue, self.budget, self.workload)
            worker.start()

        alloc_list = []
        acc_list = []
        mean_list = []
        std_list = []
        meandict = dict()
        stddict = dict()
        gmeandict = dict()
        hmeandict = dict()
        for i in xrange(len(self.ker_alloc)*len(self.accelerators)):
            alloc, acc, mean, std, gmean, hmean = result_queue.get()
            if acc not in meandict:
                meandict[acc] = dict()
                stddict[acc] = dict()
                gmeandict[acc] = dict()
                hmeandict[acc] = dict()
            meandict[acc][int(alloc*100)] = mean
            stddict[acc][int(alloc*100)] = std
            gmeandict[acc][int(alloc*100)] = gmean
            hmeandict[acc][int(alloc*100)] = hmean

        mean_lists = []
        std_lists = []
        gmean_lists = []
        hmean_lists = []
        for acc in self.accelerators:
            mean_lists.append( [ meandict[acc][int(alloc*100)] for alloc in self.ker_alloc ])
            std_lists.append( [ stddict[acc][int(alloc*100)] for alloc in self.ker_alloc ])
            gmean_lists.append( [ gmeandict[acc][int(alloc*100)] for alloc in self.ker_alloc ])
            hmean_lists.append( [ hmeandict[acc][int(alloc*100)] for alloc in self.ker_alloc ])


        #pickle.dump(self.accelerators, f)
        #pickle.dump(self.ker_alloc, f)
        pickle.dump(mean_lists, f)
        pickle.dump(std_lists, f)
        pickle.dump(gmean_lists, f)
        pickle.dump(hmean_lists, f)
        f.close()

    def plot(self):
        dfn = joinpath(self.DATA_DIR, ('%s.pypkl' % self.id))
        with open(dfn, 'rb') as f:
            mean_lists = pickle.load(f)
            std_lists = pickle.load(f)
            gmean_lists = pickle.load(f)
            hmean_lists = pickle.load(f)

            #fig = plt.figure(figsize=(12,9))
            #axes = fig.add_subplot(111)

            #x = numpy.array(self.ker_alloc)
            #for mean, std in zip(mean_lists, std_lists):
            #for mean, std in zip(mean_lists[0:1], std_lists[0:1]):
                #y = numpy.array(mean)
                #err = numpy.array(std)

                #axes.errorbar(x, y, yerr=err)
                #axes.plot(x, y)
            #y = numpy.array(cov_list)
            #z = numpy.array(asic_area_list)
            #X, Y = np.meshgrid(x,y)
            #Z = np.array(fpga_area_lists)
            #axes = fig.add_subplot(111, projection='3d')

            #surf = axes.scatter(x, y, c=z)
            #cb = fig.colorbar(surf, shrink=0.8)
            #cb.set_label("Optimal ASIC allocation")
            #axes.set_xlabel('ASIC allocation in percentage')
            #axes.set_ylabel('Speedup (mean)')
            #axes.set_xlim(0, 0.11)
            #axes.legend(axes.lines, self.accelerators)
            #axes.set_ylim(0, 35)
            #ofn = joinpath(FIG_DIR, '%s.png'%self.id)
            #fig.savefig(ofn, bbox_inches='tight')
            analysis.plot_data(self.ker_alloc, mean_lists,
                    xlabel='ASIC allocation in percentage',
                    ylabel='Speedup (mean)',
                    legend_labels=self.accelerators,
                    #xlim=(0, 0.5),
                    xlim=(0, 0.11),
                    figdir=self.FIG_DIR,
                    ofn='%s-amean.png'%self.id)

            #analysis.plot_data(self.ker_alloc, gmean_lists,
                    #xlabel='ASIC allocation in percentage',
                    #ylabel='Speedup (gmean)',
                    #legend_labels=self.accelerators,
                    #xlim=(0, 0.5),
                    #figdir=FIG_DIR,
                    #ofn='%s-gmean.png'%self.id)

            #analysis.plot_data(self.ker_alloc, hmean_lists,
                    #xlabel='ASIC allocation in percentage',
                    #ylabel='Speedup (hmean)',
                    #legend_labels=self.accelerators,
                    #xlim=(0, 0.5),
                    #figdir=FIG_DIR,
                    #ofn='%s-hmean.png'%self.id)



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
            kid,cov = job

            app = App(f=1)
            app.reg_kernel(kid, cov)

            sys = HeteroSys(self.budget)
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


    def __init__(self, options, budget, pv=False):
        self.prefix = 'asic'
        self.fmt = options.fmt

        self.budget = budget

        self.pv = pv

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
            r = numpy.random.uniform(rmin, rmax)
            while r < 0:
                r = numpy.random.uniform(rmin,rmax)
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
            r = numpy.random.uniform(rmin, rmax)
            while r < 0:
                r = numpy.random.uniform(rmin,rmax)
        return r


    def analyze(self):
        dfn = joinpath(self.DATA_DIR, ('%s.pypkl' % self.id))
        f = open(dfn, 'wb')
        asic_area_list = []
        kernel_miu_list = []
        cov_list = []

        work_queue = multiprocessing.Queue()
        for i in xrange(self.num_samples):
            uc_perf = self.random_uc_perf()
            uc_cov = self.random_uc_cov()

            kid = 'gauss%d' % (len(kernel.kernel_pool) +1)
            kernel.kernel_pool[kid] = {'ASIC': UCoreParam(miu=uc_perf)}

            work_queue.put((kid, uc_cov))

        result_queue = multiprocessing.Queue()

        for i in range(self.num_processes):
            worker = self.Worker(work_queue, result_queue, self.budget)
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
        dfn = joinpath(self.DATA_DIR, ('%s.pypkl' % self.id))
        with open(dfn, 'rb') as f:
            asic_area_list = pickle.load(f)
            kernel_miu_list = pickle.load(f)
            cov_list = pickle.load(f)
            x = numpy.array(kernel_miu_list)
            y = numpy.array(cov_list)
            z = numpy.array(asic_area_list)
            #X, Y = np.meshgrid(x,y)
            #Z = np.array(fpga_area_lists)
            fig = plt.figure(figsize=(12,9))
            #axes = fig.add_subplot(111, projection='3d')
            axes = fig.add_subplot(111)

            surf = axes.scatter(x, y, c=z)
            cb = fig.colorbar(surf, shrink=0.8)
            cb.set_label("Optimal ASIC allocation")
            axes.set_xlabel('ASIC performance on kernel')
            axes.set_ylabel('Kernel coverage (%)')
            #axes.set_xlim(0.05, 0.65)
            #axes.set_ylim(0, 35)
            ofn = joinpath(self.FIG_DIR, '%s.png'%self.id)
            fig.savefig(ofn, bbox_inches='tight')


class FPGAAnalysis(BaseAnalysis):

    class Worker(multiprocessing.Process):

        def __init__(self, work_queue, result_queue, budget, fixed_area=None):

            multiprocessing.Process.__init__(self)

            self.work_queue = work_queue
            self.result_queue = result_queue
            self.kill_received = False

            self.fpga_area_list = range(5, 91, 2)
            self.budget = budget

            if fixed_area:
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
            fpga_area_list = []
            #cov_list = scipy.stats.norm.rvs(0.4, 0.1, size=100)
            #cov_list = self.cov_list
            kid,cov = job

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
            r = numpy.random.uniform(rmin, rmax)
            while r < 0:
                r = numpy.random.uniform(rmin,rmax)
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
            r = numpy.random.uniform(rmin, rmax)
            while r < 0:
                r = numpy.random.uniform(rmin,rmax)
        return r

    def analyze(self):
        dfn = joinpath(self.DATA_DIR, ('%s.pypkl' % self.id))
        #kernels = kernel.gen_kernel_gauss(80,10)
        #cov_list = scipy.stats.uniform.rvs(0.1, 0.7, size=20)
        #cov_list = scipy.stats.norm.rvs(0.4, 0.1)
        f = open(dfn, 'wb')
        fpga_area_list = []
        kernel_miu_list = []
        cov_list = []
        #penalty25_list = []
        #penalty19_list = []
        #penalty31_list = []

        work_queue = multiprocessing.Queue()
        for i in xrange(self.num_samples):
            uc_perf = self.random_uc_perf()
            uc_cov = self.random_uc_cov()

            kid = 'gauss%d' % (len(kernel.kernel_pool) +1)
            kernel.kernel_pool[kid] = {'FPGA': UCoreParam(miu=uc_perf)}

            work_queue.put((kid, uc_cov))

        result_queue = multiprocessing.Queue()

        for i in range(self.num_processes):
            worker = self.Worker(work_queue, result_queue, self.budget, self.fixed_area)
            worker.start()

        for i in xrange(self.num_samples):
            area,kid,cov,penalties = result_queue.get()
            fpga_area_list.append(area)
            kernel_miu_list.append(kernel.kernel_pool[kid]['FPGA'].miu)
            cov_list.append(cov)


        pickle.dump(fpga_area_list, f)
        pickle.dump(kernel_miu_list, f)
        pickle.dump(cov_list, f)
        f.close()

    def plot(self):
        dfn = joinpath(self.DATA_DIR, ('%s.pypkl' % self.id))
        with open(dfn, 'rb') as f:
            fpga_area_list = pickle.load(f)
            kernel_miu_list = pickle.load(f)
            cov_list = pickle.load(f)
            x = numpy.array(kernel_miu_list)
            y = numpy.array(cov_list)
            z = numpy.array(fpga_area_list)
            #X, Y = np.meshgrid(x,y)
            #Z = np.array(fpga_area_lists)
            fig = plt.figure(figsize=(7,5.25))
            #axes = fig.add_subplot(111, projection='3d')
            axes = fig.add_subplot(111)

            surf = axes.scatter(x, y, c=z)
            cb = fig.colorbar(surf, shrink=0.8)
            cb.set_label("Optimal FPGA allocation (%)")
            #axes.colorbar()
            axes.set_xlabel('FPGA performance on kernel')
            axes.set_ylabel('Kernel coverage (%)')
            #if self.options.kernel_perf_dist == 'lognorm':
                #axes.set_xscale('log')
            #axes.set_xlim(0.05, 0.65)
            #axes.set_ylim(0, 35)

            ofn = joinpath(self.FIG_DIR, '%s.%s'% (self.id, self.fmt))
            fig.savefig(ofn, bbox_inches='tight')


class FPGAFixedArea(BaseAnalysis):

    class Worker(multiprocessing.Process):

        def __init__(self, work_queue, result_queue, budget, fixed_area=None):

            multiprocessing.Process.__init__(self)

            self.work_queue = work_queue
            self.result_queue = result_queue
            self.kill_received = False

            self.fpga_area_list = range(5, 91, 2)
            self.budget = budget

            if fixed_area:
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
            fpga_area_list = []
            #cov_list = scipy.stats.norm.rvs(0.4, 0.1, size=100)
            #cov_list = self.cov_list
            kid,cov = job

            app = App(f=1)
            app.reg_kernel(kid, cov)

            sys = HeteroSys(self.budget)
            sys.set_mech('HKMGS')
            sys.set_tech(16)
            sys.use_gpacc = True

            perf_opt = 0
            perf_fixed = dict()
            if self.fixed_area:
                for fpga_area in self.fpga_area_list:
                    sys.realloc_gpacc(0.01*fpga_area)
                    ret = sys.get_perf(app=app)
                    if perf_opt < ret['perf']:
                        fpga_area_opt = fpga_area
                        perf_opt = ret['perf']
                    for area in self.fixed_area:
                        if fpga_area == area:
                            perf_fixed[area] = ret['perf']
                    #if fpga_area == 17:
                        #perf_fixed25 = ret['perf']
                    #if fpga_area == 11:
                        #perf_fixed19 = ret['perf']
                    #if fpga_area == 25:
                        #perf_fixed31 = ret['perf']
                perf_penalty = [ perf_fixed[area]/perf_opt for area in self.fixed_area ]
            else:
                for fpga_area in self.fpga_area_list:
                    sys.realloc_gpacc(0.01*fpga_area)
                    ret = sys.get_perf(app=app)
                    if perf_opt < ret['perf']:
                        fpga_area_opt = fpga_area
                        perf_opt = ret['perf']
                perf_penalty = None

            #perf_penalty25 = perf_fixed25 / perf_opt
            #perf_penalty19 = perf_fixed19 / perf_opt
            #perf_penalty31 = perf_fixed31 / perf_opt
            return (fpga_area_opt, kid, cov, perf_penalty)

    def __init__(self, fmt, budget, options, pv=False):
        self.prefix = 'fpgafixedarea'
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

        self.fixed_area = (11, 17, 25, 31)

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
            r = numpy.random.uniform(rmin, rmax)
            while r < 0:
                r = numpy.random.uniform(rmin,rmax)
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
            r = numpy.random.uniform(rmin, rmax)
            while r < 0:
                r = numpy.random.uniform(rmin,rmax)
        return r

    def analyze(self):
        dfn = joinpath(self.DATA_DIR, ('%s.pypkl' % self.id))
        #kernels = kernel.gen_kernel_gauss(80,10)
        #cov_list = scipy.stats.uniform.rvs(0.1, 0.7, size=20)
        #cov_list = scipy.stats.norm.rvs(0.4, 0.1)
        f = open(dfn, 'wb')
        fpga_area_list = []
        kernel_miu_list = []
        cov_list = []
        #penalty25_list = []
        #penalty19_list = []
        #penalty31_list = []
        penalty_lists = dict([(area, []) for area in self.fixed_area])

        work_queue = multiprocessing.Queue()
        for i in xrange(self.num_samples):
            uc_perf = self.random_uc_perf()
            uc_cov = self.random_uc_cov()

            kid = 'gauss%d' % (len(kernel.kernel_pool) +1)
            kernel.kernel_pool[kid] = {'FPGA': UCoreParam(miu=uc_perf)}

            work_queue.put((kid, uc_cov))

        result_queue = multiprocessing.Queue()

        for i in range(self.num_processes):
            worker = self.Worker(work_queue, result_queue, self.budget, self.fixed_area)
            worker.start()

        for i in xrange(self.num_samples):
            area,kid,cov,penalties = result_queue.get()
            fpga_area_list.append(area)
            kernel_miu_list.append(kernel.kernel_pool[kid]['FPGA'].miu)
            cov_list.append(cov)
            if penalties:
                for area, penalty in zip(self.fixed_area, penalties):
                    penalty_lists[area].append(penalty)

            #penalty25_list.append(penalty25)
            #penalty19_list.append(penalty19)
            #penalty31_list.append(penalty31)

        pickle.dump(fpga_area_list, f)
        pickle.dump(kernel_miu_list, f)
        pickle.dump(cov_list, f)
        pickle.dump(penalty_lists, f)
        #pickle.dump(penalty25_list, f)
        #pickle.dump(penalty19_list, f)
        #pickle.dump(penalty31_list, f)
        f.close()

    def plot(self):
        dfn = joinpath(self.DATA_DIR, ('%s.pypkl' % self.id))
        with open(dfn, 'rb') as f:
            fpga_area_list = pickle.load(f)
            kernel_miu_list = pickle.load(f)
            cov_list = pickle.load(f)
            penalty_lists = pickle.load(f)
            #penalty25_list = pickle.load(f)
            #penalty19_list = pickle.load(f)
            #penalty31_list = pickle.load(f)
            #x = numpy.array(kernel_miu_list)
            #y = numpy.array(cov_list)
            #z = numpy.array(fpga_area_list)
            #X, Y = np.meshgrid(x,y)
            #Z = np.array(fpga_area_lists)
            #fig = plt.figure(figsize=(16,12))
            #axes = fig.add_subplot(111, projection='3d')
            #axes = fig.add_subplot(221)

            #surf = axes.scatter(x, y, c=z)
            #cb = fig.colorbar(surf, shrink=0.8)
            #cb.set_label("Optimal FPGA allocation")
            #axes.colorbar()
            #axes.set_xlabel('FPGA performance on kernel')
            #axes.set_ylabel('Kernel coverage (%)')
            #if self.options.kernel_perf_dist == 'lognorm':
                #axes.set_xscale('log')
            #axes.set_xlim(0.05, 0.65)
            #axes.set_ylim(0, 35)

            #for area, figure_idx in zip(self.fixed_area, (2,3,4)):
            for area in self.fixed_area:
                fig = plt.figure(figsize=(8,6))
                axes = fig.add_subplot(111)
                x2 = numpy.arange(self.num_samples)
                axes.plot(x2, penalty_lists[area], 'o')
                axes.set_title('%d%% FPGA allocation' % area)
                axes.set_ylim(0.75, 1)

                ofn = joinpath(self.FIG_DIR, '%s_%d.png'%(self.id, area))
                fig.savefig(ofn, bbox_inches='tight')

            #axes2 = fig.add_subplot(223)
            #x2 = numpy.arange(self.num_samples)
            #axes2.plot(x2, penalty19_list, 'o')
            #axes2.set_title('11% FPGA allocation')

            #axes2 = fig.add_subplot(224)
            #x2 = numpy.arange(self.num_samples)
            #axes2.plot(x2, penalty31_list, 'o')
            #axes2.set_title('25% FPGA allocation')

            #ofn = joinpath(FIG_DIR, '%s.png'%self.id)
            #fig.savefig(ofn, bbox_inches='tight')


class FPGAFixedArea2(BaseAnalysis):

    class Worker(multiprocessing.Process):

        def __init__(self, work_queue, result_queue, budget, workload):

            multiprocessing.Process.__init__(self)

            self.work_queue = work_queue
            self.result_queue = result_queue
            self.kill_received = False

            self.fpga_area_list = range(5, 91, 2)
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
            fpga_area_list = []
            #cov_list = scipy.stats.norm.rvs(0.4, 0.1, size=100)
            #cov_list = self.cov_list
            a = job

            alloc = a * 0.01

            sys = HeteroSys(self.budget)
            sys.set_mech('HKMGS')
            sys.set_tech(16)
            sys.realloc_gpacc(alloc)
            sys.use_gpacc = True

            perfs = numpy.array([ sys.get_perf(app)['perf'] for app in self.workload ])
            mean = perfs.mean()
            std = perfs.std()
            return (a, mean, std)

    def __init__(self, fmt, budget, options, pv=False):
        self.prefix = 'fpgafixedarea2'
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

        self.fpga_alloc = (10, 15, 20, 25, 30, 35, 40, 45)

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
            r = numpy.random.uniform(rmin, rmax)
            while r < 0:
                r = numpy.random.uniform(rmin,rmax)
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
            r = numpy.random.uniform(rmin, rmax)
            while r < 0:
                r = numpy.random.uniform(rmin,rmax)
        return r

    def build_workload(self):
        workload = []
        for i in xrange(self.num_samples):
            uc_perf = self.random_uc_perf()
            uc_cov = self.random_uc_cov()

            kid = 'gauss%d' % (len(kernel.kernel_pool) +1)
            kernel.kernel_pool[kid] = {'FPGA': UCoreParam(miu=uc_perf)}

            app =  App(f=1)
            app.reg_kernel(kid, uc_cov)

            workload.append(app)

        self.workload = workload


    def analyze(self):
        dfn = joinpath(self.DATA_DIR, ('%s.pypkl' % self.id))
        f = open(dfn, 'wb')

        self.build_workload()
        fpga_area_list = []
        kernel_miu_list = []
        cov_list = []

        work_queue = multiprocessing.Queue()
        for alloc in self.fpga_alloc:
            work_queue.put(alloc)

        result_queue = multiprocessing.Queue()

        for i in range(min(self.num_processes, len(self.fpga_alloc))):
            worker = self.Worker(work_queue, result_queue, self.budget, self.workload)
            worker.start()

        alloc_list = []
        fpga_list = []
        meandict = dict()
        stddict = dict()
        for i in xrange(len(self.fpga_alloc)):
            alloc, mean, std = result_queue.get()
            meandict[alloc] = mean
            stddict[alloc] = std

        mean_list = [ meandict[alloc] for alloc in self.fpga_alloc ]
        std_list = [ stddict[alloc] for alloc in self.fpga_alloc ]

        pickle.dump(mean_list,f)
        pickle.dump(std_list,f)
        f.close()

    def plot(self):
        dfn = joinpath(self.DATA_DIR, ('%s.pypkl' % self.id))
        with open(dfn, 'rb') as f:
            mean_list = pickle.load(f)
            std_list = pickle.load(f)

            fig = plt.figure(figsize=(8,6))
            axes = fig.add_subplot(111)

            x = numpy.array(self.fpga_alloc)
            y = numpy.array(mean_list)
            err = numpy.array(std_list)

            axes.errorbar(x, y, yerr=err)

            ofn = joinpath(self.FIG_DIR, '%s.png'%self.id)
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
    ###### obsolete options #####
    #app_choices = ('MMM', 'BS', 'FFT')
    #app_options.add_option('--app', default='MMM', choices=app_choices,
            #help='choose the workload, choose from ('
            #+ ','.join(app_choices)
            #+ '), default: %default')
    #app_options.add_option('--fratio', default='0,90,10')
    #app_options.add_option('--app-f', type='int', default=90)
    #app_options.add_option('--kernels', default='MMM:5,BS:5')
    #############################

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


def build_workload():
    fname = joinpath(HOME, 'kernels_asicfpgaratio10x.xml')
    kernels = kernel.load_xml(fname)
    w = workload.build(500, kernels, 'norm', 0.4, 0.1)
    fname = joinpath(HOME, 'workload_norm40x10')
    workload.dump_xml(w, fname)




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


    if options.sec == 'fpga':
        anl = FPGAAnalysis(fmt=options.fmt, pv=False, budget=budget, options=options)
    elif options.sec == 'fpgafixedarea':
        anl = FPGAFixedArea(fmt=options.fmt, pv=False, budget=budget, options=options)
    elif options.sec == 'fpgafixedarea2':
        anl = FPGAFixedArea2(fmt=options.fmt, pv=False, budget=budget, options=options)
    elif options.sec == 'asic':
        anl = ASICAnalysis(options, budget=budget, pv=False)
    elif options.sec == 'asicsingle':
        anl = ASICSingle(options,budget=budget)
    elif options.sec == 'asicdual':
        anl = ASICDual(options,budget=budget)
    elif options.sec == 'hybrid':
        anl = Hybrid(options,budget=budget)
    elif options.sec == 'asictriple':
        anl = ASICTriple(options,budget=budget)

    if options.action:
        actions = options.action.split(',')
    else:
        logging.error('No action specified')

    if 'build' in actions:
        build_workload()
    if 'analysis' in actions:
        anl.analyze()
    if 'plot' in actions:
        anl.plot()


if __name__ == '__main__':
    main()
