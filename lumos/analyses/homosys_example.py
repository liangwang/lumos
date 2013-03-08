#!/usr/bin/env python
"""
An exmple on using :class:`~lumos.model.system.HomogSys`.

"""
import cPickle as pickle
from os.path import join as joinpath
from optparse import OptionParser
from lumos.model.system import HomogSys
from lumos.model.core import IOCore
from lumos.model.budget import SysLarge, SysMedium, SysSmall

from analysis import plot_series, BaseAnalysis
import analysis


ANALYSIS_NAME = 'homosys_example'
HOME = joinpath(analysis.HOME, ANALYSIS_NAME)
FIG_DIR,DATA_DIR=analysis.make_ws_dirs(ANALYSIS_NAME)


class HomosysExample(BaseAnalysis):
    def __init__(self, fmt, sys_area=None, sys_power=None):
        BaseAnalysis.__init__(self, fmt)

        self.prefix = 'dasi'
        if sys_area:
            self.sys_area = sys_area
        if sys_power:
            self.sys_power = sys_power

        self.tech_list = (45, 32, 22, 16)
        self.mech = 'HKMGS'

    def set_sys(self, area, power):
        self.sys_area = area
        self.sys_power = power
        self.id = '%s_%dw_%dmm' % (self.prefix, power, area)

    def analyze(self):
        sys = HomogSys()
        sys.set_sys_prop(area=self.sys_area, power=self.sys_power)
        sys.set_sys_prop(core=IOCore(mech=self.mech))
        speed_lists = []

        # dim silicon without variation
        speed_list = []
        for ctech in self.tech_list:
            sys.set_core_prop(tech=ctech, pv=False)
            ret = sys.opt_core_num()
            speed_list.append(ret['perf'])
        speed_lists.append(speed_list)

        # dim silicon with variation
        speed_list = []
        for ctech in self.tech_list:
            sys.set_core_prop(tech=ctech, pv=True)
            ret = sys.opt_core_num()
            speed_list.append(ret['perf'])
        speed_lists.append(speed_list)

        # dim silicon with variation reduction 0.5
        speed_list = []
        for ctech in self.tech_list:
            sys.set_core_prop(tech=ctech, pv=True, pen_adjust=0.5)
            ret = sys.opt_core_num()
            speed_list.append(ret['perf'])
        speed_lists.append(speed_list)

        # dim silicon with variation reduction 0.1
        speed_list = []
        for ctech in self.tech_list:
            sys.set_core_prop(tech=ctech, pv=True, pen_adjust=0.1)
            ret = sys.opt_core_num()
            speed_list.append(ret['perf'])
        speed_lists.append(speed_list)

        # dark silicon
        speed_list = []
        for ctech in self.tech_list:
            sys.set_core_prop(tech=ctech, pv=False)
            ret = sys.perf_by_dark()
            speed_list.append(ret['perf'])
        speed_lists.append(speed_list)

        dfn = joinpath(DATA_DIR, ('%s.pypkl' % self.id))
        with open(dfn, 'wb') as f:
            pickle.dump(speed_lists, f)

    def plot(self):
        dfn = joinpath(DATA_DIR, ('%s.pypkl' % self.id))
        try:
            with open(dfn, 'rb') as f:
                speed_lists = pickle.load(f)
        except IOError:
            print 'Pickle file %s.pypkl not found! No plots generated' % self.id
            return


        plot_series(self.tech_list, speed_lists,
                             xlabel='Technology Nodes (nm)',
                             ylabel='Speedup (normalized)',
                             legend_labels=['Ideal', 'VarWC', 'VarRdc1', 'VarRdc2', 'Dark'],
                             legend_loc='upper left',
                             ms_list=(6, 6, 6, 6),
                             figsize=(5.2, 3.9),
                             figdir=FIG_DIR,
                             ofn='%s.%s' % (self.id, self.fmt))


if __name__ == '__main__':
    # Init command line arguments parser
    parser = OptionParser()

    mode_choices = ('a', 'p', 'ap')
    parser.add_option('--mode', default='p', choices=mode_choices,
                      help='choose the running mode, choose from ('
                      + ','.join(mode_choices)
                      + '), default: %default]')

    budget_choices = ('small', 'medium', 'large')
    parser.add_option('--sys-budget', default='small', choices=budget_choices,
                      help='choose the system budget, from ('
                      + ','.join(budget_choices)
                      + '), default: %default]')

    fmt_choices = ('png', 'pdf')
    parser.add_option('--fmt', default='pdf', choices=fmt_choices,
                      help='choose the format of output, choose from ('
                      + ','.join(fmt_choices)
                      + '), default: %default')

    (options, args) = parser.parse_args()

    if options.sys_budget == 'small':
        budget = SysSmall
    elif options.sys_budget == 'medium':
        budget = SysMedium
    else:
        budget = SysLarge

    anl = HomosysExample(fmt=options.fmt)
    anl.set_sys(area=budget.area, power=budget.power)
    anl.do(options.mode)
