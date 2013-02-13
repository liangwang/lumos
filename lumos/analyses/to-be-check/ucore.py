import cPickle as pickle
import itertools
import numpy as np
import math
import matplotlib
matplotlib.use('Agg')

import logging
from os.path import join as joinpath
from optparse import OptionParser, OptionGroup
import os
import string
import ConfigParser
from model.app import App, AppMMM, AppBS, AppFFT64
import model.system
from model.system import AsymSys
from model.budget import *
from model.core import Core
from model.ucore import UCore
from model.tech import PTMScale as ptmtech
from data import reader
from analysis import BaseAnalysis
from analysis import plot_data, plot_twinx, plot_series, plot_series2
from analysis import FIG_DIR as FIG_BASE, DATA_DIR as DATA_BASE

FIG_DIR=joinpath(FIG_BASE, 'ucore')
try:
    os.makedirs(FIG_DIR)
except OSError:
    if os.path.isdir(FIG_DIR):
        pass
    else:
        raise
DATA_DIR=joinpath(DATA_BASE, 'ucore')
try:
    os.makedirs(DATA_DIR)
except OSError:
    if os.path.isdir(DATA_DIR):
        pass
    else:
        raise


class TypeAnalysis(BaseAnalysis):
    def __init__(self, fmt, app, pv=False):
        BaseAnalysis.__init__(self, fmt)

        self.prefix = 'type'
        self.fmt = fmt

        self.ucore_ratio_list = (0.1, 0.3, 0.5, 0.7, 0.9)
        #self.ucore_ratio_list = (0.1, )
        self.ucore_type_list = ['GPU', 'FPGA', 'ASIC']
        #self.ucore_type_list = ['ASIC',]
        self.tech_list = (45, 32, 22, 16)
        self.mech = 'HKMGS'

        self.app = app
        self.pv = pv

    def set_sys_budget(self, budget):
        """@todo: Docstring for set_sys

        :area: @todo
        :power: @todo
        :returns: @todo

        """
        self.budget = budget
        self.id = '%s_%s_%dw_%dmm' % (self.prefix, self.app.tag, budget.power, budget.area)

    def analyze(self):
        """@todo: Docstring for analyze
        :returns: @todo

        """
        sys = AsymSys(budget=self.budget)
        sys.set_mech(self.mech)
        sys.set_core_pv(self.pv)

        app = self.app

        dfn = joinpath(DATA_DIR, ('%s.pypkl' % self.id))
        with open(dfn, 'wb') as f:
            for ucore_ratio in self.ucore_ratio_list:
                speed_lists = []
                sys.ucore_alloc(per=ucore_ratio)

                for ucore_type in self.ucore_type_list:
                    speed_list = []
                    sys.set_ucore_type(ucore_type)
                    for ctech in self.tech_list:
                        sys.set_tech(ctech)
                        ret = sys.get_perf(app=app)
                        speed_list.append(ret['perf'])

                    speed_lists.append(speed_list)

                sys.ucore_alloc(area=0)
                speed_list = []
                for ctech in self.tech_list:
                    sys.set_tech(ctech)
                    ret = sys.get_perf(app=app)
                    speed_list.append(ret['perf'])
                speed_lists.append(speed_list)

                logging.debug(speed_lists)
                pickle.dump(speed_lists, f)

    def plot(self):
        """@todo: Docstring for plot
        :returns: @todo

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


class AreaAnalysis(BaseAnalysis):
    def __init__(self, fmt, app, pv=False):
        BaseAnalysis.__init__(self, fmt)

        self.prefix = 'area'
        self.sys_area = 200
        self.sys_power = 120
        self.fmt = fmt

        #self.ucore_ratio_list = (0.05, 0.1, 0.3, 0.5, 0.7, 0.9)
        self.ucore_ratio_list = (0.04, 0.05, 0.1, 0.15)
        self.ucore_type_list = ['GPU', 'FPGA', 'ASIC']
        #self.ucore_type_list = ('ASIC',)
        self.tech_list = (45, 32, 22, 16)
        self.mech = 'HKMGS'

        self.app = app
        self.pv = pv

    def set_sys_budget(self, budget):
        """@todo: Docstring for set_sys

        :area: @todo
        :power: @todo
        :returns: @todo

        """
        self.budget = budget
        self.id = '%s_%s_%dw_%dmm' % (self.prefix, self.app.tag, budget.power, budget.area)

    def set_ucore_ratio(self, ratio_list):
        self.ucore_ratio_list = ratio_list

    def set_ucore_type(self, type_list):
        self.ucore_type_list = type_list

    def analyze(self):
        """@todo: Docstring for analyze
        :returns: @todo

        """
        sys = AsymSys(self.budget)
        sys.set_mech(self.mech)
        sys.set_core_pv(self.pv)

        app = self.app

        dfn = joinpath(DATA_DIR, ('%s.pypkl' % self.id))
        with open(dfn, 'wb') as f:
            for ucore_type in self.ucore_type_list:
                speed_lists = []
                sys.set_ucore_type(ucore_type)

                for ucore_ratio in self.ucore_ratio_list:
                    speed_list = []
                    sys.ucore_alloc(per=ucore_ratio)
                    for ctech in self.tech_list:
                        sys.set_tech(ctech)
                        ret = sys.get_perf(app=app)
                        speed_list.append(ret['perf'])

                    speed_lists.append(speed_list)

                sys.ucore_alloc(area=0)
                speed_list = []
                for ctech in self.tech_list:
                    sys.set_tech(ctech)
                    ret = sys.get_perf(app=app)
                    speed_list.append(ret['perf'])
                speed_lists.append(speed_list)

                logging.debug(speed_lists)
                pickle.dump(speed_lists, f)

    def plot(self):
        """@todo: Docstring for plot
        :returns: @todo

        """
        dfn = joinpath(DATA_DIR, ('%s.pypkl' % self.id))
        legend_list = [ ("ucore_%d%%" % int(ratio*100)) for ratio in self.ucore_ratio_list] + ['Dim Si.',]
        try:
            with open(dfn, 'rb') as f:
                for ucore_type in self.ucore_type_list:
                    speed_lists = pickle.load(f)
                    plot_series(self.tech_list, speed_lists,
                            ylabel='Speedup (normalized)',
                            xlabel='Technology Nodes (nm)',
                            legend_labels=legend_list,
                            legend_loc='upper left',
                            ms_list=(6, 6, 6, 6),
                            figsize=(5.2, 3.9),
                            figdir=FIG_DIR,
                            ofn='%s-%s.%s' % (self.id, ucore_type, self.fmt))
        except IOError:
            logging.error('Pickle file %s.pkl not found! No plots generated' % self.id)


class RatioAnalysis(BaseAnalysis):
    """Docstring for RatioAnalysis """

    def __init__(self, fmt, app, pv=False):
        """@todo: to be defined """
        BaseAnalysis.__init__(self, fmt)

        self.prefix = 'type'
        self.fmt = fmt
        self.ucore_type_list = ['GPU', 'FPGA', 'ASIC']
        self.mech = 'HKMGS'

        self.pv = pv

    def set_sys_budget(self, budget):
        self.budget = budget
        self.id = '%s_%s_%dw_%dmm' % (self.prefix, self.app.tag, budget.power, budget.area)

    def analyze(self):
        sys = AsymSys(budget=self.budget)
        sys.set_mech(self.mech)
        sys.set_core_pv(self.pv)



LOGGING_LEVELS = {'critical': logging.CRITICAL,
        'error': logging.ERROR,
        'warning': logging.WARNING,
        'info': logging.INFO,
        'debug': logging.DEBUG}

def main():
    """@todo: Docstring for main
    :returns: @todo

    """
    # Init command line arguments parser
    parser = OptionParser()

    sys_options = OptionGroup(parser, "System Configurations")
    sys_options.add_option('--sys-area', type='int', default=400)
    sys_options.add_option('--sys-power', type='int', default=100)
    sys_options.add_option('--uratio', default='0.1,0.3,0.5,0.7,0.9')
    sys_options.add_option('--utype', default = 'GPU,FPGA,ASIC')
    sys_options.add_option('--sys-budget', default='large')
    parser.add_option_group(sys_options)

    app_options = OptionGroup(parser, "Application Configurations")
    app_choices = ('MMM', 'BS', 'FFT')
    app_options.add_option('--app', default='MMM', choices=app_choices,
            help='choose the workload, choose from ('
            + ','.join(app_choices)
            + '), default: %default')
    app_options.add_option('--fratio', default='0,90,10')
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
    parser.add_option('-f', '--config-file', help='Use configurations in the specified file')


    (options, args) = parser.parse_args()

    logging_level = LOGGING_LEVELS.get(options.logging_level, logging.NOTSET)
    logging.basicConfig(level=logging_level)

    uratio_list = [ (float(r)) for r in options.uratio.split(',')]
    utype_list = [ (string.upper(r)) for r in options.utype.split(',')]
    ratio_list = [ (0.01*int(r)) for r in options.fratio.split(',')]
    if options.app == 'MMM':
        app = AppMMM(f=1-ratio_list[0], f_acc=ratio_list[2])
    elif options.app == 'BS':
        app = AppBS(f=1-ratio_list[0], f_acc=ratio_list[2])

    if options.sys_budget == 'large':
        budget = SysLarge
    elif options.sys_budget == 'medium':
        budget = SysMedium
    elif options.sys_budget == 'small':
        budget = SysSmall
    else:
        logging.error('unknwon budget')

    if options.sec == 'type':
        anl = TypeAnalysis(fmt=options.fmt, pv=False, app=app)
        anl.set_sys_budget(LargeWithIdealBW)
        anl.do(options.mode)
    elif options.sec == 'area':
        anl = AreaAnalysis(fmt=options.fmt, pv=False, app=app)
        anl.set_sys_budget(LargeWithIdealBW)
        #anl.set_sys_budget(budget)
        anl.set_ucore_ratio(uratio_list)
        anl.set_ucore_type(utype_list)
        anl.do(options.mode)


if __name__ == '__main__':
    main()
