#!/usr/bin/env python

import math
import matplotlib.pyplot as plt
from core import IOCore, O3Core

class System:
    def __init__(self):

        self.cnum = 0 # the number of cores
        self.acnum = 0 # the number of active cores in parallel mode

        self.sperf = 0 # serial performance
        self.pperf = 0 # parallel performance

        self.urmax = 0 # the maximum utilization ratio
        self.urmin = 0 # the minimum utilization ratio
        self.ur = 0 # utilization ratio


    def speedup(self, app):
        f = app.f
        return 1/((1-f)/self.sperf + f/(self.pperf*self.acnum))


class O3System(System):
    def build(self):
        c = O3Core()
        a = c.area
        while a < self.area:
            self.corelist.append(c)
            a += c.area

    def dimsi(self):
        if not self.corelist:
            print "There are no cores to optimize"
            return 0

        #Serial
        o3c = self.corelist[0]
        if not isinstance(o3c, O3Core):
            print "No O3Core found in O3System"
            return 0

        perf = 0
        dvfs_factor = math.pow(self.power/o3c.power(), 0.333)
        if dvfs_factor > DVFS_MAX:
            dvfs_factor = DVFS_MAX
        o3c.dvfs(dvfs_factor)
        perf = perf + (1-self.f)/o3c.perf()

        #parallel
        dvfs_factor = math.pow(self.power/(len(self.corelist)*o3c.power()), 0.333)
        if dvfs_factor > DVFS_MAX :
            dvfs_factor = DVFS_MAX
        if dvfs_factor < DVFS_MIN :
            dvfs_factor = DVFS_MIN

        o3c.dvfs(dvfs_factor)
        perf = perf + self.f / (len(self.corelist)*o3c.perf())

        return 1/perf

    def darksi(self):
        if not self.corelist:
            print "There are no cores to optimize"
            return 0

        #Serial
        o3c = self.corelist[0]
        if not isinstance(o3c, O3Core):
            print "No O3Core found in O3System"
            return 0

        perf = 0
        dvfs_factor = math.pow(self.power/o3c.power(), 0.333)
        if dvfs_factor > DVFS_MAX:
            dvfs_factor = DVFS_MAX
        o3c.dvfs(dvfs_factor)
        perf = perf + (1-self.f)/o3c.perf()

        #parallel
        o3c.dvfs(DVFS_MAX)
        num = self.power/o3c.power()
        perf = perf + self.f / (num*o3c.perf())

        return 1/perf


class IOSystem(System):
    def build(self):
        c = IOCore()
        a = c.area
        while a < self.area:
            self.corelist.append(c)
            a += c.area

    def dimsi(self):
        if not self.corelist:
            print "There are no cores to optimize"
            return 0

        #Serial
        ioc = self.corelist[0]
        if not isinstance(ioc, IOCore):
            print "No IOCore found in IOSystem"
            return 0

        perf = 0
        dvfs_factor = math.pow(self.power/ioc.power(), 0.333)
        #if dvfs_factor > DVFS_MAX:
            #dvfs_factor = DVFS_MAX
        ioc.dvfs(dvfs_factor)
        perf = perf + (1-self.f)/ioc.perf()

        #parallel
        dvfs_factor = math.pow(self.power/(len(self.corelist)*ioc.power()), 0.333)
        #if dvfs_factor > DVFS_MAX :
            #dvfs_factor = DVFS_MAX
        if dvfs_factor < DVFS_MIN :
            dvfs_factor = DVFS_MIN

        ioc.dvfs(dvfs_factor)
        perf = perf + self.f / (len(self.corelist)*ioc.perf())

        return 1/perf

    def darksi(self):
        if not self.corelist:
            print "There are no cores to optimize"
            return 0

        #Serial
        ioc = self.corelist[0]
        if not isinstance(ioc, IOCore):
            print "No IOCore found in IOSystem"
            return 0

        perf = 0
        dvfs_factor = math.pow(self.power/ioc.power(), 0.333)
        #if dvfs_factor > DVFS_MAX:
            #dvfs_factor = DVFS_MAX
        ioc.dvfs(dvfs_factor)
        perf = perf + (1-self.f)/ioc.perf()

        #parallel
        #ioc.dvfs(DVFS_MAX)
        num = self.power/ioc.power()
        perf = perf + self.f / (num*ioc.perf())

        return 1/perf

