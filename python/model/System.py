#!/usr/bin/env python

import math
import matplotlib.pyplot as plt
from Core import *

class System:
    def __init__(self):

        self.cnum = 0 # the number of cores
        self.acnum = 0 # the number of active cores in parallel mode

        self.sperf = 0 # serial performance
        self.pperf = 0 # parallel performance

        self._util_ratio_max = 0 # the maximum utilization ratio
        self._util_ratio_min = 0 # the minimum utilization ratio
        self.ur = 0 # utilization ratio


    def speedup(self, app):
        f = app.f
        return 1/((1-f)/self.sperf + f/(self.pperf*self.acnum))


