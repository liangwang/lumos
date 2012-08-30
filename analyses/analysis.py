import itertools
#import numpy as np
import matplotlib.pyplot as plt
#import matplotlib.lines as mlines
from matplotlib.ticker import MultipleLocator

import os
from os.path import join as joinpath
import conf.misc

HOME = joinpath(conf.misc.homedir, 'analyses')
OUTPUT_HOME = joinpath(conf.misc.homedir, 'outputs')
DATA_DIR = joinpath(conf.misc.homedir,
                    'outputs', 'analyses')
FIG_DIR = joinpath(conf.misc.homedir,
                    'outputs', 'figures')

marker_cycle = ['s', 'o', 'v', '*', '<',
'>', '^', '+', 'x', 'D',
'd', '1', '2', '3', '4',
'h', 'H', 'p', '|', '_']

def mk_dir(parent,  dname):
    abspath = joinpath(parent, dname)
    try:
        os.makedirs(abspath)
    except OSError:
        if os.path.isdir(abspath):
            pass
        else:
            raise
    return abspath


def make_ws(anl_name):
    ws_dir = joinpath(OUTPUT_HOME, anl_name)
    fdir = mk_dir(ws_dir, 'figures')
    ddir = mk_dir(ws_dir, 'data')
    return (fdir, ddir)


def make_ws_dirs(anl_name):
    ws_dir = joinpath(HOME, anl_name)
    fdir = mk_dir(ws_dir, 'figures')
    ddir = mk_dir(ws_dir, 'data')
    return (fdir, ddir)


def try_update(config, options, section, name):
    if config.has_option(section, name):
        if not hasattr(options, name):
            setattr(options, name, config.get(section, name))
        elif options.override:
            setattr(options, name, config.get(section, name))


def parse_bw(bw_cfg):
    cfg_striped = ''.join(bw_cfg.split())
    bw_dict = dict()
    for bw in cfg_striped.split(','):
        tmp = bw.split(':')
        t = int(tmp[0])
        v = float(tmp[1])
        bw_dict[t] = v

    return bw_dict


def plot_twinx(x_list, y1_lists, y2_lists,
               xlabel, y1label, y2label,
               legend_labels=None, legend_loc=None, title=None,
               xlim=None, y1lim=None, y2lim=None,
               figsize=None, marker_list=None, ms_list=None,
               figdir=None, ofn=None, cb_func=None):

    if not marker_list:
        marker_list = ['s', 'o', 'v', '*', '+', '>', '^', '<', 'x', 'D', 'd',
                       '1', '2', '3', '4', 'h', 'H', 'p', '|', '_']

    if not ofn:
        ofn = 'twinx_plot.png'

    if not figsize:
        figsize = (8, 6)

    fig = plt.figure(figsize=figsize)
    ax1 = fig.add_subplot(111)
    ax2 = ax1.twinx()

    if title:
        ax1.set_title(title)

    if not ms_list:
        for y1, marker in itertools.izip(y1_lists, itertools.cycle(marker_list)):
            ax1.plot(x_list, y1, marker=marker, ms=10)

        for y2, marker in itertools.izip(y2_lists, itertools.cycle(marker_list)):
            ax2.plot(x_list, y2, marker=marker, ms=10)
    else:
        for y1, marker, ms in itertools.izip(y1_lists, itertools.cycle(marker_list), itertools.cycle(ms_list)):
            ax1.plot(x_list, y1, marker=marker, ms=ms)

        for y2, marker, ms in itertools.izip(y2_lists, itertools.cycle(marker_list), itertools.cycle(ms_list)):
            ax2.plot(x_list, y2, marker=marker, ms=ms)

    if legend_labels and legend_loc:
        ax1.legend(ax1.lines, legend_labels, loc=legend_loc,  prop=dict(size='medium'))

    ax1.set_xlabel(xlabel)
    ax1.set_ylabel(y1label)
    ax2.set_ylabel(y2label)

    if xlim:
        ax1.set_xlim(xlim[0], xlim[1])

    if y1lim:
        ax1.set_ylim(y1lim[0], y1lim[1])

    if y2lim:
        ax2.set_ylim(y2lim[0], y2lim[1])

    if cb_func:
        cb_func(ax1, ax2, fig)

    if not figdir:
        ofile = joinpath(FIG_DIR, ofn)
    else:
        ofile = joinpath(figdir, ofn)

    fig.savefig(ofile, bbox_inches='tight')

