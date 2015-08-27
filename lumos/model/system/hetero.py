#!/usr/bin/env python

import logging
from .budget import Sys_L
from .. import tech as techmodel
from ..core import BaseCore
# from ..core.io_cmos import PERF_BASE
PERF_BASE = 12.92
# from ..ucore import UCore
from ..acc import ASAcc, RLAcc
from lumos.model import mem
from lumos.model.mem.cache import get_cache_trait
from lumos import settings

VMIN = 300
VMAX = 1100
VSF_MAX = 1.3  # maxium vdd is 1.3 * vdd_nominal
V_PRECISION = 1  # 1mV


_logger = logging.getLogger('HeterogSys')
_logger.setLevel(logging.INFO)
debug_tag = settings.LUMOS_DEBUG
if debug_tag:
    if 'all' in debug_tag or 'heterogsys' in debug_tag:
        _logger.setLevel(logging.DEBUG)


class HeterogSysError(Exception):
    pass


class SysConfig():
    def __init__(self):
        self.tech = 22
        self.budget = Sys_L

        self.serial_core_type = None
        self.serial_core_tech_variant = 'hp'
        self.thru_core_as_serial = True
        self.thru_core_type = 'io'
        self.thru_core_tech_name = 'cmos'
        self.thru_core_tech_variant = 'hp'

        self.asacc_tech_model = 'cmos'
        self.asacc_tech_variant = 'hp'
        # asacc_config = {(ker_id, acc_id): (area_ratio, tech_model)}
        self.asacc_config = dict()

        self.rlacc_tech_model = 'cmos'
        self.rlacc_tech_variant = 'hp'
        self.rlacc_id = 'fpga'
        self.rlacc_area_ratio = 0

    def add_asacc(self, ker_id, acc_id, area_ratio):
        self.asacc_config[(ker_id, acc_id)] = area_ratio


