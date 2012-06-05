#!/usr/bin/env python
# encoding: utf-8

import logging
import cPickle as pickle
import matplotlib
matplotlib.use('Agg')

from model.system import HeteroSys
from model.app import App
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

FIG_DIR,DATA_DIR = analysis.make_ws('hetero')


class TypeAnalysis(BaseAnalysis):
    def __init__(self, fmt, app, pv=False):
        BaseAnalysis.__init__(self, fmt)

        self.prefix = 'type'
        self.fmt = fmt

        self.ucore_ratio_list = (0.1, 0.3, 0.5, 0.7, 0.9)
        #self.ucore_ratio_list = (0.1, )
        #self.ucore_type_list = ['GPU', 'FPGA', 'ASIC']
        self.ucore_type_list = ['ASIC',]
        self.tech_list = (45, 32, 22, 16)
        self.mech = 'HKMGS'

        self.app = app
        self.pv = pv

    def set_sys_budget(self, budget):
        """set system budget

        :budget: budget
        :returns: N/A

        """
        self.budget = budget
        self.id = '%s_%s_%dw_%dmm' % (self.prefix, self.app.tag, budget.power, budget.area)

    def analyze(self):
        """analyze
        :returns: N/A

        """
        sys = HeteroSys(budget=self.budget)
        sys.set_mech(self.mech)
        app = self.app
        kid = app.get_kernel()
        sys.add_asic(kid, 0.1)
        #sys.set_core_pv(self.pv)


        dfn = joinpath(DATA_DIR, ('%s.pypkl' % self.id))
        with open(dfn, 'wb') as f:
            for ucore_ratio in self.ucore_ratio_list:
                speed_lists = []
                #sys.ucore_alloc(per=ucore_ratio)
                sys.realloc_asic(kid, ucore_ratio)

                speed_list = []
                for ctech in self.tech_list:
                    sys.set_tech(ctech)
                    # TODO: modify App to work with UCore
                    ret = sys.get_perf(app=app)
                    speed_list.append(ret['perf'])

                speed_lists.append(speed_list)

                sys.realloc_asic(kid, 0)
                speed_list = []
                for ctech in self.tech_list:
                    sys.set_tech(ctech)
                    ret = sys.get_perf(app=app)
                    speed_list.append(ret['perf'])
                speed_lists.append(speed_list)

                logging.debug(speed_lists)
                pickle.dump(speed_lists, f)

    def plot(self):
        """plot
        :returns: N/A

        """
        dfn = joinpath(DATA_DIR, ('%s.pypkl' % self.id))
        legend_list = self.ucore_type_list + ['Dim Si.',]
        try:
            with open(dfn, 'rb') as f:
                for ucore_ratio in self.ucore_ratio_list:
                    speed_lists = pickle.load(f)
                    plot_series(self.tech_list, speed_lists,
                            ylabel='Speedup (normalized)',
                            xlabel='Technology Nodes (nm)',
                            legend_labels=legend_list,
                            legend_loc='upper left',
                            ms_list=(6, 6, 6, 6),
                            figsize=(5.2, 3.9),
                            figdir=FIG_DIR,
                            ofn='%s-ucore%.1f.%s' % (self.id, ucore_ratio, self.fmt))
        except IOError:
            logging.error('Pickle file %s.pkl not found! No plots generated' % self.id)