def plot_errbar(x_list, y_lists, err_lists, xlabel, ylabel, legend_labels=None, legend_loc=None, ylim=None, xlim=None, ylog=False, xgrid=True, ygrid=True, title=None, figsize=None, marker_list=None, ms_list=None, figdir=None, ofn=None, cb_func=None):
    if not marker_list:
        marker_list = ['s', 'o', 'v', '*', '<', '>', '^', '+', 'x', 'D', 'd',
                       '1', '2', '3', '4', 'h', 'H', 'p', '|', '_']

    if not ofn:
        ofn = 'data_plot.png'

    if not figsize:
        figsize = (8, 6)

    fig = plt.figure(figsize=figsize)
    axes = fig.add_subplot(111)
    if not ms_list:
        for y, err,  marker in itertools.izip(y_lists, err_lists, itertools.cycle(marker_list)):
            axes.errorbar(x_list, y, err=err, marker=marker, ms=10)
    else:
        for y, err, marker, ms in itertools.izip(y_lists, err_lists, itertools.cycle(marker_list), itertools.cycle(ms_list)):
            axes.plot(x_list, y, err=err, marker=marker, ms=ms)

    if ylim:
        axes.set_ylim(ylim[0], ylim[1])
    if xlim:
        axes.set_xlim(xlim[0], xlim[1])
    if ylog:
        axes.set_yscale('log')

    axes.set_xlabel(xlabel)
    axes.set_ylabel(ylabel)
    if legend_labels:
        if legend_loc:
            axes.legend(axes.lines, legend_labels, loc=legend_loc,  prop=dict(size='medium'))
        else:
            axes.legend(axes.lines, legend_labels, prop=dict(size='medium'))

    axes.xaxis.grid(xgrid)
    axes.yaxis.grid(ygrid)

    if cb_func:
        cb_func(axes, fig)

    if not figdir:
        ofile = joinpath(FIG_DIR, ofn)
    else:
        ofile = joinpath(figdir, ofn)

    fig.savefig(ofile, bbox_inches='tight')


def plot_data(x_list, y_lists, xlabel, ylabel,
        legend_title=None, legend_labels=None,
        legend_loc=None, legend_prop=None,
        ylim=None, xlim=None, ylog=False,
        xgrid=True, ygrid=True, title=None,
        figsize=None, marker_list=None, ms_list=None,
        figdir=None, ofn=None, cb_func=None):
    if not marker_list:
        marker_list = ['s', 'o', 'v', '*', '<', '>', '^', '+', 'x', 'D', 'd',
                       '1', '2', '3', '4', 'h', 'H', 'p', '|', '_']

    if not ofn:
        ofn = 'data_plot.png'

    if not figsize:
        figsize = (8, 6)

    fig = plt.figure(figsize=figsize)
    axes = fig.add_subplot(111)
    if not ms_list:
        for y, marker in itertools.izip(y_lists, itertools.cycle(marker_list)):
            axes.plot(x_list, y, marker=marker, ms=10)
    else:
        for y, marker, ms in itertools.izip(y_lists, itertools.cycle(marker_list), itertools.cycle(ms_list)):
            axes.plot(x_list, y, marker=marker, ms=ms)

    if ylim:
        axes.set_ylim(ylim[0], ylim[1])
    if xlim:
        axes.set_xlim(xlim[0], xlim[1])
    if ylog:
        axes.set_yscale('log')

    axes.set_xlabel(xlabel)
    axes.set_ylabel(ylabel)

    if not legend_loc:
        legend_loc = 'upper left'

    if not legend_prop:
        legend_prop = dict(size='medium')

    if legend_labels:
        #if legend_loc:
        axes.legend(axes.lines, legend_labels, loc=legend_loc,
                title=legend_title, prop=legend_prop)
        #else:
            #axes.legend(axes.lines, legend_labels, prop=dict(size='medium'))

    axes.xaxis.grid(xgrid)
    axes.yaxis.grid(ygrid)

    if title:
        axes.set_title(title)

    if cb_func:
        cb_func(axes, fig)

    if not figdir:
        ofile = joinpath(FIG_DIR, ofn)
    else:
        ofile = joinpath(figdir, ofn)

    fig.savefig(ofile, bbox_inches='tight')