class HeterogSys():
    """
    This class models a heterogeneous many core system composed of
    regular cores and accelerators such as dedicated ASICs,
    reconfigurable logic (FPGA), and GPGPUs. composed by regular
    cores, accelerators such as ASICs, FPGA, and GPU.

    Args:
       budget (:class:`~lumos.model.budget.Budget`):
          The budget of the system (area and power). Possible values are
          :class:`~lumos.model.budget.SysSmall`,
          :class:`~lumos.model.budget.SysMedium`, and
          :class:`~lumos.model.budget.SysLarge`.
       tech (num):
          Technology node of the system, possible values are 45, 32, 22, 16.
       serial_core (core):
          The core for serial part of the program. It could be
          :class:`~lumos.model.core.IOCore`,
          :class:`~lumos.model.core.O3Core`, or
          :class:`~lumos.model.fedcore.FedCore`.

    """
    def __init__(self, sysconfig, kernels, _dimperf_preprocessed=True):
        self.sys_area = sysconfig.budget.area
        self.sys_power = sysconfig.budget.power
        self.sys_bw = sysconfig.budget.bw

        self.tech = sysconfig.tech
        self.sys_bandwidth = self.sys_bw[self.tech]

        available_area = self.sys_area
        self.asic_dict = dict()
        asacc_techmodel = techmodel.get_model(sysconfig.asacc_tech_model,
                                              sysconfig.asacc_tech_variant)
        for (key_, area_ratio) in sysconfig.asacc_config.items():
            ker_id, acc_id = key_
            ko = kernels[ker_id]
            asacc_area = self.sys_area * area_ratio
            asacc = ASAcc(acc_id, ko, asacc_area, self.tech, asacc_techmodel)
            if ker_id not in self.asic_dict:
                self.asic_dict[ker_id] = dict()
            self.asic_dict[ker_id][acc_id] = asacc
            available_area -= asacc_area

        if sysconfig.rlacc_area_ratio:
            self.use_rlacc = True
            rlacc_area = sysconfig.rlacc_area_ratio * self.sys_area
            rlacc_techmodel = techmodel.get_model(sysconfig.rlacc_tech_model,
                                                  sysconfig.rlacc_tech_variant)
            self.rlacc = RLAcc(sysconfig.rlacc_id, rlacc_area, self.tech, rlacc_techmodel)
            available_area -= rlacc_area
        else:
            self.use_rlacc = False
            self.rlacc = None

        self.thru_core = BaseCore(sysconfig.tech, sysconfig.thru_core_tech_name,
                                  sysconfig.thru_core_tech_variant, sysconfig.thru_core_type)

        if not sysconfig.thru_core_as_serial:
            CoreClass = core.get_coreclass(sysconfig.serial_core_type)
            self.serial_core = CoreClass(self.tech, sysconfig.serial_core_tech_variant)
            available_area -= self.serial_core.area
        else:
            self.serial_core = self.thru_core

        self.thru_core_area = available_area
        self.thru_core_num = int(self.thru_core_area / self.thru_core.area)

        self.thru_core_power = self.sys_power
        if _dimperf_preprocessed:
            ret = self._dim_perf_opt()
            self.dim_perf = ret['perf']
            self.opt_cnum = ret['cnum']
            self.opt_vdd = ret['vdd']
        else:
            self.dim_perf = None
            self.opt_cnum = None
            self.opt_vdd = None

        _logger.debug('Serial core: {0}, area: {1}'.format(
            self.serial_core.ctype, self.serial_core.area))
        _logger.debug('thru core: {0}, area: {1}, cnum: {2}'.format(
            self.thru_core.ctype, self.thru_core.area, self.thru_core_num))

    def has_asacc(self, kid):
        if kid in self.asic_dict:
            return True
        else:
            return False

    def has_rlacc(self):
        if self.rlacc:
            return True
        else:
            return False

    def get_asacc_list(self, kid):
        try:
            asacc_dict = self.asic_dict[kid]
        except KeyError:
            return None

        return [asacc for asacc in asacc_dict.values()]

    def _dim_perf_cnum(self, cnum, vmin=VMIN):
        """Get the performance of Dim silicon with given active number of cores

        :cnum: @todo
        :app: @todo
        :returns: @todo

        """
        core = self.thru_core

        cnum_max = int(self.thru_core_area / core.area)

        if cnum > cnum_max or cnum < 0:
            return None

        cpower = self.thru_core_power / float(cnum)
        VMIN = core.vmin
        VMAX = core.vmax

        if vmin > VMIN:
            if core.power(vmin) > cpower:
                active_cnum = min(int(self.thru_core_area / core.area),
                                  int(self.core_power / core.power(vmin)))

                perf = active_cnum * core.perf_by_vdd(vmin)
                return {'perf': perf / PERF_BASE,
                        'vdd': vmin,
                        'cnum': active_cnum,
                        'util': float(100 * active_cnum) / float(cnum_max)}
        else:
            vmin = VMIN

        vl = vmin
        vr = min(core.vnom * VSF_MAX, core.vmax)
        vm = int((vl + vr) / 2)

        while (vr - vl) > V_PRECISION:
            vm = int((vl + vr) / 2)
            if core.power(vm) > cpower:
                vl = vl
                vr = vm
            else:
                vl = vm
                vr = vr

        rpower = core.power(vr)

        if rpower <= cpower:
            rperf = cnum * core.perf_by_vdd(vr)
            _logger.debug('_dim_perf_cnum: optimal vdd for {0} thru_cores: {1}mV'.format(cnum, vr))
            return {'perf': rperf / PERF_BASE,
                    'vdd': vr,
                    'cnum': cnum,
                    'util': float(100 * cnum) / float(cnum_max)}

        else:
            core.vd = vl
            lperf = cnum * core.perf_by_vdd(vl)
            _logger.debug('_dim_perf_cnum: optimal vdd for {0} thru_core: {1}mV'.format(cnum, vr))
            return {'perf': lperf / PERF_BASE,
                    'vdd': vl,
                    'cnum': cnum,
                    'util': float(100 * cnum) / float(cnum_max)}

    def _dim_perf_opt(self):
        """Get the performance of Dim silicon subsystem

        :returns: @todo

        """
        core = self.thru_core
        cnum_max = int(self.thru_core_area / core.area)
        cnum_list = range(1, cnum_max + 1)

        _logger.debug('_dim_perf_opt: thru_core_area: {0}, core area: {1}, cnum_max: {2}'.format(
            self.thru_core_area, core.area, cnum_max))
        perf = 0
        for cnum in cnum_list:
            r = self._dim_perf_cnum(cnum)
            if r['cnum'] < cnum:
                break
            if r['perf'] > perf:
                perf = r['perf']
                vdd = r['vdd']
                util = r['util']
                opt_cnum = cnum

        return {'cnum': opt_cnum,
                'vdd': vdd,
                'util': util,
                'perf': perf}

    def _calc_dim_perf(self, thru_core_power=None):
        if thru_core_power:
            self.thru_core_power = thru_core_power
        else:
            self.thru_core_power = self.sys_power

        ret = self._dim_perf_opt()

        self.dim_perf = ret['perf']
        self.opt_cnum = ret['cnum']
        self.opt_vdd = ret['vdd']

    def get_perf(self, app):
        """ Get the optimal performance fo the system. It uses accelerators to execute
        kernels if available. Otherwise, kernels are executed and accelerated by
        throughput cores. The system will try to find the optimal number of throughput
        cores to be active to achieve the best overall throughput.

        Parameters
        ----------
        app: :class:`~lumos.model.application.SimpleApplication`
           The targeted application.

        Returns
        -------
        dict: results wrapped in a python dict with three keys:

        perf :float
          Relative performance, also should be the optimal with the given
          system configuration.
        cnum :int
          The number of active cores for the optimal configuration.
        vdd :float
          The supply voltage of throughput cores when executing parallel part
          of the application.

        For example, a results dict::

          {
            'perf': 123.4,
            'cnum': 12,
            'vdd': 800,
          }
        """
        _logger.debug('Get perf on app {0}'.format(app.name))
        serial_core = self.serial_core
        rlacc = self.rlacc

        serial_perf = serial_core.perf_by_vdd(serial_core.vmax) / PERF_BASE
        _logger.debug('serial_perf: {0}'.format(serial_perf))

        dim_perf = self.dim_perf
        if not dim_perf:
            raise HeterogSysError('dim_perf not initialized properly')
        perf = (1 - app.f) / serial_perf + app.f_noacc / dim_perf
        _logger.debug('dim_perf: {0}'.format(dim_perf))

        _logger.debug('perf: {0}'.format(perf))
        for kid in app.get_all_kernels():
            cov = app.get_cov(kid)
            _logger.debug('get_perf: kernel {0}, cov {1}'.format(kid, cov))
            if self.has_asacc(kid):
                asacc = self.get_asacc_list(kid)[0]
                asacc_perf = asacc.perf(
                    power=self.sys_power, bandwidth=self.sys_bandwidth) / PERF_BASE
                perf = perf + cov / asacc_perf
                _logger.debug('get_perf: ASAcc perf: {0}'.format(asacc_perf))
            elif self.use_rlacc:
                rlacc_perf = rlacc.perf(
                    app.get_kernel(kid), power=self.sys_power, bandwidth=self.sys_bandwidth) / PERF_BASE
                perf = perf + cov / rlacc_perf
                _logger.debug('get_perf: RLAcc perf: {0}'.format(rlacc_perf))
            else:
                perf = perf + cov / dim_perf

        return {'perf': 1 / perf,
                'cnum': self.opt_cnum,
                'vdd': self.opt_vdd}

