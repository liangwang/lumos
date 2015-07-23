#!/usr/bin/env python

import logging
from ..core import BaseCore
PERF_BASE = 12.92

VMIN = 300
VMAX = 1100
VSF_MAX = 1.3  # maxium vdd is 1.3 * vdd_nominal
V_PRECISION = 1  # 1mV


from lumos import settings
_logger = logging.getLogger('HomogSys')
if settings.LUMOS_DEBUG:
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

        self.core = BaseCore(45, 'cmos', 'hp', 'io')

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


    def perf_by_vdd(self, vdd, app):
        """
        Get the relative performance of the system for a given application, after
        scaling the supply voltage by the given value.

        Args:
           vdd (num):
              The voltage to be scaled to.
           app (:class:`~lumos.model.application.Application`):
              The targeted application.

        Returns:
          dict: results wrapped in a python dict with three keys:

          perf (float):
            Relative performance, also should be the optimal with the given
            system configuration.
          cnum (int):
            The number of active cores for the optimal configuration.
          vdd (float):
            The supply voltage of throughput cores when executing parallel part
            of the application.

          For example, a results dict::

            {
              'perf': 123.4,
              'cnum': 12,
              'vdd': 800,
            }

        """
        core = self.core
        f = app.f

        vdd_max = min(core.vnom*VSF_MAX, core.vmax)
        sperf=core.perf_by_vdd(vdd_max)

        core.vdd = vdd
        active_num = min(int(self.area / core.area),
                         int(self.power / core.power(vdd)))

        perf = 1/ ((1 - f) / sperf + f / (active_num * core.perf_by_vdd(vdd)))
        core_num = int(self.area / core.area)
        util = float(100*active_num)/float(core_num)
        return {'perf': perf/PERF_BASE,
                'active': active_num,
                'core' : core_num,
                'util': util}

    def perf_by_cnum(self, cnum, app, vmin=None):
        """
        Get the relative performance of the system for a given application, with a
        given constraint on the number of active cores.

        Parameters
        ----------
        cnum: num
          The number of core required to be active.
        app: :class:`~lumos.model.application.Application`
          The targeted application.
        vmin: num
          An optional argument to specify the lowest boundary which supply
          voltage can be scaled down.

        Returns
        -------
        dict: results wrapped in a python dict with three keys:

        perf : num
          The relatvie performance.
        vdd : num
          The supply voltage of the optimal configuration under core number
          constraint.
        freq : num
          The frequency with the optimal configuration under core number
          constraint.
        cnum : num
          The actual number of active cores, if the requried number can not be met.
        util : num
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
        sperf = core.perf_by_vdd(core.vmax)

        if not vmin:
            vmin = core.vmin

        # Check whether vmin can meet the power requirement
        if vmin >= core.vmin:
            if core.power(vmin) > cpower:
                # Either vmin is too high or active_cnum is too large
                # so that the system could not meet the power budget even
                # with the minimum vdd. Return the active core number with vmin
                # Users can capture the exception by comparing the active_cnum
                # and the returned active_cnum
                active_cnum = min(int(self.area/core.area),
                                  int(self.power/core.power(vmin)))

                perf = 1/((1-f)/sperf + f/(active_cnum*core.perf_by_vdd(vmin)))
                util = float(100*active_cnum)/float(cnum)
                _logger.debug('vmin is too high or active_cnum is too large')
                return {'perf': perf/PERF_BASE,
                        'vdd': vmin,
                        'cnum': active_cnum,
                        'freq': core.freq(vmin),
                        'util': util}
        else:
            vmin = core.vmin


        vl = vmin
        vr = core.vmax
        vm = int((vl+vr)/2)

        while (vr-vl)>V_PRECISION:
            vm = int((vl+vr)/2)

            _logger.debug('[Core]\t:vl: {0}mV, vr: {1}mV, vm: {2}mV, freq: {3}, power: {4}, area: {5}'.format(vl, vr, vm, core.freq(vm), core.power(vm), core.area))
            if core.power(vm) > cpower:
                vl = vl
                vr = vm
            else:
                vl = vm
                vr = vr

        _logger.debug('End of bin-search, vl: {0}mV, vr: {1}mV'.format(vl, vr))
        core.vdd = vl
        lpower = core.power(vl)
        lfreq = core.freq(vl)
        lcnum = min(int(self.area/core.area),
                    int(self.power/lpower))
        lperf = 1/((1-f)/sperf + f/(cnum*core.perf_by_vdd(vl)))

        rpower = core.power(vr)
        rfreq = core.freq(vr)
        rcnum = min(int(self.area/core.area),
                    int(self.power/rpower))
        rperf = 1/((1-f)/sperf + f/(cnum*core.perf_by_vdd(vr)))

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




    def speedup_by_vfslist(self, vfs_list, app):
        raise NotImplementedError()
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
            active_num = min(self.area/core.area, self.power/core.power(vfs*core.vnom))
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

    def speedup_by_vlist(self, v_list, app):
        raise NotImplementedError()
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
            active_num = min(self.area/core.area, self.power/core.power(v))
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

    def opt_core_num(self, app, vmin=VMIN):

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


    def perf_by_dark(self, app):
        core = self.core
        f = app.f

        #core.dvfs_by_volt(VMAX)
        core.dvfs_by_factor(VSF_MAX)
        #sperf=core.perf0*core.freq
        sperf=core.perf

        vdd = core.v0 * VSF_MAX

        active_num = min(int(self.area/core.area),
                         int(self.power/core.power(vdd)))
        #perf = 1/ ((1-f)/sperf + f/(active_num*core.perf0*core.freq))
        perf = 1/ ((1-f)/sperf + f/(active_num*core.perf))
        core_num = int(self.area/core.area)
        util = float(100*active_num)/float(core_num)
        return {'perf': perf/PERF_BASE,
                'active': active_num,
                'core' : core_num,
                'util': util,
                'vdd': vdd}

from .budget import Sys_L
class SysConfigDetailed():
    def __init__(self):
        self.tech = 22
        self.core_type = 'io'
        self.core_tech_name = 'cmos'
        self.core_tech_variant = 'hp'
        self.budget = Sys_L
        self.delay_l1 = 3
        self.delay_l2 = 20
        self.delay_mem = 426
        self.cache_sz_l1 = 65536
        # self.cache_sz_l2 = 12582912
        self.cache_sz_l2 = 33554432 # 32MB

from lumos.model.mem import cache
class HomoSysDetailed():
    def __init__(self, sysconfig):
        self.sys_area = sysconfig.budget.area
        self.sys_power = sysconfig.budget.power
        self.sys_bw = sysconfig.budget.bw

        self.core = BaseCore(sysconfig.tech, sysconfig.core_tech_name,
                             sysconfig.core_tech_variant, sysconfig.core_type)
        self.delay_l1 = sysconfig.delay_l1
        self.delay_l2 = sysconfig.delay_l2
        self.delay_mem = sysconfig.delay_mem
        self.cache_sz_l1 = sysconfig.cache_sz_l1
        cache_tech_type = '-'.join([sysconfig.core_type.split('-')[1], sysconfig.core_tech_variant] )
        self.l1_traits = cache.CacheTraits(self.cache_sz_l1, cache_tech_type, sysconfig.tech)
        self.cache_sz_l2 = sysconfig.cache_sz_l2
        self.l2_traits = cache.CacheTraits(self.cache_sz_l2, cache_tech_type, sysconfig.tech)

    def get_cnum(self, vdd):
        core = self.core
        core_power = core.power(vdd)
        _logger.debug('core_power: {0}'.format(core_power))
        l2_power = self.l2_traits.power
        _logger.debug('l2_power: {0}'.format(l2_power))
        l1_power = self.l1_traits.power
        _logger.debug('l1_power: {0}'.format(l1_power))
        cnum = min((self.sys_power-l2_power)/(core_power+l1_power), self.sys_area/core.area)
        return int(cnum)

    def perf(self, vdd, app, cnum=None):
        if not cnum:
            cnum = self.get_cnum(vdd)

        _logger.debug('cnum: {0}'.format(cnum))
        core = self.core
        _logger.debug('freq: {0}'.format(core.freq(vdd)))
        miss_l1 = min(1, app.miss_l1 * ((self.cache_sz_l1/(app.cache_sz_l1_nom)) ** (1-app.alpha_l1)))
        miss_l2 = min(1, app.miss_l2 * ((self.cache_sz_l2/(cnum*app.cache_sz_l2_nom)) ** (1-app.alpha_l2)))
        _logger.debug('l1_miss: {0}, l2_miss: {1}'.format(miss_l1, miss_l2))
        t0 = ((1-miss_l1)*self.delay_l1 + miss_l1*(1-miss_l2)*self.delay_l2 +
              miss_l1*miss_l2*self.delay_mem)
        t = t0 * core.freq(vdd) / core.freq(core.vnom)
        _logger.debug('t: {0}'.format(t))
        eta = 1 / (1 + t * app.rm / app.cpi_exe)
        _logger.debug('eta: {0}'.format(eta))
        p_speedup = core.perf_by_vdd(vdd) * cnum * eta / PERF_BASE
        _logger.debug('p_speedup: {0}'.format(p_speedup))

        vdd_max = min(core.vnom * VSF_MAX, core.vmax)
        s_speedup = core.perf_by_vdd(vdd_max) / PERF_BASE
        _logger.debug('s_speedup: {0}'.format(s_speedup))

        perf = 1 / ( (1-app.pf)/s_speedup + app.pf/p_speedup)
        return perf
