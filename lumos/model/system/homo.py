#!/usr/bin/env python

import logging
from ..core import IOCore_CMOS as IOCore, O3Core_CMOS as O3Core
from ..core.io_cmos import PERF_BASE
from ..application import App

VMIN = 300
VMAX = 1100
VSF_MAX = 1.3  # maxium vdd is 1.3 * vdd_nominal
V_PRECISION = 1  # 1mV


from lumos import settings
_logger = logging.getLogger('HomogSys')
if settings.DEBUG:
    _logger.setLevel(logging.DEBUG)
else:
    _logger.setLevel(logging.INFO)

class HomogSys(object):
    """
    This class models a homogeneous many core system composed of
    either in-order cores or out-of-order cores.

    Args:
       area (num):
          Area budget of the system.
       power (num):
          Power budget of the system.

    """
    def __init__(self, area=None, power=None):
        if area:
            self.area = area
        else:
            self.area = 0

        if power:
            self.power = power
        else:
            self.power = 0

        self.core = IOCore(tech=45, model_name='hp')

    def set_core_prop(self, **kwargs):
        """
        Set properties of the core in the system. It just calls the corresponding
        method of the core object.

        Args:
           Named property and its value.

        Returns:
           N/A

        """
        self.core.config(**kwargs)

    def set_sys_prop(self, **kwargs):
        """
        Set properties of the core in the system. Any property can be set
        by this method, such as budgets of area and power, and the composed
        core.

        Args:
           Named property and its value.

        Returns:
           N/A
        """
        for k, v in kwargs.items():
            k = k.lower()
            setattr(self, k, v)

    def get_core_num(self):
        """
        Get the number of cores for the system under area constraint.

        Args:
           N/A

        Returns:
           The number of cores
        """
        core = self.core
        return int(self.area / core.area)


    def perf_by_vdd(self, vdd, app=App(f=0.99)):
        """
        Get the relative performance of the system for a given application, after
        scaling the supply voltage by the given value.

        Args:
           vdd (num):
              The voltage to be scaled to.
           app (:class:`~lumos.model.application.App`):
              The targeted application.

        Returns:
           perf (num):
              The relatvie performance.
           active (num):
              The number of active cores. If it less than the number of
              available cores, then it turns to be a dark silicon configuration.
           core (num):
              The number of available cores on system.
           util (num):
              The utilization of the system at given supply voltage.
        """
        core = self.core
        f = app.f

        core.vdd = min(core.vnom*VSF_MAX, core.vmax)
        sperf=core.perf

        core.vdd = vdd
        active_num = min(int(self.area / core.area),
                         int(self.power / core.power))

        perf = 1/ ((1 - f) / sperf + f / (active_num * core.perf))
        core_num = int(self.area / core.area)
        util = float(100*active_num)/float(core_num)
        return {'perf': perf/PERF_BASE,
                'active': active_num,
                'core' : core_num,
                'util': util}

    def perf_by_cnum(self, cnum, app=App(f=0.99), vmin=None):
        """
        Get the relative performance of the system for a given application, with a
        given constraint on the number of active cores.

        Args:
           cnum (num):
              The number of core required to be active.
           app (:class:`~lumos.model.application.App`):
              The targeted application.
           vmin (num):
              An optional argument to specify the lowest boundary which supply
              voltage can be scaled down.

        Returns:
           perf (num):
              The relatvie performance.
           vdd (num):
              The supply voltage of the optimal configuration under core number
              constraint.
           freq (num):
              The frequency with the optimal configuration under core number
              constraint.
           cnum (num):
              The actual number of active cores, if the requried number can not be met.
           util (num):
              The utilization of the system at the optimal configuraiton.
        """

        core = self.core
        f = app.f

        cnum_max = int(self.area/core.area)

        if cnum > cnum_max or cnum < 0:
            return None

        cpower = self.power/float(cnum)
        _logger.debug('Per-core power budget: {0}'.format(cpower))

        # Serial performance is achieved by the highest vdd
        core.vdd = min(int(core.vnom*VSF_MAX), core.vmax)
        sperf = core.perf

        if not vmin:
            vmin = core.vmin

        # Check whether vmin can meet the power requirement
        if vmin >= core.vmin:
            core.vdd = vmin
            if core.power > cpower:
                # Either vmin is too high or active_cnum is too large
                # so that the system could not meet the power budget even
                # with the minimum vdd. Return the active core number with vmin
                # Users can capture the exception by comparing the active_cnum
                # and the returned active_cnum
                active_cnum = min(int(self.area/core.area),
                                 int(self.power/core.power))

                perf = 1/((1-f)/sperf + f/(active_cnum*core.perf))
                util = float(100*active_cnum)/float(cnum)
                _logger.debug('vmin is too high or active_cnum is too large')
                return {'perf': perf/PERF_BASE,
                        'vdd': vmin,
                        'cnum': active_cnum,
                        'freq': core.freq,
                        'util': util}
        else:
            vmin = core.vmin


        vl = vmin
        vr = min(int(core.vnom * VSF_MAX), core.vmax)
        vm = int((vl+vr)/2)

        while (vr-vl)>V_PRECISION:
            vm = int((vl+vr)/2)
            core.vdd = vm

            _logger.debug('[Core]\t:vl: {0}mV, vr: {1}mV, vm: {2}mV, freq: {3}, power: {4}, area: {5}'.format(vl, vr, vm, core.freq, core.power, core.area))
            if core.power > cpower:
                vl = vl
                vr = vm
            else:
                vl = vm
                vr = vr

        _logger.debug('End of bin-search, vl: {0}mV, vr: {1}mV'.format(vl, vr))
        core.vdd = vl
        lpower = core.power
        lfreq = core.freq
        lcnum = min(int(self.area/core.area),
                    int(self.power/lpower))
        lperf = 1/((1-f)/sperf + f/(cnum*core.perf))

        core.vdd = vr
        rpower = core.power
        rfreq = core.freq
        rcnum = min(int(self.area/core.area),
                    int(self.power/rpower))
        rperf = 1/((1-f)/sperf + f/(cnum*core.perf))

        if rpower <= cpower:
            # right bound meets the power constraint
            return {'perf': rperf/PERF_BASE,
                    'vdd': vr,
                    'cnum': cnum,
                    'freq': rfreq,
                    'util': float(100*cnum)/float(cnum_max)}
        else:
            return {'perf': lperf/PERF_BASE,
                    'vdd': vl,
                    'freq': lfreq,
                    'cnum': cnum,
                    'util': float(100*cnum)/float(cnum_max)}




    def speedup_by_vfslist(self, vfs_list, app=App(f=0.99)):
        core = self.core

        #para_ratio = 0.99
        f = app.f

        #core.dvfs_by_volt(VMAX)
        core.dvfs_by_factor(VSF_MAX)
        #sperf = core.perf0*core.freq
        sperf = core.perf

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
            #perf = 1/ ((1-f)/sperf + f/(active_num*core.perf0*core.freq))
            perf = 1/ ((1-f)/sperf + f/(active_num*core.perf))
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
        core = self.core

        #para_ratio = 0.99
        f = app.f

        #core.dvfs_by_volt(VMAX)
        core.dvfs_by_factor(VSF_MAX)
        #sperf = core.perf0*core.freq
        sperf = core.perf

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
            #perf = 1/ ((1-f)/sperf + f/(active_num*core.perf0*core.freq))
            perf = 1/ ((1-f)/sperf + f/(active_num*core.perf))
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
                freq = r['freq']
                optimal_cnum = cnum

        return {'cnum': optimal_cnum,
                'vdd' : vdd,
                'freq': freq,
                'util': util,
                'perf': perf}


    def perf_by_dark(self, app=App(f=0.99)):
        core = self.core
        f = app.f

        #core.dvfs_by_volt(VMAX)
        core.dvfs_by_factor(VSF_MAX)
        #sperf=core.perf0*core.freq
        sperf=core.perf

        vdd = core.v0 * VSF_MAX

        active_num = min(int(self.area/core.area),
                         int(self.power/core.power))
        #perf = 1/ ((1-f)/sperf + f/(active_num*core.perf0*core.freq))
        perf = 1/ ((1-f)/sperf + f/(active_num*core.perf))
        core_num = int(self.area/core.area)
        util = float(100*active_num)/float(core_num)
        return {'perf': perf/PERF_BASE,
                'active': active_num,
                'core' : core_num,
                'util': util,
                'vdd': vdd}

