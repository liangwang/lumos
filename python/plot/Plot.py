#!/usr/bin/env python
    
import os
from os.path import abspath, join as joinpath


class Plot(object):
    def __init__(self):
        self.format = 'pdf'

        self.outdir = abspath(os.path.curdir)
        self.indir = abspath(os.path.curdir)


class Matplot(Plot):
    def __init__(self):
        Plot.__init__(self)

class Gnuplot(Plot):
    def __init__(self):
        Plot.__init__(self)





