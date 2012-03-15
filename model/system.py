#!/usr/bin/env python

from core import Core
from app import App 

from tech import Base
import math
PERF_BASE = math.sqrt(Base.area['IO']) * Base.freq['IO']
VMIN = 0.3
VMAX = 1.1
VSF_MAX = 1.3 # maxium vdd is 1.3 * vdd_nominal
V_PRECISION = 0.001 # 1mV
PROBE_PRECISION = 0.0001


from conf import misc as miscConfig
DEBUG=miscConfig.debug

class SymSystem(object):
    def __init__(self, area=None, power=None):
        if area:
            self.area=area
        else:
            self.area=0

        if power:
            self.power= power
        else:
            self.power = 0

    def set_core_prop(self, **kwargs):
        self.core.config(**kwargs)

    def set_sys_prop(self, **kwargs):
        for k,v in kwargs.items():
            k=k.lower()
            setattr(self, k, v)

    def get_core_num(self):
        core = self.core
        return int(self.area/core.area)

    def perf_by_vfs(self, vfs, app=App(f=0.99)):
        core = self.core
        f = app.f

        #core.dvfs_by_volt(VMAX)
        core.dvfs_by_factor(VSF_MAX)
        sperf=core.perf0*core.freq

        core.dvfs_by_factor(vfs)
        active_num = min(int(self.area/core.area), 
                         int(self.power/core.power))
        perf = 1/ ((1-f)/sperf + f/(active_num*core.perf0*core.freq))
        core_num = int(self.area/core.area)
        util = float(100*active_num)/float(core_num)
        return {'perf': perf/PERF_BASE,
                'active': active_num,
                'core' : core_num,
                'util': util}
    def perf_by_vdd(self, vdd, app=App(f=0.99)):
        core = self.core
        f = app.f

        #core.dvfs_by_volt(VMAX)
        core.dvfs_by_factor(VSF_MAX)
        sperf=core.perf0*core.freq

        core.dvfs_by_volt(vdd)
        active_num = min(int(self.area/core.area), 
                         int(self.power/core.power))
        perf = 1/ ((1-f)/sperf + f/(active_num*core.perf0*core.freq))
        core_num = int(self.area/core.area)
        util = float(100*active_num)/float(core_num)
        return {'perf': perf/PERF_BASE,
                'active': active_num,
                'core' : core_num,
                'util': util}

    def perf_by_cnum(self, cnum, app=App(f=0.99), vmin=VMIN):

        core = self.core
        f = app.f

        cnum_max = int(self.area/core.area)

        if cnum > cnum_max or cnum < 0:
            return None

        cpower = self.power/float(cnum)
        #print cpower

        # Serial performance is achieved by the highest vdd
        #core.dvfs_by_volt(VMAX)
        core.dvfs_by_factor(VSF_MAX)
        sperf=core.perf0*core.freq
        if DEBUG:
            print 'sperf: %g, freq: %g' % (sperf, core.freq)

        # Check whether vmin can meet the power requirement
        if vmin > VMIN:
            core.dvfs_by_volt(vmin)
            if core.power > cpower:
                # Either vmin is too high or active_cnum is too large
                # so that the system could not meet the power budget even
                # with the minimum vdd. Return the active core number with vmin
                # Users can capture the exception by comparing the active_cnum 
                # and the returned active_cnum
                active_cnum = min(int(self.area/core.area), 
                                 int(self.power/core.power))
                perf = 1/((1-f)/sperf + f/(active_cnum*core.perf0*core.freq))
                util = float(100*active_cnum)/float(cnum)
                return {'perf': perf/PERF_BASE,
                        'vdd': vmin,
                        'cnum': active_cnum,
                        'util': util}
        else:
            vmin = VMIN
            

        vl = vmin
        vr = core.v0 * VSF_MAX
        vm = (vl+vr)/2

        while (vr-vl)>V_PRECISION:
            vm = (vl+vr)/2
            core.dvfs_by_volt(vm)
            

            #print '[Core]\t:vl:%f, vr: %f, vm: %f, freq: %f, power: %f, area: %f' % (vl, vr, vm, core.freq, core.power, core.area)
            if core.power > cpower: 
                vl = vl
                vr = vm
            else:
                vl = vm
                vr = vr

        core.dvfs_by_volt(vl)
        lpower = core.power
        lcnum = min(int(self.area/core.area), 
                    int(self.power/lpower))
        lperf = 1/((1-f)/sperf + f/(cnum*core.perf0*core.freq))

        core.dvfs_by_volt(vr)
        rpower = core.power
        rcnum = min(int(self.area/core.area), 
                    int(self.power/rpower))
        rperf = 1/((1-f)/sperf + f/(cnum*core.perf0*core.freq))

        if rpower <= cpower:
            # right bound meets the power constraint
            return {'perf': rperf/PERF_BASE,
                    'vdd': vr,
                    'cnum': cnum,
                    'util': float(100*cnum)/float(cnum_max)}
        else:
            return {'perf': lperf/PERF_BASE,
                    'vdd': vl,
                    'cnum': cnum,
                    'util': float(100*cnum)/float(cnum_max)}


        #if vr == vm:
            #core.dvfs_by_volt(vl)

        ## debug use only
        ##if active_cnum == cnum:
            ##print 'freq: %g, vdd: %g, perf_base: %g' % (core.freq, core.vdd, PERF_BASE)
        ## end debug
        #perf = 1/((1-f)/sperf + f/(active_cnum*core.perf0*core.freq))
        #util = float(100*active_cnum)/float(cnum)
        #return {'perf': perf/PERF_BASE,
                #'vdd': vm,
                #'cnum': active_cnum,
                #'util': util}


    def probe2(self, app=App(f=0.99)):
        core = self.core
        f = app.f

        v0 = core.v0
        vleft = VMIN
        vright = v0 * VSF_MAX
        vpivot = (vleft+vright)/2

        #core.dvfs_by_volt(VMAX)
        core.dvfs_by_factor(VSF_MAX)
        sperf = core.perf0*core.freq

        while (vpivot-vleft) > (PROBE_PRECISION/2) :
            vl = vpivot - PROBE_PRECISION / 2
            vr = vpivot + PROBE_PRECISION / 2

            core.dvfs_by_volt(vl)
            active_num = min(self.area/core.area, self.power/core.power)
            l_num = active_num
            sl = 1/ ( (1-f)/sperf + f/(active_num*core.perf0*core.freq))

            core.dvfs_by_volt(vpivot)
            active_num = min(self.area/core.area, self.power/core.power)
            p_num = active_num
            sp = 1/ ( (1-f)/sperf + f/(active_num*core.perf0*core.freq))
            core_num = active_num

            core.dvfs_by_volt(vr)
            active_num = min(self.area/core.area, self.power/core.power)
            r_num = active_num
            sr = 1/ ( (1-f)/sperf + f/(active_num*core.perf0*core.freq))

            #print 'lv: %f, lc: %f, rv: %f, rc: %f, pv: %f, pc: %f' % (vl, l_num, vr, r_num, vpivot, p_num)
            if sl<sp<sr:
                vleft=vpivot
                vpivot = (vleft+vright)/2
            elif sl>sp>sr:
                vright = vpivot
                vpivot = (vleft+vright)/2
            elif sp > sl and sp > sr:
                # vpivot is the optimal speedup point
                break

        self.volt = vpivot
        self.speedup = sp/PERF_BASE
        self.util = core_num*core.area/self.area

    def speedup_by_vfslist(self, vfs_list, app=App(f=0.99)):
        #core = Core45nmCon()
        #core = Core(ctype=self.ctype, mech=self.mech, tech=self.tech)
        core = self.core

        #para_ratio = 0.99
        f = app.f

        #core.dvfs_by_volt(VMAX)
        core.dvfs_by_factor(VSF_MAX)
        sperf = core.perf0*core.freq

        perf_list = []
        speedup_list = []
        util_list = []

        #debug code
        #if self.area == 0 or self.power == 0:
            #print 'area: %d, power: %d' % (self.area, self.power)
            #raise Exception('wrong input')
        #end debug

        for vfs in vfs_list:
            # FIXME: dvfs_by_volt for future technology
            core.dvfs_by_factor(vfs)
            active_num = min(self.area/core.area, self.power/core.power)
            perf = 1/ ((1-f)/sperf + f/(active_num*core.perf0*core.freq))
            speedup_list.append(perf/PERF_BASE)
            util = 100*active_num*core.area/self.area
            util_list.append(util)

            # code segment for debug
            #import math
            #if math.fabs(vsf-0.55)<0.01 and self.power==110 and self.area==5000:
                #print 'area %d: active_num %f, perf %f, core power %f, core area %f, sys util %f' % (self.area, active_num, perf, core.power, core.area, util)
            #if math.fabs(vsf-0.6)<0.01 and self.power==110 and self.area==4000:
                #print 'area %d: active_num %f, perf %f, core power %f, core area %f, sys util %f' % (self.area, active_num, perf, core.power, core.area, util)
            # end debug

        return (speedup_list,util_list)

    def speedup_by_vlist(self, v_list, app=App(f=0.99)):
        #core = Core45nmCon()
        #core = Core(ctype=self.ctype, mech=self.mech, tech=self.tech)
        core = self.core

        #para_ratio = 0.99
        f = app.f

        #core.dvfs_by_volt(VMAX)
        core.dvfs_by_factor(VSF_MAX)
        sperf = core.perf0*core.freq

        perf_list = []
        speedup_list = []
        util_list = []

        #debug code
        #if self.area == 0 or self.power == 0:
            #print 'area: %d, power: %d' % (self.area, self.power)
            #raise Exception('wrong input')
        #end debug

        for v in v_list:
            # FIXME: dvfs_by_volt for future technology
            core.dvfs_by_volt(v)
            active_num = min(self.area/core.area, self.power/core.power)
            perf = 1/ ((1-f)/sperf + f/(active_num*core.perf0*core.freq))
            speedup_list.append(perf/PERF_BASE)
            util = 100*active_num*core.area/self.area
            util_list.append(util)

            # code segment for debug
            #import math
            #if math.fabs(vsf-0.55)<0.01 and self.power==110 and self.area==5000:
                #print 'area %d: active_num %f, perf %f, core power %f, core area %f, sys util %f' % (self.area, active_num, perf, core.power, core.area, util)
            #if math.fabs(vsf-0.6)<0.01 and self.power==110 and self.area==4000:
                #print 'area %d: active_num %f, perf %f, core power %f, core area %f, sys util %f' % (self.area, active_num, perf, core.power, core.area, util)
            # end debug

        return (speedup_list,util_list)

    def opt_core_num(self, app=App(f=0.99), vmin=VMIN):

        cnum_max = self.get_core_num()
        cnumList = range(1, cnum_max+1)

        perf = 0
        for cnum in cnumList:
            r = self.perf_by_cnum(cnum, app, vmin)
            if r['cnum'] < cnum:
                break
            if r['perf'] > perf:
                perf = r['perf']
                vdd = r['vdd']
                util = r['util']
                optimal_cnum = cnum

        return {'cnum': optimal_cnum,
                'vdd' : vdd,
                'util': util,
                'perf': perf}


    def perf_by_dark(self, app=App(f=0.99)):
        core = self.core
        f = app.f

        #core.dvfs_by_volt(VMAX)
        core.dvfs_by_factor(VSF_MAX)
        sperf=core.perf0*core.freq

        #vdd = min(core.v0*1.3, VMAX)
        vdd = core.v0 * VSF_MAX
        #core.dvfs_by_volt(vdd)
        #print 'Area:%d, Power: %d, tech: %d, mech: %s, vdd: %g, freq: %g, power: %g' % (self.area, self.power, core.tech, core.mech, core.vdd, core.freq, core.power)
        active_num = min(int(self.area/core.area), 
                         int(self.power/core.power))
        perf = 1/ ((1-f)/sperf + f/(active_num*core.perf0*core.freq))
        core_num = int(self.area/core.area)
        util = float(100*active_num)/float(core_num)
        return {'perf': perf/PERF_BASE,
                'active': active_num,
                'core' : core_num,
                'util': util,
                'vdd': vdd}


