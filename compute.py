#!/usr/bin/env python

import math
import numpy as np
import matplotlib.pyplot as plt

from core import IOCore, O3Core
from system import *
from application import *

def get_core_by_type(type):
    if type == 'io':
        return IOCore()
    if type == 'o3':
        return O3Core()

def main():
    #sys = O3System()
    #sys.build()
    #print "O3System dim: %f" % sys.dimsi()
    #print "O3System dark: %f" % sys.darksi()
    #sys = IOSystem()
    #sys.build()
    #print "IOSystem dim: %f" % sys.dimsi()
    #print "IOSystem dark: %f" % sys.darksi()
    #sys = HeteroSystem()
    #sys.build()
    #print "HeteroSystem: %f\n" % sys.speedup()
    #sys = SymmetricSystem(IOCore(tech=16))
    #app = Application(f=0.99)
    #step = 0.01
    
    #utils = []
    #perfs = []
    #samples = int(math.floor((sys.urmax-sys.urmin)/step))
    #for i in range(samples):
        #sys.set_util_ratio(sys.urmin+i*step)
        #utils.append(sys.ur)
        #perfs.append(sys.speedup(app))

    #print utils
    #plt.plot(utils, perfs)
    #plt.show()

    sys = SimpleSystem(IOCore(tech=16))
    sys.plotDVFS(step=0.001)



if __name__ == '__main__':
    main()
