#!/usr/bin/env python

import logging
from ..core import IOCore_CMOS as IOCore, O3Core_CMOS as O3Core
from ..core.io_cmos import PERF_BASE
from ..ucore import UCore
from ..application import App

VMIN = 300
VMAX = 1100
VSF_MAX = 1.3  # maxium vdd is 1.3 * vdd_nominal
V_PRECISION = 1  # 1mV


from lumos import settings
_logger = logging.getLogger('HeterogSys')
if settings.DEBUG:
    _logger.setLevel(logging.DEBUG)
else:
    _logger.setLevel(logging.INFO)

class HeterogSys(object):
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
    def __init__(self, budget, tech, serial_core=None, tput_core=None):
        self.sys_area = budget.area
        self.sys_power = budget.power
        self.sys_bw = budget.bw

        self.tech = tech
        self.sys_bandwidth = self.sys_bw[tech]

        self.asic_dict = {}
        self.gp_acc = UCore('fpga')
        self.use_gpacc = False

        if tput_core:
            self.thru_core = tput_core
        else:
            self.thru_core = IOCore(tech=tech, model_name='hp')

        self.dim_perf = None

        if serial_core:
            self.serial_core = serial_core
            self.thru_core_area = self.sys_area - serial_core.area
        else:
            self.serial_core = IOCore(tech=tech, model_name='hp')
            self.thru_core_area = self.sys_area

        _logger.debug('Serial core: {0}, area: {1}'.format(self.serial_core.ctype, self.serial_core.area))
        thru_cnum = int(self.thru_core_area / self.thru_core.area)
        _logger.debug('Tput core: {0}, area: {1}, cnum: {2}'.format(self.thru_core.ctype, self.thru_core.area, thru_cnum))

    def set_asic(self, kid, area_ratio):
        """
        Set the ASIC accelerator's area

        Args:
           kid (str):
              The ID of the kernel that the ASIC is targeted for.
           area_ratio (num):
              The new area ratio of the ASIC to be set.

        Returns:
           Bool to indicate whether successfully set the area.
        """
        area = self.sys_area * area_ratio

        if kid not in self.asic_dict:
            if self.thru_core_area < area:
                logging.error('not enough area for this ASIC %s' % kid)
                return False
            self.thru_core_area = self.thru_core_area - area
            self.asic_dict[kid] = UCore(uid='asic{0}'.format(kid), area=area, tech=self.tech)

            self.dim_perf = None # need to update dim_perf later
            return True
        else:
            asic_core = self.asic_dict[kid]

            if self.thru_core_area + asic_core.area < area:
                logging.error('not enough area for this ASIC %s' % kid)
                return False

            self.thru_core_area = self.thru_core_area + asic_core.area - area
            asic_core.config(area=area)

            self.dim_perf = None # need to update dim_perf later
            return True


    def del_asic(self, kid):
        """
        Remove an ASIC accelerator from the system, free its area to other
        computing components. By default, the freed area is allocated to
        throughput cores.

        Args:
           kid (str):
              The ID of kernel which the ASIC is targeted for.

        Returns:
           Bool indicating successful deletion
        """
        if kid not in self.asic_dict:
            logging.error('kernel %s has not been registered' % kid)
            return False

        asic_core = self.asic_dict[kid]
        self.thru_core_area = self.thru_core_area + asic_core.area

        del self.asic_dict[kid]

        self.dim_perf = None # need ot update dim_perf later
        return True

    def del_asics(self):
        """
        Remove all ASIC accelerators in the system.
        """
        for kid in self.asic_dict.keys():
            self.del_asic(kid)

    def realloc_gpacc(self, area_ratio):
        """
        Adjust the area of a general-purpose accelerator. Currently, only FPGA
        is supported.

        Args:
           area_ratio (num):
              The new area to be adjusted

        Returns:
           Bool indicating a successful update.

        """
        area = self.sys_area * area_ratio
        if self.thru_core_area + self.gp_acc.area < area:
            logging.error('not enough area for this GP accelerator')
            return False

        self.thru_core_area = self.thru_core_area + self.gp_acc.area - area
        self.gp_acc.config(area=area, tech=self.tech)

        self.dim_perf = None # need to update dim_perf later
        return True

    def set_tech(self, tech):
        """
        Set the technology node of all cores and ucores.

        Args:
           tech (num):
              The technology node.

        Returns:
           N/A
        """
        self.thru_core.config(tech=tech)
        self.serial_core.config(tech=tech)
        self.gp_acc.config(tech=tech)

        for k in self.asic_dict:
            self.asic_dict[k].config(tech=tech)

        self.tech = tech
        self.sys_bandwidth = self.sys_bw[tech]

        self.dim_perf = None # need to update dim_perf later


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
            core.vdd = vmin
            if core.power > cpower:
                active_cnum = min(int(self.thru_core_area / core.area),
                                  int(self.core_power / core.power))

                perf = active_cnum * core.perf
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
            core.vdd = vm

            if core.power > cpower:
                vl = vl
                vr = vm
            else:
                vl = vm
                vr = vr

        core.vdd = vr
        rpower = core.power

        if rpower <= cpower:
            rperf = cnum * core.perf
            _logger.debug('Optimal Vdd for tput_core: {0}mV'.format(vr))
            return {'perf': rperf / PERF_BASE,
                    'vdd': vr,
                    'cnum': cnum,
                    'util': float(100 * cnum) / float(cnum_max)}

        else:
            core.vd = vl
            lperf = cnum * core.perf
            _logger.debug('Optimal Vdd for tput_core: {0}mV'.format(vr))
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
        """
        Get the optimal performance fo the system. It uses accelerators to execute
        kernels if available. Otherwise, kernels are executed and accelerated by
        throughput cores. The system will try to find the optimal number of throughput
        cores to be active to achieve the best overall throughput.

        Args:
           app (:class:`~lumos.model.application.App`):
              The targeted application.

        Returns:
           perf (num):
              Relative performance, also should be the optimal with the given
              system configuration.
           cnum (num):
              The number of active cores for the optimal configuration.
           vdd (num):
              The supply voltage of throughput cores when executing parallel part
              of the application.

        """
        #thru_core = self.thru_core
        serial_core = self.serial_core
        gp_acc = self.gp_acc

        asics = self.asic_dict

        serial_core.vdd = min(serial_core.vnom * VSF_MAX, serial_core.vmax)
        serial_perf = serial_core.perf / PERF_BASE

        if not self.dim_perf:
            # need to update dim_perf
            self.thru_core_power = self.sys_power
            ret = self._dim_perf_opt()
            self.dim_perf = ret['perf']
            self.opt_cnum = ret['cnum']
            self.opt_vdd = ret['vdd']

        dim_perf = self.dim_perf
        perf = (1 - app.f) / serial_perf + app.f_noacc / dim_perf

        for kernel in app.kernels:
            if self.use_gpacc:
                if kernel in asics:
                    acc = asics[kernel]
                else:
                    acc = None

                if acc and acc.area > 0:
                    perf = perf + app.kernels[kernel] / (acc.perf(power=self.sys_power, bandwidth=self.sys_bandwidth) / PERF_BASE)
                else:
                    perf = perf + app.kernels[kernel] / (gp_acc.perf(kernel, power=self.sys_power, bandwidth=self.sys_bandwidth) / PERF_BASE)
            else:
                if kernel in asics:
                    acc = asics[kernel]
                else:
                    acc = None

                if acc and acc.area > 0:
                    perf = perf + app.kernels[kernel] / (acc.perf(kernel, power=self.sys_power, bandwidth=self.sys_bandwidth) / PERF_BASE)
                else:
                    perf = perf + app.kernels[kernel] / dim_perf

        return {'perf': 1 / perf,
                'cnum': self.opt_cnum,
                'vdd': self.opt_vdd}





