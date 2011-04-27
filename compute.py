#!/usr/bin/env python

import math

# default voltage at 45nm
vdd_base = 1
vdd_scl = {}
vdd_scl['itrs'] = {45 : 1, 32 : 0.93,
                   22 : 0.84, 16 : 0.75,
                   11 : 0.68, 8  : 0.62}
vdd_scl['cons'] = {45 : 1, 32 : 0.93,
                   22 : 0.88, 16 : 0.86,
                   11 : 0.84, 8  : 0.84}

freq_base = {'io': 4.2, 'o3': 3.7}
freq_scl = {}
freq_scl['itrs'] = {45 : 1, 32 : 1.09,
                    22 : 2.38, 16 : 3.21,
                    11 : 4.17, 8  : 3.85}
freq_scl['cons'] = {45 : 1, 32 : 1.10,
                    22 : 1.19, 16 : 1.25,
                    11 : 1.30, 8 : 1.34}

power_base = {'io':6.14, 'o3': 19.83}
power_scl = {}
power_scl['itrs'] = {45 : 1, 32 : 0.66,
                     22 : 0.54, 16 : 0.38,
                     11 : 0.25, 8  : 0.12}
power_scl['cons'] = {45 : 1, 32 : 0.71,
                     22 : 0.52, 16 : 0.39,
                     11 : 0.29, 8  : 0.22}

area_base = {'io':7.65, 'o3': 26.48}
area_scl = {45 : 1, 32 : 0.5,
            22 : math.pow(0.5, 2),
            16 : math.pow(0.5, 3),
            11 : math.pow(0.5, 4),
            8  : math.pow(0.5, 5)}

# adopted from 2010Tables_FEP_FOCUS_C_ITRS.xls, sheet 2009_FEP2-HPDevice
vth_base={45 : 0.3201, 32 : 0.297,
          22 : 0.2673, 16 : 0.2409,
          11 : 0.2178,  8 : 0.198}

# Upper and lower bounds for DVFS ratio
DVFS_U_BOUND = {'itrs': dict([(tech, 1.3) for tech in vth_base]),
                'cons': dict([(tech, 1.3) for tech in vth_base])}
DVFS_L_BOUND = {'itrs': dict([(tech, vth_base[tech]/(vdd_scl['itrs'][tech]*vdd_base)) for tech in vth_base]),    
                'cons': dict([(tech, vth_base[tech]/(vdd_scl['cons'][tech]*vdd_base)) for tech in vth_base])}    

def freqRatio(vratio, tech, scltable):
    v0 = vdd_base * scltable[tech]
    v1 = v0 * vratio
    vth = vth_base[tech]
    vmin = v1-vth

    
class Core:
    def __init__ (self, area, freq, tech=45):
        self.area = area
        self.tech = tech
        self.freq = freq
        self.volt = voltage

    def perf(self):
        return math.sqrt(self.area)*self.freq

    def dvfs(self, ratio):
        if ratio > DVFS_MAX or ratio < DVFS_MIN:
            return
        self.freq = self.freq * ratio
        self.volt = self.volt * ratio

class IOCore(Core):
    def __init__ (self, tech=45, area=7.65, power=6.14, frequency=4.2, voltage=1):
        Core.__init__(self, area, frequency, voltage, tech)
        self.f0=4.2
        self.p0=6.14
        self.v0=1

    def power(self):
        return self.p0 * (self.volt/self.v0)**2 * (self.freq/self.f0)
        
class O3Core(Core):
    def __init__ (self, tech=45, area=26.48, power=19.83, frequency=3.7, voltage=1):
        Core.__init__(self, area, frequency, voltage, tech)
        self.f0=3.7
        self.p0=19.83
        self.v0=1

    def power(self):
        return self.p0 * (self.volt/self.v0)**2 * (self.freq/self.f0)

class System:
    def __init__(self, area=500, power=200):
        self.corelist = []
        self.area = area
        self.power = power
        self.cnum = 0 # the number of cores
        self.sperf = 0 # serial performance
        self.pperf = 0 # parallel performance
        self.acnum = 0 # the number of active cores in parallel mode

    def speedup(self, app):
        f = app.f
        return 1/((1-f)/self.sperf + f/(self.pperf*self.acnum))

class Application:
    """ An application is a program a system runs for. The application has certain characteristics, such as parallel ratio """
    def __init__(self, f=0.9):
        """ Initialize an application
        
        Arguments:
        f -- the fraction of parallel part of program (default 0.9)
        
        """
        self.f = f

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
        if dvfs_factor > DVFS_MAX:
            dvfs_factor = DVFS_MAX
        ioc.dvfs(dvfs_factor)
        perf = perf + (1-self.f)/ioc.perf()

        #parallel
        dvfs_factor = math.pow(self.power/(len(self.corelist)*ioc.power()), 0.333)
        if dvfs_factor > DVFS_MAX :
            dvfs_factor = DVFS_MAX
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
        if dvfs_factor > DVFS_MAX:
            dvfs_factor = DVFS_MAX
        ioc.dvfs(dvfs_factor)
        perf = perf + (1-self.f)/ioc.perf()

        #parallel
        ioc.dvfs(DVFS_MAX)
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
        if dvfs_factor > DVFS_MAX:
            dvfs_factor = DVFS_MAX
        o3c.dvfs(dvfs_factor)
        perf = perf + (1-self.f)/o3c.perf()

        #parallel
        ioc = self.corelist[1]
        if not isinstance(ioc, IOCore):
            print "No IOCore found in HeteroSystem"
            return 0

        dvfs_factor = math.pow(self.power/((len(self.corelist)-1)*ioc.power()), 0.333)
        if dvfs_factor > DVFS_MAX :
            dvfs_factor = DVFS_MAX

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
        if dvfs_factor > DVFS_MAX:
            dvfs_factor = DVFS_MAX
        o3c.dvfs(dvfs_factor)
        perf = perf + (1-self.f)/o3c.perf()

        #parallel
        ioc = self.corelist[1]
        if not isinstance(ioc, IOCore):
            print "No IOCore found in HeteroSystem"
            return 0

        dvfs_factor = math.pow(self.power/((len(self.corelist)-1)*ioc.power()), 0.333)
        if dvfs_factor > DVFS_MAX :
            dvfs_factor = DVFS_MAX

        o3c.dvfs(dvfs_factor)
        perf = perf + self.f / ((len(self.corelist)-1)*ioc.perf())

        return 1/perf


def main():
    sys = O3System()
    sys.build()
    sys.setParaFactor(0.9)
    print "O3System dim: %f" % sys.dimsi()
    print "O3System dark: %f" % sys.darksi()
    sys = IOSystem()
    sys.build()
    sys.setParaFactor(0.9)
    print "IOSystem dim: %f" % sys.dimsi()
    print "IOSystem dark: %f" % sys.darksi()
    sys = HeteroSystem()
    sys.build()
    sys.setParaFactor(0.9)
    print "HeteroSystem: %f\n" % sys.speedup()


if __name__ == '__main__':
    main()
