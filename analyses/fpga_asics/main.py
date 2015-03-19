#!/usr/bin/env python

import os


HOME = os.path.abspath(os.path.dirname(__file__))
ANALYSIS_NAME = os.path.basename(os.path.dirname(__file__))


def parse_args():
    from lumos.analyses import LumosArgumentParser, LumosNumlist
    # Init command line arguments parser
    parser = LumosArgumentParser(
        config_dir=os.path.abspath(os.path.dirname(__file__)),
        desc='{0}: heterogeneous system with throughput cores, FPGA, and ASICs.'.format(ANALYSIS_NAME))

    # sys_options = OptionGroup(parser, "System Configurations")
    budget_choices = ('large', 'medium', 'small', 'custom')
    parser.add_argument('--budget', default='large', choices=budget_choices,
            help="choose from pre-defined budgets, or 'custom' for customized budget by specifying AREA, POWER, and BANDWIDTH.")
    parser.add_argument('--sys-area', type=int, default=400, metavar='AREA',
            help='Area budget in mm^2, default: %(default)d. This option will be discarded when budget is NOT custom')
    parser.add_argument('--sys-power', type=int, default=100, metavar='POWER',
            help='Power budget in Watts, default: %(default)d. This option will be discarded when budget is NOT custom')
    parser.add_argument('--sys-bw', metavar='BANDWIDTH', default='45:180,32:198,22:234,16:252',
                        help='Bandwidth as a list indexed by technology nodes. This option will be discarded when budget is NOT custom')
    thru_core_choices = ('IOCore', 'IOCore_TFET')
    parser.add_argument('--thru-core', default='IOCore', choices=thru_core_choices,
                        help='The core type of throughput cores')

    parser.add_argument('--workload', metavar='FILE',
            help='workload configuration file, e.g. workload.xml')
    parser.add_argument('--kernels', metavar='FILE',
            help='kernels configuration file, e.g. kernels.xml')

    # action_choices = ('analyze', 'plot')
    parser.add_argument('-a', '--actions',
            help='choose acitions, can be \'analysis\', \'plot\', or both and separated by \',\'.')
    fmt_choices = ('png', 'pdf', 'eps')
    parser.add_argument('--fmt', default='pdf', choices=fmt_choices,
            help='choose the format of output.')
    parser.add_argument('--series', help='Select series')
    parser.add_argument('--kids', type=LumosNumlist, default='3,4,5,6')

    llevel_choices = ('info', 'debug', 'error')
    parser.add_argument('-l', '--logging-level', default='info',
            choices=llevel_choices,
            help='Logging level of LEVEL.')

    options = parser.parse_args()

    return options


from lumos.model.ptm_new.system import HetSys as HeterogSys
from lumos.model.ptm_new import kernel, workload
from lumos.model.ptem_new.core import IOCore, IOCore_TFET

import logging
LOGGING_LEVELS = {'critical': logging.CRITICAL,
        'error': logging.ERROR,
        'warning': logging.WARNING,
        'info': logging.INFO,
        'debug': logging.DEBUG}
_logger = logging.getLogger(ANALYSIS_NAME)


import cPickle as pickle

import os

import multiprocessing
import Queue
import scipy.stats
import numpy
import numpy.random