def plot_data_nomarker(x_list, y_lists, xlabel, ylabel, legend_title=None, legend_labels=None, legend_loc=None, ylim=None, xlim=None, ylog=False, xgrid=True, ygrid=True, title=None, figsize=None, marker_list=None, ms_list=None, figdir=None, ofn=None, cb_func=None):

    if not ofn:
        ofn = 'data_plot.png'

    if not figsize:
        figsize = (8, 6)

    fig = plt.figure(figsize=figsize)
    axes = fig.add_subplot(111)

    for y in y_lists:
        axes.plot(x_list, y)

    if ylim:
        axes.set_ylim(ylim[0], ylim[1])
    if xlim:
        axes.set_xlim(xlim[0], xlim[1])
    if ylog:
        axes.set_yscale('log')

    axes.set_xlabel(xlabel)
    axes.set_ylabel(ylabel)
    if legend_labels:
        #if legend_loc:
        axes.legend(axes.lines, legend_labels, loc=legend_loc,
                title=legend_title, prop=dict(size='medium'))
        #else:
            #axes.legend(axes.lines, legend_labels, prop=dict(size='medium'))

    axes.xaxis.grid(xgrid)
    axes.yaxis.grid(ygrid)

    if title:
        axes.set_title(title)

    if cb_func:
        cb_func(axes, fig)

    if not figdir:
        ofile = joinpath(FIG_DIR, ofn)
    else:
        ofile = joinpath(figdir, ofn)

    fig.savefig(ofile, bbox_inches='tight')

def plot_series(x_list, y_lists, xlabel, ylabel, legend_labels=None, legend_loc=None, ylim=None, set_grid=True, title=None, figsize=None, marker_list=None, ms_list=None, figdir=None, ofn=None, cb_func=None):
    if not marker_list:
        marker_list = ['s', 'o', 'v', 'd', 'D', '>', '^', '<', 'x', '+', '*',
                       '1', '2', '3', '4', 'h', 'H', 'p', '|', '_']

    if not ofn:
        ofn = 'series_plot.png'

    if not figsize:
        figsize = (8, 6)

    fig = plt.figure(figsize=figsize)
    axes = fig.add_subplot(111)
    x = range(1, len(x_list) + 1)
    if not ms_list:
        for y, marker in itertools.izip(y_lists, itertools.cycle(marker_list)):
            axes.plot(x, y, marker=marker, ms=10)
    else:
        for y, marker, ms in itertools.izip(y_lists, itertools.cycle(marker_list), itertools.cycle(ms_list)):
            axes.plot(x, y, marker=marker, ms=ms)

    majorLocator = MultipleLocator()
    axes.set_xlim(0.5, len(x) + 0.5)
    if ylim:
        axes.set_ylim(ylim[0], ylim[1])
    axes.set_xlabel(xlabel)
    axes.set_ylabel(ylabel)
    axes.xaxis.set_major_locator(majorLocator)
    axes.set_xticklabels(x_list)
    if legend_labels:
        axes.legend(axes.lines, legend_labels, loc=legend_loc, prop=dict(size='medium'))
    axes.grid(set_grid)

    if cb_func:
        cb_func(axes, fig)

    if not figdir:
        ofile = joinpath(FIG_DIR, ofn)
    else:
        ofile = joinpath(figdir, ofn)

    fig.savefig(ofile, bbox_inches='tight')
    #fig.savefig(ofile)


def plot_series2(x_list, y_lists, xlabel, ylabel, legend_labels, legend_loc, ylim=None, set_grid=True, title=None, figsize=None, marker_list=None, ms_list=None, figdir=None, ofn=None):
    """
    For darkdim's voltage plots only due to special legend layout
    """
    if not marker_list:
        marker_list = ['s', 'o', 'v', '*', '<', '>', '^', '+', 'x', 'D', 'd',
                       '1', '2', '3', '4', 'h', 'H', 'p', '|', '_']

    if not ofn:
        ofn = 'series_plot.png'

    if not figsize:
        figsize = (8, 6)

    fig = plt.figure(figsize=figsize)
    axes = fig.add_subplot(111)
    x = range(1, len(x_list) + 1)
    if not ms_list:
        for y, marker in itertools.izip(y_lists, itertools.cycle(marker_list)):
            axes.plot(x, y, marker=marker, ms=10)
    else:
        for y, marker, ms in itertools.izip(y_lists, itertools.cycle(marker_list), itertools.cycle(ms_list)):
            axes.plot(x, y, marker=marker, ms=ms)

    majorLocator = MultipleLocator()
    axes.set_xlim(0.5, len(x) + 0.5)
    if ylim:
        axes.set_ylim(ylim[0], ylim[1])
    axes.set_xlabel(xlabel)
    axes.set_ylabel(ylabel)
    axes.xaxis.set_major_locator(majorLocator)
    axes.set_xticklabels(x_list)
    axes.legend(axes.lines, legend_labels, loc=legend_loc, ncol=3, prop=dict(size='medium'))
    axes.grid(set_grid)

    if not figdir:
        ofile = joinpath(FIG_DIR, ofn)
    else:
        ofile = joinpath(figdir, ofn)

    fig.savefig(ofile, bbox_inches='tight')


class BaseAnalysis(object):
    def __init__(self, fmt):
        self.fmt = fmt

    def do(self, mode):
        if 'a' in mode:
            self.analyze()
        if 'p' in mode:
            self.plot()