class AccAnalysis(BaseAnalysis):

    def __init__(self, fmt, app, budget, pv=False):
        BaseAnalysis.__init__(self, fmt)

        self.prefix = 'acc'
        self.fmt = fmt

        self.budget = budget

        self.ucore_ratio_list = (0.1, 0.3, 0.5, 0.7, 0.9)
        self.ucore_type_list = ('FPGA', 'ASIC')
        self.tech_list = (45, 32, 22, 16)
        self.mech = 'HKMGS'

        self.app = app
        self.pv = pv

        self.asic_cfg = 'NA'
        self.fpga_cfg = 'NA'
        self.id = self.id_update()

    def asic_config(self, config):
        self.asic_cfg = config
        self.id = self.id_update()

    def fpga_config(self, config):
        self.fpga_cfg = config
        self.id = self.id_update()

    def id_update(self):
        asic_cfg_tag = self.asic_cfg.replace(':','-').replace('|','-').replace(',','-')
        fpga_cfg_tag = self.fpga_cfg.replace(',','-')
        return '%s_asic_%s_fpga_%s_app_%s_%dw_%dmm' % (self.prefix,
                asic_cfg_tag, fpga_cfg_tag,
                self.app.tag, self.budget.power, self.budget.area)

    def analyze(self):
        sys = HeteroSys(self.budget)
        sys.set_mech(self.mech)

        app = self.app

        dfn = joinpath(DATA_DIR, ('%s.pypkl' % self.id))
        with open(dfn, 'wb') as f:
            speed_lists = []

            sys.use_gpacc = False
            for acc_config in self.asic_cfg.split('|'):
                for acc in acc_config.split(','):
                    tmp = acc.split(':')
                    kid = tmp[0]
                    aratio = 0.01 * int(tmp[1])
                    sys.set_asic(kid, aratio)

                speed_list = []

                for ctech in self.tech_list:
                    sys.set_tech(ctech)
                    ret = sys.get_perf(app=app)
                    speed_list.append(ret['perf'])

                speed_lists.append(speed_list)

            sys.del_asics()
            sys.use_gpacc = True
            for acc_config in self.fpga_cfg.split(','):
                sys.realloc_gpacc(0.01*int(acc_config))
                speed_list = []

                for ctech in self.tech_list:
                    sys.set_tech(ctech)
                    ret = sys.get_perf(app=app)
                    speed_list.append(ret['perf'])

                speed_lists.append(speed_list)

            logging.debug(speed_lists)
            pickle.dump(speed_lists, f)

    def plot(self):
        dfn = joinpath(DATA_DIR, ('%s.pypkl' % self.id))
        legend_list = self.asic_cfg.split('|') + [ ('FPGA-%s' % i) for i in self.fpga_cfg.split(',')]
        with open(dfn, 'rb') as f:
            speed_lists = pickle.load(f)
            plot_series(self.tech_list, speed_lists, 
                    ylabel='Speedup (normalized)',
                    xlabel='Technology Nodes (nm)',
                    legend_labels=legend_list,
                    legend_loc='upper left',
                    ms_list=(6, 6, 6, 6),
                    figsize=(5.2, 3.9),
                    figdir=FIG_DIR,
                    ofn='%s.%s' % (self.id, self.fmt))


class FPGAAnalysis(BaseAnalysis):
    def __init__(self, fmt, app_f, app_cfg, budget, pv=False):
        self.prefix = 'fpga'
        self.fmt = fmt

        self.budget = budget

        self.pv = pv

        self.fpga_area_list = (10, 20, 30, 40, 50, 60, 70)

        self.app_f = app_f
        self.app_cfg = app_cfg

        self.id = self.prefix

    def analyze(self):
        sys = HeteroSys(self.budget)
        sys.set_mech('HKMGS')
        sys.set_tech(16)
        sys.use_gpacc = True

        app_list = self.app_cfg.split('|')
        app_f = self.app_f

        dfn = joinpath(DATA_DIR, ('%s.pypkl' % self.id))
        with open(dfn, 'wb') as f:
            speed_lists = []
            for acfg in app_list:
                speed_list = []

                app = App(f=app_f/100)
                for kernel in acfg.split(','):
                    k0, k1 = kernel.split(':')
                    kid = k0
                    cov = 0.01 * int(k1)
                    app.reg_kernel(kid, cov)

                for fpga_area in self.fpga_area_list:
                    sys.realloc_gpacc(0.01*fpga_area)
                    ret = sys.get_perf(app=app)
                    speed_list.append(ret['perf'])

                speed_lists.append(speed_list)

            pickle.dump(speed_lists, f)

    def plot(self):
        dfn = joinpath(DATA_DIR, ('%s.pypkl' % self.id))
        legend_list = self.app_cfg.split('|')
        with open(dfn, 'rb') as f:
            speed_lists = pickle.load(f)
            plot_data(self.fpga_area_list, speed_lists,
                    ylabel='Speedup (normalized)',
                    xlabel='FPGA area ratio (%)',
                    xlim=(5, 75),
                    legend_labels = legend_list,
                    legend_loc = 'upper left',
                    figdir = FIG_DIR,
                    ofn = '%s.%s' % (self.id, self.fmt))



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

    app = App(f=(options.app_f/100))
    for kernel in options.kernels.split(','):
        k0,k1 = kernel.split(':')
        kid = k0
        cov = 0.01 * int(k1)
        app.reg_kernel(kid, cov)


    if options.sec == 'type':
        anl = TypeAnalysis(fmt=options.fmt, pv=False, app=app)
        anl.set_sys_budget(LargeWithIdealBW)
        anl.do(options.mode)
    elif options.sec == 'acc':
        anl = AccAnalysis(fmt=options.fmt, pv=False, app=app, budget=budget)
        anl.asic_config(options.asic_config)
        anl.fpga_config(options.fpga_config)
        anl.do(options.mode)
    elif options.sec == 'fpga':
        anl = FPGAAnalysis(fmt=options.fmt, pv=False, budget=budget, app_f=options.app_f, app_cfg=options.app_cfg)
        anl.do(options.mode)


if __name__ == '__main__':
    main()
