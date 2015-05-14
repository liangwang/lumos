#!/usr/bin/env python
import matplotlib.pyplot as plt
plt.style.use('ggplot')
from matplotlib.ticker import MultipleLocator
from itertools import cycle as icycle
from os.path import join as joinpath


def plot_twinx(x_list, y1_lists, y2_lists,
               xlabel, y1label, y2label,
               legend_labels=None, legend_loc=None, title=None,
               xlim=None, y1lim=None, y2lim=None, set_grid=False,
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
        for y1, marker in zip(y1_lists, icycle(marker_list)):
            ax1.plot(x_list, y1, marker=marker, ms=10)

        for y2, marker in zip(y2_lists, icycle(marker_list)):
            ax2.plot(x_list, y2, marker=marker, ms=10, ls='-.')
    else:
        for y1, marker, ms in zip(y1_lists, icycle(marker_list), icycle(ms_list)):
            ax1.plot(x_list, y1, marker=marker, ms=ms)

        for y2, marker, ms in zip(y2_lists, icycle(marker_list), icycle(ms_list)):
            ax2.plot(x_list, y2, marker=marker, ms=ms, ls='-.')

    if legend_labels and legend_loc:
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
        marker_list = ['s', 'o', 'v', '*', '<', '>', '^', '+', 'x', 'D', 'd',
                       '1', '2', '3', '4', 'h', 'H', 'p', '|', '_']

    if not ofn:
        ofn = 'data_plot.png'

    if not figsize:
        figsize = (8, 6)

    fig = plt.figure(figsize=figsize)
    axes = fig.add_subplot(111)
    if not ms_list:
        for y, err,  marker in zip(y_lists, err_lists, icycle(marker_list)):
            axes.errorbar(x_list, y, err=err, marker=marker, ms=10)
    else:
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
        marker_list = ['s', 'o', 'v', '*', '<', '>', '^', '+', 'x', 'D', 'd',
                       '1', '2', '3', '4', 'h', 'H', 'p', '|', '_']

    if not ofn:
        ofn = 'data_plot.png'

    if not figsize:
        figsize = (8, 6)

    fig = plt.figure(figsize=figsize)
    axes = fig.add_subplot(111)
    if not ms_list:
        for y, marker in zip(y_lists, icycle(marker_list)):
            axes.plot(x_list, y, marker=marker, ms=10)
    else:
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
        for y, marker in zip(y_lists, icycle(marker_list)):
            axes.plot(x, y, marker=marker, ms=10)
    else:
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


def plot_series2(x_list, y_lists, xlabel, ylabel, legend_labels, legend_loc,
                 ylim=None, set_grid=True, title=None, figsize=None,
                 marker_list=None, ms_list=None, figdir=None, ofn=None):
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
        for y, marker in zip(y_lists, icycle(marker_list)):
            axes.plot(x, y, marker=marker, ms=10)
    else:
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
    axes.legend(axes.lines, legend_labels, loc=legend_loc, ncol=3, prop=dict(size='medium'))
    axes.grid(set_grid)

    if not figdir:
        ofile = ofn
    else:
        ofile = joinpath(figdir, ofn)

    fig.savefig(ofile, bbox_inches='tight')
