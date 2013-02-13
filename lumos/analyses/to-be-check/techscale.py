import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
from os.path import join as joinpath
from optparse import OptionParser
import os
import analysis
FIG_DIR=joinpath(analysis.FIG_DIR, 'techscale')

try:
    os.makedirs(FIG_DIR)
except OSError:
    if os.path.isdir(FIG_DIR):
        pass
    else:
        raise

freq = {
    'proj': {
        'ITRS': {45 : 1, 32 : 1.16,
                 22 : 1.45, 16 : 1.81,
                 11 : 2.26, 8  : 2.63},
        'CONS': {45 : 1, 32 : 1.10,
                 22 : 1.19, 16 : 1.25,
                 11 : 1.30, 8 : 1.34}
    },
    'inv': {
        'LP': {45: 1, 32: 1.08,
               22: 0.95, 16: 0.91},
        'HKMGS': {45: 1, 32: 1.10,
                  22: 1.14, 16: 1.15}
    },
    'adder32': {
        'LP': {45: 1, 32: 0.973895,
               22: 0.749425, 16: 0.648536},
        'HKMGS': {45: 1, 32: 0.949949,
                  22: 0.794519, 16: 0.664474}
    }
}
dp = {
    'proj': {
        'ITRS': {45 : 1, 32 : 0.66,
                 22 : 0.54, 16 : 0.38},
        'CONS': {45 : 1, 32 : 0.71,
                 22 : 0.52, 16 : 0.39}
    },
    'inv': {
        'LP': {45: 1, 32: 0.529,
               22: 0.234, 16: 0.125},
        'HKMGS': {45: 1, 32: 0.525,
                  22: 0.239, 16: 0.117}
    },
    'adder32': {
        'LP': {45: 1, 32: 0.526511,
               22: 0.228541, 16: 0.121649},
        'HKMGS': {45: 1, 32: 0.491971,
                  22: 0.206244, 16: 0.091815}
    }
}
sp = {
    'proj': {
        'ITRS': {45 : 1, 32 : 0.66,
                 22 : 0.54, 16 : 0.38},
        'CONS': {45 : 1, 32 : 0.71,
                 22 : 0.52, 16 : 0.39}
    },
    'inv': {
        'LP': {45: 1, 32: 1.73,
               22: 3.60, 16: 11.13},
        'HKMGS': {45: 1, 32: 0.567,
                  22: 0.324, 16: 0.492}
    },
    'adder32': {
        'LP': {45: 1, 32: 1.54438,
               22: 3.40117, 16: 7.64628},
        'HKMGS': {45: 1, 32: 0.306052,
                  22: 0.121858, 16: 0.131116}
    }
}

vt={
    'HKMGS': {45: 0.424, 32: 0.466,
              22: 0.508, 16: 0.504},
    'LP'   : {45: 0.622, 32: 0.647,
              22: 0.707, 16: 0.710}
}

techList = (45, 32, 22, 16)
xList = range(1, len(techList)+1)
seriesList = (('proj','ITRS'), ('proj','CONS'),
              #('inv','LP'),('inv','HKMGS'),
              #('adder32','LP'),('adder32','HKMGS'))
              ('inv','HKMGS'),('adder32','HKMGS'))
legendList = [ ('%s-%s'%(ckt,type)) for (ckt,type) in seriesList]

def plot_freq(ofile=None, has_title=True):
    fig = plt.figure(figsize=(6,4.5))
    fig.subplots_adjust(left=0.05, right=0.98, top=0.98, bottom=0.05)
    axes = fig.add_subplot(111)
    for (ckt, type) in seriesList:
        freqs=[(freq[ckt][type][tech]) for tech in techList]
        axes.plot(xList, freqs, 'o-', linewidth=2)

    majorLocator = MultipleLocator()
    axes.set_xlim(0.5, len(xList)+0.5)
    axes.xaxis.set_major_locator(majorLocator)
    axes.set_xticklabels(['45nm', '32nm', '22nm', '16nm'])
    axes.grid(True)
    axes.legend(axes.lines, legendList, loc='upper left',
                #bbox_to_anchor=(0.5, 1.07), ncol=2,
                #ncol=2,
                prop=dict(size='small'),
                fancybox=True, shadow=True)
    if has_title:
        axes.set_title('Frequency Scaling')

    if ofile is None:
        ofile = joinpath(FIG_DIR, 'freq.png')

    fig.savefig(ofile)


def plot_dp(ofile=None, has_title=True):
    fig = plt.figure(figsize=(6,4.5))
    fig.subplots_adjust(left=0.05, right=0.98, top=0.98, bottom=0.05)
    axes = fig.add_subplot(111)
    for (ckt, type) in seriesList:
        dps=[(dp[ckt][type][tech]) for tech in techList]
        axes.plot(xList, dps, 'o-', linewidth=2)

    majorLocator = MultipleLocator()
    axes.set_xlim(0.5, len(xList)+0.5)
    axes.set_ylim(0, 1.05)
    axes.xaxis.set_major_locator(majorLocator)
    axes.set_xticklabels(['45nm', '32nm', '22nm', '16nm'])
    axes.grid(True)
    axes.legend(axes.lines, legendList, loc='lower left',
                #bbox_to_anchor=(0.5, 1.07), ncol=3,
                #ncol=2,
                prop=dict(size='small'),
                fancybox=True, shadow=True)
    if has_title:
        axes.set_title('Dynamic Power Scaling')

    if ofile is None:
        ofile = joinpath(FIG_DIR, 'dp.png')

    fig.savefig(ofile)


def plot_sp(ofile=None, has_title=True):
    fig = plt.figure(figsize=(6,4.5))
    fig.subplots_adjust(left=0.05, right=0.98, top=0.98, bottom=0.05)
    axes = fig.add_subplot(111)
    for (ckt, type) in seriesList:
        sps=[(sp[ckt][type][tech]) for tech in techList]
        axes.plot(xList, sps, 'o-', linewidth=2)

    majorLocator = MultipleLocator()
    axes.set_xlim(0.5, len(xList)+0.5)
    axes.set_ylim(0, 1.05)
    axes.xaxis.set_major_locator(majorLocator)
    axes.set_xticklabels(['45nm', '32nm', '22nm', '16nm'])
    axes.grid(True)
    #axes.legend(axes.lines, legendList, loc='upper left',
    axes.legend(axes.lines, legendList, loc='lower left',
                #bbox_to_anchor=(0.5, 1.07), ncol=3,
                #ncol=2,
                prop=dict(size='small'),
                fancybox=True, shadow=True)
    if has_title:
        axes.set_title('Static Power Scaling')

    if ofile is None:
        ofile = joinpath(FIG_DIR, 'sp.png')

    fig.savefig(ofile)

parser = OptionParser()
parser.add_option('--freq', action='store_true', default=False)
parser.add_option('--dp', action='store_true', default=False)
parser.add_option('--sp', action='store_true', default=False)
parser.add_option('--has-title', action='store_true', default=False)
parser.add_option('-o', '--ofile', default=None)
(options, args) = parser.parse_args()

if options.freq:
    plot_freq(options.ofile, options.has_title)
elif options.dp:
    plot_dp(options.ofile, options.has_title)
elif options.sp:
    plot_sp(options.ofile, options.has_title)
else:
    print 'Nothing to do'
