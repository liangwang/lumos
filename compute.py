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
    technodes = [45, 32, 22, 16, 11, 8]
    sys = UnlimitedPowerSystem(area=300)
    datalines = []
    line = "tech_node Power(IO) Power(O3)\n"
    datalines.append(line)
    for tech in technodes:
        sys.set_core(IOCore(tech=tech))
        iopower = sys.power

        sys.set_core(O3Core(tech=tech))
        o3power = sys.power

        line = "%d %f %f\n" % (tech, iopower, o3power)
        datalines.append(line)
        
    datalines.append('\n\n')

    line = "tech_node Power(IO) Power(O3)\n"
    datalines.append(line)
    for tech in technodes:
        sys.set_core(IOCore(tech=tech, mech='cons'))
        iopower = sys.power

        sys.set_core(O3Core(tech=tech, mech='cons'))
        o3power = sys.power

        line = "%d %f %f\n" % (tech, iopower, o3power)
        datalines.append(line)
        
    with open('power.dat', 'w') as f:
        f.writelines(datalines)





if __name__ == '__main__':
    main()
