#!/usr/bin/env python
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
from itertools import cycle as icycle
from os.path import join as joinpath
import pandas as pd
import numpy as np

# plt.style.use('ggplot')

marker_cycle = [
    's', 'o', 'v', '*', '<',
    '>', '^', '+', 'x', 'D',
    'd', '1', '2', '3', '4',
    'h', 'H', 'p', '|', '_'
]
marker_size = (10,)


def plot_twinx(x_list, y1_lists, y2_lists, xlabel, y1label, y2label,
               legend_labels=None, legend_loc=None, title=None,
               xlim=None, y1lim=None, y2lim=None, set_grid=False,
               figsize=None, marker_list=None, ms_list=None,
               figdir=None, ofn=None, cb_func=None):

    if not marker_list:
        marker_list = marker_cycle

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
        ms_list = marker_size

    for y1, marker, ms in zip(y1_lists, icycle(marker_list), icycle(ms_list)):
        ax1.plot(x_list, y1, marker=marker, ms=ms)

    for y2, marker, ms in zip(y2_lists, icycle(marker_list), icycle(ms_list)):
        ax2.plot(x_list, y2, marker=marker, ms=ms, ls='-.')

    if not legend_loc:
        legend_loc = 'best'

    if legend_labels:
        ax1.legend(ax1.lines, legend_labels, loc=legend_loc,  prop=dict(size='medium'))

    ax1.set_xlabel(xlabel)
    ax1.set_ylabel(y1label)
    ax1.grid(set_grid)
    ax2.set_ylabel(y2label)
    ax2.grid(set_grid)

    if xlim:
        ax1.set_xlim(xlim[0], xlim[1])

    if y1lim:
        ax1.set_ylim(y1lim[0], y1lim[1])

    if y2lim:
        ax2.set_ylim(y2lim[0], y2lim[1])

    if cb_func:
        cb_func(ax1, ax2, fig)

    if not figdir:
        ofile = ofn
    else:
        ofile = joinpath(figdir, ofn)

    fig.savefig(ofile, bbox_inches='tight')


def plot_errbar(x_list, y_lists, err_lists, xlabel, ylabel, legend_labels=None,
                legend_loc=None, ylim=None, xlim=None, ylog=False,
                xgrid=True, ygrid=True, title=None, figsize=None, marker_list=None,
                ms_list=None, figdir=None, ofn=None, cb_func=None):
    if not marker_list:
        marker_list = marker_cycle

    if not ofn:
        ofn = 'data_plot.png'

    if not figsize:
        figsize = (8, 6)

    fig = plt.figure(figsize=figsize)
    axes = fig.add_subplot(111)
    if not ms_list:
        ms_list = marker_size

    for y, err, marker, ms in zip(y_lists, err_lists, icycle(marker_list), icycle(ms_list)):
        axes.plot(x_list, y, err=err, marker=marker, ms=ms)

    if ylim:
        axes.set_ylim(ylim[0], ylim[1])
    if xlim:
        axes.set_xlim(xlim[0], xlim[1])
    if ylog:
        axes.set_yscale('log')

    axes.set_xlabel(xlabel)
    axes.set_ylabel(ylabel)

    if not legend_loc:
        legend_loc = 'best'

    if legend_labels:
        axes.legend(axes.lines, legend_labels, loc=legend_loc,  prop=dict(size='medium'))

    axes.xaxis.grid(xgrid)
    axes.yaxis.grid(ygrid)

    if cb_func:
        cb_func(axes, fig)

    if not figdir:
        ofile = ofn
    else:
        ofile = joinpath(figdir, ofn)

    fig.savefig(ofile, bbox_inches='tight')


def plot_data(x_list, y_lists, xlabel, ylabel, legend_title=None,
              legend_labels=None, legend_loc=None, legend_prop=None,
              ylim=None, xlim=None, ylog=False, xgrid=True, ygrid=True,
              title=None, figsize=None, marker_list=None, ms_list=None,
              figdir=None, ofn=None, cb_func=None):
    if not marker_list:
        marker_list = marker_cycle

    if not ofn:
        ofn = 'data_plot.png'

    if not figsize:
        figsize = (8, 6)

    fig = plt.figure(figsize=figsize)
    axes = fig.add_subplot(111)
    if not ms_list:
        ms_list = marker_size

    for y, marker, ms in zip(y_lists, icycle(marker_list), icycle(ms_list)):
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
        axes.legend(axes.lines, legend_labels, loc=legend_loc,
                    title=legend_title, prop=legend_prop)

    axes.xaxis.grid(xgrid)
    axes.yaxis.grid(ygrid)

    if title:
        axes.set_title(title)

    if cb_func:
        cb_func(axes, fig)

    if not figdir:
        ofile = ofn
    else:
        ofile = joinpath(figdir, ofn)

    fig.savefig(ofile, bbox_inches='tight')


def plot_data_nomarker(x_list, y_lists, xlabel, ylabel, legend_title=None,
                       legend_labels=None, legend_loc=None, ylim=None, xlim=None,
                       ylog=False, xgrid=True, ygrid=True, title=None, figsize=None,
                       marker_list=None, ms_list=None, figdir=None, ofn=None, cb_func=None):

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

    if not legend_loc:
        legend_loc = 'best'

    if legend_labels:
        axes.legend(axes.lines, legend_labels, loc=legend_loc,
                    title=legend_title, prop=dict(size='medium'))

    axes.xaxis.grid(xgrid)
    axes.yaxis.grid(ygrid)

    if title:
        axes.set_title(title)

    if cb_func:
        cb_func(axes, fig)

    if not figdir:
        ofile = ofn
    else:
        ofile = joinpath(figdir, ofn)

    fig.savefig(ofile, bbox_inches='tight')