class SysConfigDetailed():
    def __init__(self):
        self.tech = 22
        self.budget = Sys_L

        self.serial_core_type = None
        self.serial_core_tech_variant = 'hp'
        self.thru_core_as_serial = True
        self.thru_core_type = 'io'
        self.thru_core_tech_name = 'cmos'
        self.thru_core_tech_variant = 'hp'

        self.asacc_tech_model = 'cmos'
        self.asacc_tech_variant = 'hp'
        # asacc_config = {(ker_id, acc_id): (area_ratio, tech_model)}
        self.asacc_config = dict()

        self.rlacc_tech_model = 'cmos'
        self.rlacc_tech_variant = 'hp'
        self.rlacc_id = 'fpga'
        self.rlacc_area_ratio = 0

        if not self.thru_core_as_serial:
            raise Exception('SysConfigDetailed requires thru_core_as_serial')

        self.l2_tech_name = mem.BASELINE_L2_TECH_NAME
        self.l2_tech_variant = mem.BASELINE_L2_TECH_VARIANT
        self.delay_mem = mem.BASELINE_L2_DELAY
        self.cache_sz_l1 = mem.BASELINE_L1_SIZE
        self.cache_sz_l2 = mem.BASELINE_L2_SIZE

    def add_asacc(self, ker_id, acc_id, area_ratio, tech_name='cmos', tech_variant='hp'):
        self.asacc_config[(ker_id, acc_id)] = (area_ratio, tech_name, tech_variant)

    @property
    def l1_tech_name(self):
        return self.thru_core_tech_name

    @property
    def l1_tech_variant(self):
        return self.thru_core_tech_variant