class ASICQuad(object):
    """ only one accelerators per system """

    class Worker(multiprocessing.Process):

        def __init__(self, work_queue, result_queue, budget, options, workload, kernels, kids):

            multiprocessing.Process.__init__(self)

            self.work_queue = work_queue
            self.result_queue = result_queue
            self.kill_received = False

            # self.asic_area_list = range(5, 91, 2)
            self.budget = budget
            self.workload = workload
            self.kernels = kernels
            self.options = options
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
            alloc = asic_area * 0.01
            kids = self.kids
            # kfirst = k * 0.01

            serial_core = IOCore(tech=22)
            if self.options.thru_core == 'IOCore':
                tput_core = IOCore(tech=22)
                print 'CMOS IOCore as throughput cores'
            elif self.options.thru_core == 'IOCore_TFET':
                tput_core = IOCore_TFET(tech=22)
                print 'TFET IOCore as throughput cores'
            else:
                print 'Unknown throughput core type {0}'.format(self.options.thru_core)
                return

            sys = HeterogSys(self.budget, tech=22, serial_core=serial_core, tput_core=tput_core)

            for idx, kid in enumerate(kids):
                kernel = self.kernels[kid]
                sys.set_asic(kernel, 'asic'+kid, alloc*config[idx]*0.01)

            perfs = numpy.array([sys.get_perf(app)['perf'] for app in self.workload.values()])
            mean = perfs.mean()
            std = perfs.std()
            gmean = scipy.stats.gmean(perfs)
            hmean = scipy.stats.hmean(perfs)

            #print '{cid}, {asic}, {perf}, {config}'.format(
                    #cid=cid,
                    #asic=asic_area,
                    #perf=mean,
                    #config=config)

            return (cid, asic_area, mean, std, gmean, hmean)

    def __init__(self, options, budget, pv=False):
        self.prefix = ANALYSIS_NAME
        self.fmt = options.fmt
        self.budget = budget
        self.pv = pv
        self.id = self.prefix
        self.num_processes = int(options.nprocs)

        self.asic_area_list = (5, 10, 15, 20, 30, 40)

        self.kalloc = (10, 20, 30, 40)
        self.kids = ['_gen_fixednorm_00%s' % kid for kid in options.kids.split(',')]

        self.alloc_configs = (
                (10, 30, 40, 20),
                (20, 30, 40, 10),
                (10, 40, 30, 20),
                (20, 40, 30, 10),
                (25, 25, 25, 25)
                )

        self.options = options

        self.kernels = kernel.load_from_xml(os.path.join(os.path.abspath(os.path.dirname(__file__)), options.kernels))
        self.accelerators = [k for k in self.kernels if k != 'dummy']
        self.workload = workload.load_from_xml(self.kernels, os.path.join(os.path.abspath(
            os.path.dirname(__file__)),options.workload))


    def analyze(self):
        """ Analyze """
        asic_area_list = self.asic_area_list

        kids = self.kids
        alloc_configs = self.alloc_configs
        n_alloc_configs = len(alloc_configs)

        work_queue = multiprocessing.Queue()
        for cid in range(n_alloc_configs):
            for asic_area in asic_area_list:
                work_queue.put( (cid, alloc_configs[cid], asic_area) )

        result_queue = multiprocessing.Queue()

        for i in range(self.num_processes):
            worker = self.Worker(work_queue, result_queue, self.budget, self.options, self.workload, self.kernels, kids)
            worker.start()

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
            mean_lists.append( [ meandict[cid][a] for a in self.asic_area_list ])
            std_lists.append( [ stddict[cid][a] for a in self.asic_area_list ])
            gmean_lists.append( [ gmeandict[cid][a] for a in self.asic_area_list ])
            hmean_lists.append( [ hmeandict[cid][a] for a in self.asic_area_list ])


        #pickle.dump(self.accelerators, f)
        #pickle.dump(self.asic_alloc, f)
        dfn = joinpath(self.DATA_DIR, ('%s.pypkl' % self.id))
        with open(dfn, 'wb') as f:
            pickle.dump(mean_lists, f)
            pickle.dump(std_lists, f)
            pickle.dump(gmean_lists, f)
            pickle.dump(hmean_lists, f)


def do_analyze(options):
    print 'analyze'

def do_plot(options):
    print 'plot'



def main():
    #(options, args) = parser.parse_args()
    options = parse_args()

    _logger.setLevel(
        LOGGING_LEVELS.get(options.logging_level, logging.NOTSET))

    # if options.budget == 'large':
    #     budget = SysLarge
    # elif options.budget == 'medium':
    #     budget = SysMedium
    # elif options.budget == 'small':
    #     budget = SysSmall
    # elif options.budget == 'custom':
    #     budget = Budget(area=float(options.sys_area),
    #             power=float(options.sys_power),
    #             bw=parse_bw(options.sys_bw))
    # else:
    #     logging.error('unknwon budget')


    if options.actions:
        actions=options.actions.split(',')
    else:
        _logger.error("No action specified")

    for act in actions:
        try:
            act_func = globals()['do_'+act]
        except KeyError:
            _logger.error('action {0} not supported, skipped'.format(act))
            continue
        act_func(options)

    print options

if __name__ == '__main__':
    main()