def plot_series(x_list, y_lists, xlabel, ylabel, legend_labels=None,
                legend_loc=None, ylim=None, set_grid=True, title=None,
                figsize=None, marker_list=None, ms_list=None,
                figdir=None, ofn=None, cb_func=None):
    if not marker_list:
        marker_list = marker_cycle

    if not ofn:
        ofn = 'series_plot.png'

    if not figsize:
        figsize = (8, 6)

    fig = plt.figure(figsize=figsize)
    axes = fig.add_subplot(111)
    x = range(1, len(x_list) + 1)
    if not ms_list:
        ms_list = marker_size

    for y, marker, ms in zip(y_lists, icycle(marker_list), icycle(ms_list)):
        axes.plot(x, y, marker=marker, ms=ms)

    majorLocator = MultipleLocator()
    axes.set_xlim(0.5, len(x) + 0.5)

    if ylim:
        axes.set_ylim(ylim[0], ylim[1])

    axes.set_xlabel(xlabel)
    axes.set_ylabel(ylabel)
    axes.xaxis.set_major_locator(majorLocator)
    axes.set_xticklabels(x_list)
    if not legend_loc:
        legend_loc = 'best'

    if legend_labels:
        axes.legend(axes.lines, legend_labels, loc=legend_loc, prop=dict(size='medium'))
    axes.grid(set_grid)

    if cb_func:
        cb_func(axes, fig)

    if not figdir:
        ofile = ofn
    else:
        ofile = joinpath(figdir, ofn)

    fig.savefig(ofile, bbox_inches='tight')


def plot_series2(x_list, y_lists, xlabel, ylabel, legend_labels, legend_loc=None,
                 ylim=None, set_grid=True, title=None, figsize=None,
                 marker_list=None, ms_list=None, figdir=None, ofn=None):
    """
    For darkdim's voltage plots only due to special legend layout
    """
    if not marker_list:
        marker_list = marker_cycle

    if not ofn:
        ofn = 'series_plot.png'

    if not figsize:
        figsize = (8, 6)

    fig = plt.figure(figsize=figsize)
    axes = fig.add_subplot(111)
    x = range(1, len(x_list) + 1)
    if not ms_list:
        ms_list = marker_size

    for y, marker, ms in zip(y_lists, icycle(marker_list), icycle(ms_list)):
        axes.plot(x, y, marker=marker, ms=ms)

    majorLocator = MultipleLocator()
    axes.set_xlim(0.5, len(x) + 0.5)
    if ylim:
        axes.set_ylim(ylim[0], ylim[1])

    axes.set_xlabel(xlabel)
    axes.set_ylabel(ylabel)
    axes.xaxis.set_major_locator(majorLocator)
    axes.set_xticklabels(x_list)

    if not legend_loc:
        legend_loc = 'best'

    axes.legend(axes.lines, legend_labels, loc=legend_loc, ncol=3, prop=dict(size='medium'))
    axes.grid(set_grid)

    if not figdir:
        ofile = ofn
    else:
        ofile = joinpath(figdir, ofn)

    fig.savefig(ofile, bbox_inches='tight')


def line_plot(df, x_col, y_col, series_col, xlabel=None,
              ylabel=None, llabel=None, title=None, lncols=None, ms=None,
              lloc=None, figsize=None, marker_list=None, fontsize=None,
              legend_fontsize=None, figdir=None, ofn=None, **kwargs):

    # Setup default values
    if not marker_list:
        marker_list = marker_cycle

    if not ms:
        ms = marker_size[0]

    if not xlabel:
        xlabel = x_col

    if not ylabel:
        ylabel = y_col

    if not llabel:
        llabel = series_col

    if not lloc:
        lloc = 'best'

    if not ofn:
        ofn = 'line_plot.png'

    if not figsize:
        figsize = (8, 6)

    if not fontsize:
        fontsize = 14

    if not legend_fontsize:
        legend_fontsize = fontsize

    df2 = df.pivot(x_col, series_col, y_col)

    if not lncols:
        lncols = 1
    elif lncols == 'flat':
        lncols = len(df2.columns)

    fig = plt.figure(figsize=figsize)
    axes = fig.add_subplot(111)
    # x = range(1, len(df[x_col])+1)

    df2.plot(ax=axes, fontsize=fontsize, linewidth=3, ms=ms,
             style=['{0}-'.format(m) for _, m in zip(df2.columns, icycle(marker_list))], **kwargs)
    # if series.dtype == np.dtype('object'):
    #     for ser, marker, ms in zip(series, icycle(marker_list), icycle(ms_list)):
    #         df2 = df.query('{0} == "{1}"'.format(series_col, ser))[[x_col, y_col]]
    #         # axes.plot(df[x_col], df[y_col], marker=marker, ms=ms)
    #         df2.plot(x=x_col, y=y_col, axes=axes, marker=marker, ms=ms, **kwargs)
    # else:
    #     for ser, marker, ms in zip(series, icycle(marker_list), icycle(ms_list)):
    #         df2 = df.query('{0} == {1}'.format(series_col, ser))[[x_col, y_col]]
    #         # axes.plot(df[x_col], df[y_col], marker=marker, ms=ms)
    #         df2.plot(x=x_col, y=y_col, axes=axes, marker=marker, ms=ms, **kwargs)

    axes.legend(title=llabel, loc=lloc, ncol=lncols, fontsize=legend_fontsize)
    axes.set_xlabel(xlabel, fontdict={'fontsize': fontsize})
    axes.set_ylabel(ylabel, fontdict={'fontsize': fontsize})

    if not figdir:
        ofile = ofn
    else:
        ofile = joinpath(figdir, ofn)
    fig.savefig(ofile, bbox_inches='tight')

