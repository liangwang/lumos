#!/usr/bin/env python

import logging
from ..core import BaseCore
PERF_BASE = 12.92

VMIN = 300
VMAX = 1100
VSF_MAX = 1.3  # maxium vdd is 1.3 * vdd_nominal
V_PRECISION = 1  # 1mV


from lumos.settings import LUMOS_DEBUG
from lumos import BraceMessage as _bm_

__logger = None

if LUMOS_DEBUG and ('all' in LUMOS_DEBUG or 'homogsys' in LUMOS_DEBUG):
    _debug_enabled = True
else:
    _debug_enabled = False


def _debug(brace_msg):
    global __logger
    if not _debug_enabled:
        return

    if not  __logger:
        __logger = logging.getLogger('HomogSys')
        __logger.setLevel(logging.DEBUG)

    __logger.debug(brace_msg)


class HomogSysError(Exception):
    pass


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
        _debug(_bm_('Per-core power budget: {0}', cpower))

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
                _debug(_bm_('vmin is too high or active_cnum is too large'))
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

            _debug(_bm_('[Core]\t:vl: {0}mV, vr: {1}mV, vm: {2}mV, '
                                     'freq: {3}, power: {4}, area: {5}',
                                     vl, vr, vm, core.freq(vm), core.power(vm), core.area))
            if core.power(vm) > cpower:
                vl = vl
                vr = vm
            else:
                vl = vm
                vr = vr

        _debug(_bm_('End of bin-search, vl: {0}mV, vr: {1}mV', vl, vr))
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
from lumos.model import mem
from lumos.model.mem.cache import get_cache_trait
class SysConfigDetailed():
    def __init__(self):
        # assume l1 have the same technology as cores
        self.tech = mem.BASELINE_L1_TECH_NODE
        self.core_type = 'io'
        self.core_tech_name = mem.BASELINE_L1_TECH_NAME
        self.core_tech_variant = mem.BASELINE_L1_TECH_VARIANT
        self.budget = Sys_L
        self.l2_tech_name = mem.BASELINE_L2_TECH_NAME
        self.l2_tech_variant = mem.BASELINE_L2_TECH_VARIANT
        self.delay_mem = mem.BASELINE_L2_DELAY
        self.cache_sz_l1 = mem.BASELINE_L1_SIZE
        self.cache_sz_l2 = mem.BASELINE_L2_SIZE

    @property
    def l1_tech_name(self):
        return self.core_tech_name

    @property
    def l1_tech_variant(self):
        return self.core_tech_variant


class HomogSysDetailed():
    def __init__(self, sysconfig):
        self.sys_area = sysconfig.budget.area
        self.sys_power = sysconfig.budget.power
        self.sys_bw = sysconfig.budget.bw

        self.core = BaseCore(sysconfig.tech, sysconfig.core_tech_name,
                             sysconfig.core_tech_variant, sysconfig.core_type)

        baseline_cache_tech = '-'.join((mem.BASELINE_L1_TECH_NAME, mem.BASELINE_L1_TECH_VARIANT))
        baseline_traits = get_cache_trait(mem.BASELINE_L1_SIZE,
                                          baseline_cache_tech,
                                          mem.BASELINE_L1_TECH_NODE)

        self.cache_sz_l1 = sysconfig.cache_sz_l1
        l1_tech_type = '-'.join([sysconfig.l1_tech_name, sysconfig.l1_tech_variant] )
        self.l1_traits = get_cache_trait(self.cache_sz_l1, l1_tech_type, sysconfig.tech)

        scale_factor = self.l1_traits['latency'] / baseline_traits['latency']
        self.delay_l1 = int(mem.BASELINE_L1_DELAY * scale_factor )

        baseline_cache_tech = '-'.join((mem.BASELINE_L2_TECH_NAME, mem.BASELINE_L2_TECH_VARIANT))
        baseline_traits = get_cache_trait(mem.BASELINE_L2_SIZE,
                                          baseline_cache_tech,
                                          mem.BASELINE_L2_TECH_NODE)
        self.cache_sz_l2 = sysconfig.cache_sz_l2
        l2_tech_type = '-'.join([sysconfig.l2_tech_name, sysconfig.l2_tech_variant])
        self.l2_traits = get_cache_trait(self.cache_sz_l2, l2_tech_type, sysconfig.tech)

        scale_factor = self.l2_traits['latency'] / baseline_traits['latency']
        self.delay_l2 = int(mem.BASELINE_L2_DELAY * scale_factor)

        self.delay_mem = sysconfig.delay_mem

    def get_cnum(self, vdd):
        core = self.core
        core_power = core.power(vdd)
        _debug(_bm_('core_power: {0}', core_power))
        l2_power = self.l2_traits['power']
        l2_area = self.l2_traits['area']
        _debug(_bm_('l2_power: {0}', l2_power))
        l1_power = self.l1_traits['power']
        l1_area = self.l1_traits['area']
        _debug(_bm_('l1_power: {0}', l1_power))
        cnum = min((self.sys_power-l2_power)/(core_power+l1_power),
                   (self.sys_area-l2_area)/(core.area+l1_area))
        return int(cnum)

    def perf(self, vdd, app, cnum=None):
        if app.type != 'synthetic':
            raise HomogSysError('Requires a synthetic application')

        if not cnum:
            cnum = self.get_cnum(vdd)

        _debug(_bm_('cnum: {0}', cnum))
        core = self.core
        _debug(_bm_('freq: {0}', core.freq(vdd)))
        cov = 1
        perf = 0
        # kernels will be accelerated by multi-cores
        for kid in app.get_all_kernels():
            kcov = app.get_cov(kid)
            kobj = app.get_kernel(kid)

            miss_l1 = min(
                1, kobj.miss_l1 * ((self.cache_sz_l1/(kobj.cache_sz_l1_nom)) ** (1-kobj.alpha_l1)))
            miss_l2 = min(
                1, kobj.miss_l2 * ((self.cache_sz_l2/(cnum*kobj.cache_sz_l2_nom)) ** (1-kobj.alpha_l2)))

            _debug(_bm_('l1_miss: {0}, l2_miss: {1}', miss_l1, miss_l2))
            t0 = ((1-miss_l1)*self.delay_l1 + miss_l1*(1-miss_l2)*self.delay_l2 +
                  miss_l1*miss_l2*self.delay_mem)
            t = t0 * core.freq(vdd) / core.freq(core.vnom)
            _debug(_bm_('t: {0}', t))
            eta = 1 / (1 + t * kobj.rm / kobj.cpi_exe)
            eta0 = 1 / (1+ t0 * kobj.rm / kobj.cpi_exe)
            _debug(_bm_('eta: {0}, eta0: {1}', eta, eta0))
            _debug(_bm_('freq: {0}, freq0: {1}', core.freq(vdd), core.fnom))
            _debug(_bm_('vdd: {0}, v0: {1}', vdd, core.vnom))
            p_speedup = (core.freq(vdd)/core.fnom) * cnum * (eta/eta0)
            _debug(_bm_('p_speedup: {0}', p_speedup))

            vdd_max = min(core.vnom * VSF_MAX, core.vmax)
            s_speedup = 1
            _debug(_bm_('s_speedup: {0}', s_speedup))

            perf += kcov * ((1-kobj.pf + kobj.pf/p_speedup))
            cov -= kcov

        # non-kernels will not be speedup
        perf += cov

        abs_perf = core.perfnom / perf  # speedup = 1 / perf
        return abs_perf