class HeteroSystem(System):
    def build(self):
        c = O3Core()
        self.corelist.append(c)
        a = c.area
        c = IOCore()
        a = a + c.area
        while a < self.area:
            self.corelist.append(c)
            a += c.area

    def speedup(self):
        if not self.corelist:
            print "There are no cores to optimize"
            return 0

        #Serial
        o3c = self.corelist[0]
        if not isinstance(o3c, O3Core):
            print "No O3Core found in HeteroSystem"
            return 0

        perf = 0
        dvfs_factor = math.pow(self.power/o3c.power(), 0.333)
        #if dvfs_factor > DVFS_MAX:
            #dvfs_factor = DVFS_MAX
        o3c.dvfs(dvfs_factor)
        perf = perf + (1-self.f)/o3c.perf()

        #parallel
        ioc = self.corelist[1]
        if not isinstance(ioc, IOCore):
            print "No IOCore found in HeteroSystem"
            return 0

        dvfs_factor = math.pow(self.power/((len(self.corelist)-1)*ioc.power()), 0.333)
        #if dvfs_factor > DVFS_MAX :
            #dvfs_factor = DVFS_MAX

        ioc.dvfs(dvfs_factor)
        perf = perf + self.f / ((len(self.corelist)-1)*ioc.perf())

        return 1/perf

class DynSystem(System):
    # fuse_factor: how many IO cores are fused
    def __init__(self, fuse_factor=4):
        self.ff = fuse_factor

    def setFuseFactor(self, fuse_factor):
        self.ff = fuse_factor

    def build(self):
        c = IOCore()
        a = c.area
        while a < self.area:
            self.corelist.append(c)
            a += c.area

    def speedup(self):
        if not self.corelist:
            print "There are no cores to optimize"
            return 0

        #Serial
        o3c = self.corelist[0]
        if not isinstance(o3c, O3Core):
            print "No O3Core found in HeteroSystem"
            return 0

        perf = 0
        dvfs_factor = math.pow(self.power/o3c.power(), 0.333)
        #if dvfs_factor > DVFS_MAX:
            #dvfs_factor = DVFS_MAX
        o3c.dvfs(dvfs_factor)
        perf = perf + (1-self.f)/o3c.perf()

        #parallel
        ioc = self.corelist[1]
        if not isinstance(ioc, IOCore):
            print "No IOCore found in HeteroSystem"
            return 0

        dvfs_factor = math.pow(self.power/((len(self.corelist)-1)*ioc.power()), 0.333)
        #if dvfs_factor > DVFS_MAX :
            #dvfs_factor = DVFS_MAX

        o3c.dvfs(dvfs_factor)
        perf = perf + self.f / ((len(self.corelist)-1)*ioc.perf())

        return 1/perf

class SymmetricSystem(System):
    def __init__(self, core=IOCore(), 
                 budget={'area':500, 'power':200}):
        System.__init__(self)
        
        self.power = budget['power']
        self.area = budget['area']
        

        self.set_core(core)

    
    def set_core(self, core):
        self.core = core

        mech = core.mech
        tech = core.tech

        dvfs_lb = core.get_dvfs_lb() 
        freq_factor, perf, power = core.dvfs(dvfs_lb)
        self.urmax = min( (self.power/power)/(self.area/core.area), 1)

        dvfs_ub = core.get_dvfs_ub()
        freq_factor, perf, power = core.dvfs(dvfs_ub)
        self.urmin = (self.power/power)/(self.area/core.area)

        self.sperf = perf

        self.cnum = self.area / core.area

        self.set_util_ratio(self.ur) # update parallel perforamnce

    def set_util_ratio(self, ratio):
        if ratio > self.urmax:
            self.ur = self.urmax
        elif ratio < self.urmin:
            self.ur = self.urmin
        else:
            self.ur = ratio


        dvfs_factor = math.pow( (self.power*self.core.area)/(self.ur*self.core.p0*self.area), 0.333)
        
        freq_factor, perf, power = self.core.dvfs(dvfs_factor)

        self.pperf = perf

        self.acnum = self.cnum * self.ur
        
class SimpleSystem(System):
    def __init__(self, core=IOCore(), 
                 budget={'area':500, 'power':200}):
        System.__init__(self)
        
        self.power = budget['power']
        self.area = budget['area']
    

    def plotDVFS(self, step=0.1):
        c = IOCore()
        l = c.get_dvfs_lb()
        u = c.get_dvfs_ub()
        samples = int(math.floor(l*0.1/step))
        volts = []
        freqs = []
        for i in range(1, 1+samples):
            v_factor = l + i * step
            freq_factor, dummya, dummyb= c.dvfs(v_factor)
            volts.append(v_factor)
            freqs.append(freq_factor)
        
        #if ( l+samples*step < u):
            #freq_factor, dummya, dyummyb= c.dvfs(u)
            #volts.append(u)
            #freqs.append(freq_factor)

        #refs = np.arange(0.4, 1.5, 0.1)

        #plt.plot(volts, freqs, refs, refs) 
        plt.plot(volts, freqs) 
        plt.grid(True)
        plt.show()