class System(object):


    PROBE_PRECISION = 0.0001
    VSF_MIN = 0.2
    VSF_MAX = 1.0


    def __init__(self, area=0, power=0, 
                 ctype='IO', mech='ITRS', tech=45):

        self.numIO = 0
        self.numO3 = 0

        self.area = 0
        self.power= 0

        from tech import Base
        import math
        # Performance of IO core at nominal frequency, according to Pollack's Rule
        self.perf_base = math.sqrt(Base.area['IO']) * Base.freq['IO']

        self.core = Core(ctype=ctype, mech=mech, tech=tech)
        self.ctype = ctype
        self.mech = mech
        self.tech = tech

        self.active_num = 0
        self.perf_max = 0
        self.speedup = 0
        self.util = 0
        self.volt = 0

    def set_core_prop(self, **kwargs):
        self.core.config(**kwargs)

    def set_sys_prop(self, **kwargs):
        for k,v in kwargs.items():
            k=k.lower()
            setattr(self, k, v)

    def build(self,type='sym-io',area=200,power=80):
        self.area = area
        self.power = power

        #if type=='sym-io':
            #iocore = Core45nmCon()
            #self.numIO = area / iocore.area


    def probe(self, app = App(f=0.99)):
        """"
        Sweep voltage (by core.dvfs) to get the best performance for a given app
        """
        #core = Core45nmCon()
        core = Core(ctype=self.ctype, mech=self.mech, tech=self.tech)

        #para_ratio = 0.99
        para_ratio = app.f

        perf_base = core.perf0 * core.f0
        perf_max = perf_base
        core_num = min(self.area/core.area, self.power/core.power)
        util = core_num*core.area/self.area
        volt = core.vdd

        for vsf in [(1-0.0001*i) for i in range(1,10000)]:
            # FIXME: consider dvfs_by_volt for future technology
            core.dvfs_by_factor(vsf)
            active_num = min(self.area/core.area, self.power/core.power)
            perf = 1/ ( (1-para_ratio)/perf_base + para_ratio/(active_num*core.perf0*core.freq))

            if perf > perf_max:
                perf_max = perf
                core_num = active_num
                util = core_num*core.area/self.area
                volt = core.vdd
            else :
                break

        self.active_num = core_num
        self.perf_max = perf_max
        self.speedup = perf_max / perf_base
        self.util = util
        self.volt = volt

    def probe2(self, app=None):
        """"
        A fast version of probe, using binary search
        """
        #core = Core(ctype=self.ctype, mech=self.mech, tech=self.tech)
        if app is None:
            app = App(f=0.99)


        core = self.core
        para_ratio = app.f

        perf_base = self.perf_base

        v0 = core.v0
        vleft = v0 * self.VSF_MIN
        vright = v0 * self.VSF_MAX
        vpivot = (vleft+vright)/2

        # FIXME: assum v0/f0 is the highest v/f
        sperf=core.perf0*core.f0
        while (vpivot-vleft) > (self.PROBE_PRECISION/2) :
            vl = vpivot - self.PROBE_PRECISION / 2
            vr = vpivot + self.PROBE_PRECISION / 2

            core.dvfs_by_volt(vl)
            active_num = min(self.area/core.area, self.power/core.power)
            l_num = active_num
            sl = 1/ ( (1-para_ratio)/sperf + para_ratio/(active_num*core.perf0*core.freq))

            core.dvfs_by_volt(vpivot)
            active_num = min(self.area/core.area, self.power/core.power)
            p_num = active_num
            sp = 1/ ( (1-para_ratio)/sperf + para_ratio/(active_num*core.perf0*core.freq))
            core_num = active_num

            core.dvfs_by_volt(vr)
            active_num = min(self.area/core.area, self.power/core.power)
            r_num = active_num
            sr = 1/ ( (1-para_ratio)/sperf + para_ratio/(active_num*core.perf0*core.freq))

            print 'lv: %f, lc: %f, rv: %f, rc: %f, pv: %f, pc: %f' % (vl, l_num, vr, r_num, vpivot, p_num)
            if sl<sp<sr:
                vleft=vpivot
                vpivot = (vleft+vright)/2
            elif sl>sp>sr:
                vright = vpivot
                vpivot = (vleft+vright)/2
            elif sp > sl and sp > sr:
                # vpivot is the optimal speedup point
                break

        self.volt = vpivot
        self.speedup = sp/perf_base
        self.util = core_num*core.area/self.area



    def get_speedup(self, vsf_list, app=App(f=0.99)):
        #core = Core45nmCon()
        #core = Core(ctype=self.ctype, mech=self.mech, tech=self.tech)
        core = self.core

        #para_ratio = 0.99
        para_ratio = app.f

        #perf_base = core.perf0 * core.freq
        # FIXME: use highest vdd as sperf, other than perf_base
        perf_base = self.perf_base

        perf_list = []
        speedup_list = []
        util_list = []

        #debug code
        #if self.area == 0 or self.power == 0:
            #print 'area: %d, power: %d' % (self.area, self.power)
            #raise Exception('wrong input')
        #end debug

        for vsf in vsf_list:
            # FIXME: dvfs_by_volt for future technology
            core.dvfs_by_factor(vsf)
            active_num = min(self.area/core.area, self.power/core.power)
            perf = 1/ ((1-para_ratio)/perf_base + para_ratio/(active_num*core.perf0*core.freq))
            speedup_list.append(perf/perf_base)
            util = 100*active_num*core.area/self.area
            util_list.append(util)

            # code segment for debug
            #import math
            #if math.fabs(vsf-0.55)<0.01 and self.power==110 and self.area==5000:
                #print 'area %d: active_num %f, perf %f, core power %f, core area %f, sys util %f' % (self.area, active_num, perf, core.power, core.area, util)
            #if math.fabs(vsf-0.6)<0.01 and self.power==110 and self.area==4000:
                #print 'area %d: active_num %f, perf %f, core power %f, core area %f, sys util %f' % (self.area, active_num, perf, core.power, core.area, util)
            # end debug

        return (speedup_list,util_list)
    
            


if __name__ == '__main__':
    import time
    sys = System()
    #sys.build()
    #for area in xrange(100, 1000, 100):
    for area in (500,):
        #for power in xrange(80, 200, 40):
        for power in (150,):
            sys.set_sys_prop(area=area,power=power)
            
            start = time.time()
            sys.probe()
            v = sys.volt
            sp = sys.speedup
            u = sys.util
            stop = time.time()
            print 'Probe for %f, v: %f, speedup: %f, utilization: %f' % (stop-start, v, sp, u)
            start2 = time.time()
            sys.probe2()
            v2 = sys.volt
            sp2 = sys.speedup
            u2 = sys.util
            stop2 = time.time()
            print 'Probe2 for %f, v: %f, speedup: %f, utilization: %f' % (stop-start,v2, sp2, u2)
            print '[Area %d, Power %d]: probe for %f, probe2 for %f, v diff %f, speedup diff %f, utilization diff %f' % \
                    ( area, power, stop-start, stop2-start2, v2-v, sp2-sp, u2-u)

