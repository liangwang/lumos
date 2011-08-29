#!/usr/bin/env python
    
import os
from os.path import abspath, join as joinpath


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
    def __init__(self):
        Plot.__init__(self)
        
        self.outdir = joinpath(self.outdir, 'outputs', 'figures')

class Gnuplot(Plot):
    def __init__(self):
        Plot.__init__(self)





