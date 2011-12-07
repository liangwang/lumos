#!/usr/bin/env python

#FIXME: make it compatible with new core module

from Plot import Matplot
from model import System
import matplotlib.pyplot as plt
from os.path import join as joinpath

class PerfTechPlot(Matplot):
    def __init__(self, area=111, power=125, prefix='spd2tech', mech='ITRS'):

        Matplot.__init__(self)
        
        self.format = 'pdf'
        
        self.power = power
        self.area = area
        self.prefix = prefix
        self.mech = mech
        
        self.sys = System.System()

    def do_plot(self):
        pass


if __name__ == '__main__':
    p = Spd2TechPlot()
    p.set_figsize('12in,9in')

    budget = {'area':500, 'power': 200}
    p.set_budget(budget)
    p.set_plot_prefix('%dmm2-%dw' % (budget['area'], budget['power']))
    p.set_mech('ITRS')
    p.write_files()

    p.set_mech('CONS')
    p.write_files()

    budget = {'area':111, 'power': 125}
    p.set_budget(budget)
    p.set_plot_prefix('%dmm2-%dw' % (budget['area'], budget['power']))
    p.set_mech('ITRS')
    p.write_files()

    p.set_mech('CONS')
    p.write_files()

