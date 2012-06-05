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

FIG_DIR,DATA_DIR = analysis.make_ws('dist-ucore')

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
            sys.set_asic('_gen_fixednorm_005', alloc*kfirst)
            sys.set_asic('_gen_fixednorm_008', alloc*(1-kfirst))
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
        dfn = joinpath(DATA_DIR, ('%s.pypkl' % self.id))
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
            worker = ASICDual.Worker(work_queue, result_queue, self.budget, self.workload)
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
        dfn = joinpath(DATA_DIR, ('%s.pypkl' % self.id))
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
                    xlabel='ASIC allocation in percentage',
                    ylabel='Speedup (mean)',
                    legend_labels=self.kfirst_alloc,
                    xlim=(0, 0.5),
                    #xlim=(0, 0.11),
                    figdir=FIG_DIR,
                    ofn='%s-amean.png'%self.id)

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
        dfn = joinpath(DATA_DIR, ('%s.pypkl' % self.id))
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
            worker = ASICSingle.Worker(work_queue, result_queue, self.budget, self.workload)
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
        dfn = joinpath(DATA_DIR, ('%s.pypkl' % self.id))
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
                    figdir=FIG_DIR,
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
        dfn = joinpath(DATA_DIR, ('%s.pypkl' % self.id))
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
            worker = ASICAnalysis.Worker(work_queue, result_queue, self.budget)
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
            ofn = joinpath(FIG_DIR, '%s.png'%self.id)
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
                if fpga_area == 17:
                    perf_fixed25 = ret['perf']
                if fpga_area == 11:
                    perf_fixed19 = ret['perf']
                if fpga_area == 25:
                    perf_fixed31 = ret['perf']

            perf_penalty25 = perf_fixed25 / perf_opt
            perf_penalty19 = perf_fixed19 / perf_opt
            perf_penalty31 = perf_fixed31 / perf_opt
            return (fpga_area_opt, kid, cov, perf_penalty25,perf_penalty19,perf_penalty31)

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
        dfn = joinpath(DATA_DIR, ('%s.pypkl' % self.id))
        #kernels = kernel.gen_kernel_gauss(80,10)
        #cov_list = scipy.stats.uniform.rvs(0.1, 0.7, size=20)
        #cov_list = scipy.stats.norm.rvs(0.4, 0.1)
        f = open(dfn, 'wb')
        fpga_area_list = []
        kernel_miu_list = []
        cov_list = []
        penalty25_list = []
        penalty19_list = []
        penalty31_list = []

        work_queue = multiprocessing.Queue()
        for i in xrange(self.num_samples):
            uc_perf = self.random_uc_perf()
            uc_cov = self.random_uc_cov()

            kid = 'gauss%d' % (len(kernel.kernel_pool) +1)
            kernel.kernel_pool[kid] = {'FPGA': UCoreParam(miu=uc_perf)}

            work_queue.put((kid, uc_cov))

        result_queue = multiprocessing.Queue()

        for i in range(self.num_processes):
            worker = FPGAAnalysis.Worker(work_queue, result_queue, self.budget)
            worker.start()

        for i in xrange(self.num_samples):
            area,kid,cov,penalty25,penalty19,penalty31 = result_queue.get()
            fpga_area_list.append(area)
            kernel_miu_list.append(kernel.kernel_pool[kid]['FPGA'].miu)
            cov_list.append(cov)
            penalty25_list.append(penalty25)
            penalty19_list.append(penalty19)
            penalty31_list.append(penalty31)

        pickle.dump(fpga_area_list, f)
        pickle.dump(kernel_miu_list, f)
        pickle.dump(cov_list, f)
        pickle.dump(penalty25_list, f)
        pickle.dump(penalty19_list, f)
        pickle.dump(penalty31_list, f)
        f.close()

    def plot(self):
        dfn = joinpath(DATA_DIR, ('%s.pypkl' % self.id))
        with open(dfn, 'rb') as f:
            fpga_area_list = pickle.load(f)
            kernel_miu_list = pickle.load(f)
            cov_list = pickle.load(f)
            penalty25_list = pickle.load(f)
            penalty19_list = pickle.load(f)
            penalty31_list = pickle.load(f)
            x = numpy.array(kernel_miu_list)
            y = numpy.array(cov_list)
            z = numpy.array(fpga_area_list)
            #X, Y = np.meshgrid(x,y)
            #Z = np.array(fpga_area_lists)
            fig = plt.figure(figsize=(16,12))
            #axes = fig.add_subplot(111, projection='3d')
            axes = fig.add_subplot(221)

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

            axes2 = fig.add_subplot(222)
            x2 = numpy.arange(self.num_samples)
            axes2.plot(x2, penalty25_list, 'o')
            axes2.set_title('17% FPGA allocation')

            axes2 = fig.add_subplot(223)
            x2 = numpy.arange(self.num_samples)
            axes2.plot(x2, penalty19_list, 'o')
            axes2.set_title('11% FPGA allocation')

            axes2 = fig.add_subplot(224)
            x2 = numpy.arange(self.num_samples)
            axes2.plot(x2, penalty31_list, 'o')
            axes2.set_title('25% FPGA allocation')

            ofn = joinpath(FIG_DIR, '%s.png'%self.id)
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
    parser.add_option('-f', '--config-file', default='dist-ucore.cfg',
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
    elif options.sec == 'asicsingle':
        anl = ASICSingle(options,budget=budget)
        anl.do(options.mode)
    elif options.sec == 'asicdual':
        anl = ASICDual(options,budget=budget)
        anl.do(options.mode)

if __name__ == '__main__':
    main()