class HeterogSysDetailed(HeterogSys):
    def __init__(self, sysconfig, kernels):
        self.sys_area = sysconfig.budget.area
        self.sys_power = sysconfig.budget.power
        self.sys_bw = sysconfig.budget.bw

        self.tech = sysconfig.tech
        self.sys_bandwidth = self.sys_bw[self.tech]

        available_area = self.sys_area
        self.asic_dict = dict()
        for (key_, value_) in sysconfig.asacc_config.items():
            ker_id, acc_id = key_
            area_ratio, tech_name, tech_variant = value_
            asacc_techmodel = techmodel.get_model(tech_name, tech_variant)
            ko = kernels[ker_id]
            asacc_area = self.sys_area * area_ratio
            asacc = ASAcc(acc_id, ko, asacc_area, self.tech, asacc_techmodel)
            if ker_id not in self.asic_dict:
                self.asic_dict[ker_id] = dict()
            self.asic_dict[ker_id][acc_id] = asacc
            available_area -= asacc_area

        if sysconfig.rlacc_area_ratio:
            self.use_rlacc = True
            rlacc_area = sysconfig.rlacc_area_ratio * self.sys_area
            rlacc_techmodel = techmodel.get_model(sysconfig.rlacc_tech_model,
                                                  sysconfig.rlacc_tech_variant)
            self.rlacc = RLAcc(sysconfig.rlacc_id, rlacc_area, self.tech, rlacc_techmodel)
            available_area -= rlacc_area
        else:
            self.use_rlacc = False
            self.rlacc = None

        self.thru_core = BaseCore(sysconfig.tech, sysconfig.thru_core_tech_name,
                                  sysconfig.thru_core_tech_variant, sysconfig.thru_core_type)

        if not sysconfig.thru_core_as_serial:
            raise Exception('SysConfigDetailed requires thru_core_as_serial')

        self.serial_core = self.thru_core

        self.thru_core_area = available_area
        self.thru_core_num = int(self.thru_core_area / self.thru_core.area)

        # assume every functional units (cores, accelerators) are power-gated,
        # therefore consume no power if not activated.
        self.thru_core_power = self.sys_power

        baseline_cache_tech = '-'.join((mem.BASELINE_L1_TECH_NAME, mem.BASELINE_L1_TECH_VARIANT))
        baseline_traits = get_cache_trait(mem.BASELINE_L1_SIZE,
                                          baseline_cache_tech,
                                          mem.BASELINE_L1_TECH_NODE)

        self.cache_sz_l1 = sysconfig.cache_sz_l1
        l1_tech_type = '-'.join([sysconfig.l1_tech_name, sysconfig.l1_tech_variant] )
        self.l1_traits = get_cache_trait(self.cache_sz_l1, l1_tech_type, sysconfig.tech)

        scale_factor = self.l1_traits['latency'] / baseline_traits['latency']
        self.delay_l1 = int(mem.BASELINE_L1_DELAY * scale_factor)

        baseline_cache_tech = '-'.join((mem.BASELINE_L2_TECH_NAME, mem.BASELINE_L2_TECH_VARIANT))
        baseline_traits = get_cache_trait(mem.BASELINE_L2_SIZE,
                                          baseline_cache_tech,
                                          mem.BASELINE_L2_TECH_NODE)
        self.cache_sz_l2 = sysconfig.cache_sz_l2
        l2_tech_type = '-'.join([sysconfig.l2_tech_name, sysconfig.l2_tech_variant])
        self.l2_traits = get_cache_trait(self.cache_sz_l2, l2_tech_type, sysconfig.tech)

        scale_factor = self.l2_traits['latency'] / baseline_traits['latency']
        self.delay_l2 = int(mem.BASELINE_L2_DELAY * scale_factor)
        _logger.debug('l2 cache tech: {0}, latency: {1}'.format(l2_tech_type, self.delay_l2))

        self.delay_mem = sysconfig.delay_mem

    def get_cnum(self, vdd):
        core = self.thru_core
        core_power = core.power(vdd)
        l2_power = self.l2_traits['power']
        l2_area = self.l2_traits['area']
        l1_power = self.l1_traits['power']
        l1_area = self.l1_traits['area']
        cnum = min((self.sys_power-l2_power)/(core_power+l1_power),
                   (self.thru_core_area-l2_area)/(core.area+l1_area))
        return int(cnum)

    def perf(self, vdd, app, cnum=None, disable_rlacc=False, disable_asacc=False):
        """ Get the optimal performance fo the system. It uses accelerators to execute
        kernels if available. Otherwise, kernels are executed and accelerated by
        throughput cores. The system will try to find the optimal number of throughput
        cores to be active to achieve the best overall throughput.

        Parameters
        ----------
        vdd : int, in mV
          the supply of throughput cores
        app: :class:`~lumos.model.application.SimpleApplication`
          The targeted application.
        cnum : int
          the number of throughput cores, if None, the number of throughput
          cores will be determined by system power/area budget. It is None by
          default.
        disable_rlacc: boolean, optional
          Do not use RL accelerator even though it is available in the system.
          Default is False, which will use RL accelerator by default.
        disable_asacc: boolean, optional
          Do not use ASIC accelerator even if it is available. By default, it is
          False, and will try to use ASIC accelerator if available.

        Returns
        -------
        perf :float
          Relative performance, also should be the optimal with the given
          system configuration.
        """
        if app.type != 'synthetic':
            raise HeterogSysError('Requires a synthetic application')

        _logger.debug('Get perf on app {0}'.format(app.name))
        serial_core = self.serial_core
        rlacc = self.rlacc

        # vdd_max = min(serial_core.vnom * VSF_MAX, core.vmax)
        # s_speedup = serial_core.perf_by_vdd(vdd_max) / PERF_BASE
        s_speedup = 1
        _logger.debug('serial_perf: {0}'.format(s_speedup))

        if not cnum:
            cnum = self.get_cnum(vdd)

        core = self.thru_core

        # @TODO: how to deal with accelerator's performance?
        # perf = (1 - app.f) / s_speedup + app.f_noacc / p_speedup
        # _logger.debug('perf: {0}'.format(perf))
        cov, speedup = 1, 0
        for kid in app.get_all_kernels():
            kcov = app.get_cov(kid)
            kobj = app.get_kernel(kid)
            _logger.debug('get_perf: kernel {0}, cov {1}'.format(kid, kcov))
            if not disable_asacc and self.has_asacc(kid):
                asacc = self.get_asacc_list(kid)[0]
                asacc_perf = asacc.perf(power=self.sys_power, bandwidth=self.sys_bandwidth)
                asacc_speedup = asacc_perf / core.perfnom
                speedup += kcov / asacc_speedup
                _logger.debug('get_perf: ASAcc perf: {0}'.format(asacc_perf))
            elif not disable_rlacc and self.has_rlacc() and kobj.accelerated_by('fpga'):
                rlacc_perf = rlacc.perf(kobj, power=self.sys_power, bandwidth=self.sys_bandwidth)
                rlacc_speedup = rlacc_perf / core.perfnom
                speedup += kcov / rlacc_speedup
                _logger.debug('get_perf: RLAcc perf: {0}'.format(rlacc_perf))
            else:
                miss_l1 = min(
                    1, kobj.miss_l1 * ((self.cache_sz_l1/(kobj.cache_sz_l1_nom)) ** (1-kobj.alpha_l1)))
                miss_l2 = min(
                    1, kobj.miss_l2 * ((self.cache_sz_l2/(cnum*kobj.cache_sz_l2_nom)) ** (1-kobj.alpha_l2)))

                _logger.debug('l1_miss: {0}, l2_miss: {1}'.format(miss_l1, miss_l2))
                t0 = ((1-miss_l1)*self.delay_l1 + miss_l1*(1-miss_l2)*self.delay_l2 +
                      miss_l1*miss_l2*self.delay_mem)
                t = t0 * core.freq(vdd) / core.freq(core.vnom)
                _logger.debug('t: {0}'.format(t))
                eta = 1 / (1 + t * kobj.rm / kobj.cpi_exe)
                eta0 = 1 / (1 + t0 * kobj.rm / kobj.cpi_exe)
                _logger.debug('eta: {0}, eta0: {1}'.format(eta, eta0))
                _logger.debug('freq: {0}, freq0: {1}'.format(core.freq(vdd), core.fnom))
                _logger.debug('vdd: {0}, v0: {1}'.format(vdd, core.vnom))
                p_speedup = (core.freq(vdd)/core.fnom) * cnum * (eta/eta0)
                _logger.debug('p_speedup: {0}'.format(p_speedup))

                vdd_max = min(core.vnom * VSF_MAX, core.vmax)
                s_speedup = 1
                _logger.debug('s_speedup: {0}'.format(s_speedup))

                speedup += kcov * ((1-kobj.pf + kobj.pf/p_speedup))
            cov -= kcov
            _logger.debug('get_perf: speedup {0}'.format(speedup))

        # non-kernels will not be speedup/accelerated
        speedup += cov
        _logger.debug('non-kernel: {0}'.format(cov))
        perf = core.perfnom / speedup
        return perf
