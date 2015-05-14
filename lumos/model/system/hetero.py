#!/usr/bin/env python

import logging
from .budget import Sys_L
from .. import tech as techmodel
from .. import core
from ..core.io_cmos import PERF_BASE
# from ..ucore import UCore
from ..acc import ASAcc, RLAcc
from lumos import settings

VMIN = 300
VMAX = 1100
VSF_MAX = 1.3  # maxium vdd is 1.3 * vdd_nominal
V_PRECISION = 1  # 1mV


_logger = logging.getLogger('HeterogSys')
if settings.LUMOS_DEBUG:
    _logger.setLevel(logging.DEBUG)
else:
    _logger.setLevel(logging.INFO)


class SysConfig():
    def __init__(self):
        self.tech = 16
        self.budget = Sys_L

        self.serial_core_type = None
        self.serial_core_tech_variant = 'hp'
        self.thru_core_as_serial = True
        self.thru_core_type = 'io-cmos'
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
    def __init__(self, sysconfig, kernels):
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

        CoreClass = core.get_coreclass(sysconfig.thru_core_type)
        self.thru_core = CoreClass(self.tech, sysconfig.thru_core_tech_variant)

        if not sysconfig.thru_core_as_serial:
            CoreClass = core.get_coreclass(sysconfig.serial_core_type)
            self.serial_core = CoreClass(self.tech, sysconfig.serial_core_tech_variant)
            available_area -= self.serial_core.area
        else:
            self.serial_core = self.thru_core

        self.thru_core_area = available_area
        self.thru_core_num = int(self.thru_core_area / self.thru_core.area)

        self.thru_core_power = self.sys_power
        ret = self._dim_perf_opt()
        self.dim_perf = ret['perf']
        self.opt_cnum = ret['cnum']
        self.opt_vdd = ret['vdd']

        _logger.debug('Serial core: {0}, area: {1}'.format(
            self.serial_core.ctype, self.serial_core.area))
        _logger.debug('thru core: {0}, area: {1}, cnum: {2}'.format(
            self.thru_core.ctype, self.thru_core.area, self.thru_core_num))

    def has_asacc(self, kid):
        if kid in self.asic_dict:
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
            _logger.debug('Optimal Vdd for thru_core: {0}mV'.format(vr))
            return {'perf': rperf / PERF_BASE,
                    'vdd': vr,
                    'cnum': cnum,
                    'util': float(100 * cnum) / float(cnum_max)}

        else:
            core.vd = vl
            lperf = cnum * core.perf_by_vdd(vl)
            _logger.debug('Optimal Vdd for thru_core: {0}mV'.format(vr))
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

        serial_core.vdd = min(serial_core.vnom * VSF_MAX, serial_core.vmax)
        serial_perf = serial_core.perf_by_vdd(serial_core.vnom) / PERF_BASE

        dim_perf = self.dim_perf
        perf = (1 - app.f) / serial_perf + app.f_noacc / dim_perf

        for kid in app.get_all_kernels():
            cov = app.get_cov(kid)
            if self.use_rlacc:
                if self.has_asacc(kid):
                    asacc = self.get_asacc_list(kid)[0]
                    perf = perf + cov / (asacc.perf(
                        power=self.sys_power, bandwidth=self.sys_bandwidth) / PERF_BASE)
                else:
                    perf = perf + cov / (rlacc.perf(
                        app.get_kernel(kid), power=self.sys_power, bandwidth=self.sys_bandwidth) / PERF_BASE)
            else:
                if self.has_asacc(kid):
                    asacc = self.get_asacc_list(kid)[0]
                    perf = perf + cov / (asacc.perf(
                        power=self.sys_power, bandwidth=self.sys_bandwidth) / PERF_BASE)
                else:
                    perf = perf + cov / dim_perf

        return {'perf': 1 / perf,
                'cnum': self.opt_cnum,
                'vdd': self.opt_vdd}
