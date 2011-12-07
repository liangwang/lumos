#!/usr/bin/env python
    
import os
from os.path import abspath, join as joinpath

from conf import misc as miscConfig

FIG_BASE = joinpath(miscConfig.homedir, 'outputs', 'figures')

try:
    os.makedirs(fig_base)
except OSError:
    if os.path.isdir(fig_base):
        pass
    else:
        raise

class Plot(object):
    def __init__(self):
        self.format = 'pdf'

        self.outdir = abspath(os.path.curdir)
        self.indir = abspath(os.path.curdir)
    
    def set_prop(self, **kwargs):
        for k,v in kwargs.items():
            k=k.lower()
            setattr(self, k, v)


class Matplot(Plot):
    markers = ['o', '^', 's', '*', 'D', '+', 'x', 'p', 'h']
    def __init__(self):
        Plot.__init__(self)
        
        self.outdir = joinpath(self.outdir, 'outputs', 'figures')


class Gnuplot(Plot):
    def __init__(self):
        Plot.__init__(self)


# functions to draw three yaxis
# matplotlib.sourceforge.net/examples/pylab_examples/multiple_yaxis_with_spines.html
def make_patch_spines_invisible(ax):
    ax.set_frame_on(True)
    ax.patch.set_visible(False)
    for sp in ax.spines.itervalues():
        sp.set_visible(False)

def make_spine_invisible(ax, direction):
    if direction in ["right", "left"]:
        ax.yaxis.set_ticks_position(direction)
        ax.yaxis.set_label_position(direction)
    elif direction in ["top", "bottom"]:
        ax.xaxis.set_ticks_position(direction)
        ax.xaxis.set_label_position(direction)
    else:
        raise ValueError("Unknown Direction :%s" % (direction,))

    ax.spines[direction].set_visible(True)



