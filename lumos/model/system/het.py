#!/usr/bin/env python

import logging
from ..core import IOCore_CMOS as IOCore, O3Core_CMOS as O3Core
from ..core.io_cmos import PERF_BASE
from ..ucore import UCore, AppAccelerator, GPAccelerator
from ..application import Application

V_PRECISION = 1  # 1mV

from lumos import settings
_logger = logging.getLogger('HetSys')
if settings.DEBUG:
    _logger.setLevel(logging.DEBUG)
else:
    _logger.setLevel(logging.INFO)

class HetSys(object):
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

        self.asic_dict = dict() # stores all ASIC Ucore object, indexed by uid
        self.kernel_asic_table = dict() # An index table storing supported ASIC Ucores for a kernel. Indexed by kid, each entry is a list of uids that support the corresponding kernel.
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

        _logger.debug('Serial core: {0}, area: {1}'.format(
            self.serial_core.ctype, self.serial_core.area))
        thru_cnum = int(self.thru_core_area / self.thru_core.area)
        _logger.debug('Tput core: {0}, area: {1}, cnum: {2}'.format(
            self.thru_core.ctype, self.thru_core.area, thru_cnum))

    def set_asic(self, ker_obj, aid, area_ratio):
        """
        Set the ASIC accelerator's area

        Args:
           ker_obj (class Kernel):
              The kernel object that the ASIC is targeted for.
           aid (str):
              The ID of the acceleartor.
           area_ratio (num):
              The new area ratio of the ASIC to be set.

        Returns:
           Bool to indicate whether successfully set the area.

        """
        area = self.sys_area * area_ratio
        kid = ker_obj.kid

        if aid not in self.asic_dict:
            # add a new ASIC accelerator
            if self.thru_core_area < area:
                _logger.error('not enough area for this ASIC %s' % kid)
                return False
            self.thru_core_area = self.thru_core_area - area
            asic_ucore = AppAccelerator(uid=aid, ker_obj=ker_obj, area=area, tech=self.tech)
            self.asic_dict[aid] = asic_ucore
            if kid not in self.kernel_asic_table:
                self.kernel_asic_table[kid] = [aid, ]
            else:
                self.kernel_asic_table[kid].append(aid)

        else:
            asic_core = self.asic_dict[aid]

            if self.thru_core_area + asic_core.area < area:
                _logger.error('not enough area for this ASIC %s' % kid)
                return False

            self.thru_core_area = self.thru_core_area + asic_core.area - area
            asic_core.config(area=area)

        self.dim_perf = None  # need to update dim_perf later
        return True


    def del_asic(self, aid):
        """
        Remove an ASIC accelerator from the system, free its area to other
        computing components. By default, the freed area is allocated to
        throughput cores.

        Args:
           aid (str):
              The ID of the ASIC to be removed

        Returns:
           Bool indicating successful deletion
        """
        if aid not in self.asic_dict:
            _logger.error('kernel %s has not been registered' % aid)
            return False

        asic_core = self.asic_dict[aid]

        # reclaim the area allocated to the ASIC to throughput cores
        self.thru_core_area = self.thru_core_area + asic_core.area

        del self.asic_dict[aid]
        self.kernel_asic_table[asic_core.kid].remove(aid)

        self.dim_perf = None # need ot update dim_perf later
        return True

    def get_all_asics(self):
        return self.asic_dict.keys()

    def get_target_asics(self, kid):
        if kid not in self.kernel_asic_table:
            return None
        else:
            return self.kernel_asic_table[kid]

    def del_target_asics(self, kid):
        if kid not in self.kernel_asic_table:
            return

        for aid in self.kernel_asic_table[kid]:
            self.del_asic(aid)

        del self.kernel_asic_table[kid]

    def get_supported_kernels(self):
        return self.kernel_asic_table.keys()

    def del_all_asics(self):
        """
        Remove all ASIC accelerators in the system.
        """
        for kid in self.asic_dict:
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
            _logger.error('not enough area for this GP accelerator')
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


    def _dim_perf_cnum(self, cnum, vmin=None):
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

        if not vmin:
            vmin = core.vmin
        elif vmin < core.vim:
            _logger.warning('Provided vmin {0}mV is lower than core.vmin {1}mV. vmin is set to core.vmin'.format(vmin, core.vmin))
            vmin = core.vmin

        # first check whether vmin can meet the power constraint. If not,
        # it is probabaly either due to vmin is too high, or power budget
        # is too constrained.
        core.vdd = vmin
        if core.power > cpower:
            active_cnum = min(int(self.thru_core_area / core.area),
                              int(self.core_power / core.power))

            perf = active_cnum * core.perf
            _logger.warning('Power constraint is not met even at vmin of {0}mV'.format(vmin))
            return {'perf': perf / PERF_BASE,
                    'vdd': vmin,
                    'cnum': active_cnum,
                    'util': float(100 * active_cnum) / float(cnum_max)}

        vl = vmin
        vr = core.vmax
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
        #thru_core = self.thru_core
        serial_core = self.serial_core
        gp_acc = self.gp_acc

        asics = self.asic_dict


        serial_core.vdd = serial_core.vmax
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

        for kid,ker_obj in app.kernels.items():
            if self.use_gpacc:
                if kid in self.kernel_asic_table:
                    aid_list = self.kernel_asic_table[kid]
                    if len(aid_list) > 1:
                        _logger.warning('More than 1 ASIC is available for a single kernel, will default to use the first one in the list, order not guaranteed')
                    aid = aid_list[0]
                    acc = self.asic_dict[aid]
                else:
                    acc = None

                if acc and acc.area > 0:
                    perf = perf + app.kernels_covreage[kid] / (acc.perf(power=self.sys_power, bandwidth=self.sys_bandwidth) / PERF_BASE)
                else:
                    perf = perf + app.kernels[kid] / (gp_acc.perf(ker_obj, power=self.sys_power, bandwidth=self.sys_bandwidth) / PERF_BASE)
            else:
                if kid in self.kernel_asic_table:
                    aid_list = self.kernel_asic_table[kid]
                    if len(aid_list) > 1:
                        _logger.warning('More than 1 ASIC is available for a single kernel, will default to use the first one in the list, order not guaranteed')
                    aid = aid_list[0]
                    acc = self.asic_dict[aid]
                else:
                    acc = None

                if acc and acc.area > 0:
                    perf = perf + app.kernels_coverage[kid] / (acc.perf(power=self.sys_power, bandwidth=self.sys_bandwidth) / PERF_BASE)
                else:
                    perf = perf + app.kernels_coverage[kid] / dim_perf

        return {'perf': 1 / perf,
                'cnum': self.opt_cnum,
                'vdd': self.opt_vdd}





