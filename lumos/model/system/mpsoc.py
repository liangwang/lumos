#!/usr/bin/env python

"""
Multi-core, heterogeneous system-on-chip (MPSoC)
"""

import logging
from ..core import BaseCore
PERF_BASE = 12.92
from ..acc import ASAcc as Accelerator
# from ..application import Application
from lumos import settings
import math


EPSILON = 1e-9   # small number to test float equivalence
V_PRECISION = 1  # 1mV

_logger = logging.getLogger('MPSoC')
if settings.LUMOS_DEBUG:
    _logger.setLevel(logging.DEBUG)
else:
    _logger.setLevel(logging.INFO)


class MPSoCError(Exception):
    pass


class MPSoC():
    """
    This class models a heterogeneous many core system composed of
    regular cores and accelerators such as dedicated ASICs,
    reconfigurable logic (FPGA), and GPGPUs. composed by regular
    cores, accelerators such as ASICs, FPGA, and GPU.

    Parameters
    ----------
    budget : :class:`~lumos.model.Budget`
      The budget of the system (area and power). Possible values are
      :class:`~lumos.model.Sys_S`, :class:`~lumos.model.Sys_M`, and
      :class:`~lumos.model.Sys_L`.
    tech : int
      Technology node of the system, possible values are 45, 32, 22, 16.
    serial_core : :class:`~lumos.model.BaseCore`
      The core for serial part of the program. It could be
      :class:`~lumos.model.IOCore`, :class:`~lumos.model.O3Core`, or
      :class:`~lumos.model.FedCore`.
    tput_core : :class:`~lumos.model.BaseCore`
      The core for throughput (parallel) part of the program, similar to
      serial_core

    Attributes
    ----------
    sys_area : float
      system area budget, in mm^2
    sys_pwoer : float
      system power budget, in watt
    sys_bandwidth : float
      memory bandwidth budget of the system, in GB/s
    tech : int
      technology node
    kernel_asic_table : dict
      An index table storing supported ASIC Ucores for a kernel. Indexed by kid,
      each entry is a list of ASIC's IDs (acc_id) that support the corresponding
      kernel.
    asic_dict : dict
      stores all ASIC Ucore object, indexed by ASIC's IDs (acc_id)

    """
    def __init__(self, budget, tech, serial_core=None, tput_core=None):
        self.sys_area = budget.area
        self.sys_power = budget.power
        self._sys_bw = budget.bw

        self.tech = tech
        self.sys_bandwidth = self._sys_bw[tech]

        # asic_dict[kid][acc_id] = Acc_obj
        self.asic_dict = dict()
        # asic_power_dict[kid][acc_id] = (power_max, power_min, power_nom)
        self.asic_power_dict = dict()

        if tput_core:
            self.thru_core = tput_core
        else:
            self.thru_core = BaseCore(tech, 'cmos', 'hp', 'io')

        self.dim_perf = None

        self.serial_core = serial_core
        if serial_core:
            self.thru_core_area = self.sys_area - serial_core.area
            _logger.debug('Serial core: {0}, area: {1}'.format(
                self.serial_core.ctype, self.serial_core.area))
        else:
            self.thru_core_area = self.sys_area

        self.use_gpacc = False

    def add_asic(self, ker_obj, acc_id, area_ratio, tech_model):
        """ Set the ASIC accelerator's area

        Parameters
        ----------
        ker_obj : :class:`~lumos.model.Kernel`
           The kernel object that the ASIC is targeted for.
        acc_id : str
           The ID of the acceleartor.
        area_ratio : float
           The new area ratio of the ASIC to be set.

        Raises
        ------
        MPSoCError
          The ASIC area is larger than available system area

        """
        area = self.sys_area * area_ratio
        kid = ker_obj.name

        if kid not in self.asic_dict:
            # add a new ASIC accelerator
            self.asic_dict[kid] = dict()

        if acc_id not in self.asic_dict[kid]:
            if self.thru_core_area < area:
                raise MPSoCError('not enough area for this ASIC {0}'.format(acc_id))
            self.thru_core_area = self.thru_core_area - area
            asic_ucore = Accelerator(acc_id=acc_id, ker_obj=ker_obj, area=area,
                                     tech=self.tech, tech_model=tech_model)
            self.asic_dict[kid][acc_id] = asic_ucore
        else:
            raise MPSoCError('Accelerator {0} for kernel {1} already exist'.format(
                acc_id, kid))

        # need to update dim_perf later
        self.dim_perf = None

    def del_asic(self, acc_id):
        """ Remove an ASIC accelerator from the system, free its area to other
        computing components. By default, the freed area is allocated to
        throughput cores.

        Parameters
        ----------
        acc_id : str
          The ID of the ASIC to be removed

        Raises
        ------
        MPSoCError
          acc_id is not registered with the system

        """
        raise NotImplementedError()
        if acc_id not in self.asic_dict:
            raise MPSoCError('kernel %s has not been registered' % acc_id)

        asic_core = self.asic_dict[acc_id]

        # reclaim the area allocated to the ASIC to throughput cores
        self.thru_core_area = self.thru_core_area + asic_core.area

        del self.asic_dict[acc_id]
        self.kernel_asic_table[asic_core.kid].remove(acc_id)

        # need to update dim_perf later
        self.dim_perf = None

    def get_all_asics(self):
        """ Get all registered ASIC accelerators

        Returns
        -------
          list
            The names (asic ID) of all registered ASIC accelerators
        """
        return self.asic_dict.keys()

    def get_target_asics(self, kid):
        """ Get all registered ASIC accelerators for a given kernel

        Parameters
        ----------
        kid : str
          The name of the given kernel

        Returns
        -------
          list
            The names (asic IDs) of all registered ASIC accelerator for the given
            kernel. None, if no ASIC support the kernel.

        """
        if kid not in self.kernel_asic_table:
            return None
        else:
            return self.kernel_asic_table[kid]

    def del_target_asics(self, kid):
        """ Delete (unregistered) all ASIC accelerators for a given kernel.

        Currently disabled, should not be used.
        """
        raise NotImplementedError()
        if kid not in self.kernel_asic_table:
            raise MPSoCError('Kernel {0} not registered'.format(kid))

        for acc_id in self.kernel_asic_table[kid]:
            self.del_asic(acc_id)

        del self.kernel_asic_table[kid]

    def get_supported_kernels(self):
        """ Get all kernels that is targeted by at least one ASIC accelerator.

        Returns
        -------
          list
            The names of supported kernels.
        """
        return self.kernel_asic_table.keys()

    def del_all_asics(self):
        """ Remove all ASIC accelerators in the system.
        """
        raise NotImplementedError()
        for kid in self.asic_dict:
            self.del_asic(kid)

    def instantiate(self):
        self._thru_core_num = int(self.thru_core_area / self.thru_core.area)
        _logger.debug('Tput core: {0}, area: {1}, cnum: {2}'.format(
            self.thru_core.ctype, self.thru_core.area, self._thru_core_num))

    def realloc_gpacc(self, area_ratio):
        """ Adjust the area of a general-purpose accelerator.

        Currently, only FPGA is supported.

        Parameters
        ----------
        area_ratio : float
          The new area to be adjusted

        Raises
        ------
        MPSoCError
          area is larger than available system area

        """
        raise NotImplementedError()
        area = self.sys_area * area_ratio
        if self.thru_core_area + self.gp_acc.area < area:
            raise MPSoCError('not enough area for this GP accelerator')

        self.thru_core_area = self.thru_core_area + self.gp_acc.area - area
        self.gp_acc.config(area=area, tech=self.tech)
        # need to update dim_perf later
        self.dim_perf = None

    def set_tech(self, tech):
        """ Set the technology node of all cores and ucores.

        Parameters
        ----------
        tech : num
          The technology node.

        """
        self.thru_core.config(tech=tech)
        if self.serial_core:
            self.serial_core.config(tech=tech)
        if self.gp_acc:
            self.gp_acc.config(tech=tech)

        for k in self.asic_dict:
            self.asic_dict[k].config(tech=tech)

        self.tech = tech
        self.sys_bandwidth = self._sys_bw[tech]

        # need to update dim_perf later
        self.dim_perf = None

    def _dim_perf_cnum(self, cnum, vmin=None, power_budget=None):
        """Get the performance by given the active number of cores.

        Given number of multi-cores (potentially) running at lower supply voltage.

        Parameters
        ----------
        cnum : int
          The number of active cores
        vmin : float, optional
          The minimum voltage of cores
        power_budget : float
          The power budget, if None, system power budget will be used

        Returns
        -------
        perf : float
          The performance score, not relative speedup
        vdd : int
          The supply voltage in mV, when the system achieves the optimal
          throughput
        power : float
          The effective power conumption of dim cores. If it is less than the
          provided power_budget, this usually means the performance is
          constrained by area_budget instead of power_budget
        """
        core = self.thru_core

        if not power_budget:
            power_budget = self.sys_power

        cpower = power_budget / float(cnum)

        if not vmin:
            vmin = core.vmin
        elif vmin < core.vmin:
            _logger.warning('Provided vmin {0}mV is lower than core.vmin {1}mV. '
                            'vmin is set to core.vmin'.format(vmin, core.vmin))
            vmin = core.vmin

        # first check whether vmin can meet the power constraint. If not,
        # it is probabaly either due to vmin is too high, or power budget
        # is too constrained, return None in this case.
        if core.power(vmin) > cpower:
            _logger.warning('Power budget {1:.3g}W is not met even at vmin of {0}mV'.format(
                vmin, power_budget))
            return (0, 0, 0)

        # use binary search to find the highest per-core vdd that stays within the power_budget
        vmax = core.vmax

        while vmax > vmin:
            vmid = math.ceil((vmin+vmax) / 2)
            power_vmid = core.power(vmid)

            if power_vmid > cpower:
                vmax = vmid - 1
            else:
                vmin = vmid

        perf_opt = cnum * core.perf_by_vdd(vmin)
        power_eff = cnum * core.power(vmin)

        return (perf_opt, vmin, power_eff)

    def _dim_perf_opt(self, power_budget=None, cnum_max=None):
        """Get the optimal performance of multicore, subjecting to power and area budget.

        Increasing the number of cores can improve throughput, while a stringent
        system budget (e.g. power and area) may limit the throughput improvement.
        This method finds the optimal throughput-based performance.

        Parameters
        ----------
        power_budget : float
          power budget, if None, system power budget will be used
        cnum_max : int
          maximum core number, if None, system area budget will be used to determine cnum_max

        Returns
        -------
        perf : float
          optimal throughput-based performance
        vdd : int
          supply voltage when achieving the optimal throughput
        cnum : int
          the number of active cores when achieving the optimal throughput
        power_eff : float
          the effective power of throughput cores
        """
        core = self.thru_core
        if not cnum_max:
            cnum_max = int(self.sys_area / core.area)

        _logger.debug('power budget: {0}'.format(power_budget))
        perf_opt, vdd_opt, cnum_opt, power_eff = 0, 0, 0, 0
        for cnum in range(1, cnum_max + 1):
            perf_, vdd_, power_ = self._dim_perf_cnum(cnum, power_budget=power_budget)
            if perf_ == 0:
                # power budget is too small to power such many cores
                break

            if perf_ > perf_opt:
                perf_opt = perf_
                vdd_opt = vdd_
                cnum_opt = cnum
                power_eff = power_
            _logger.debug('cnum: {0}, perf_opt: {1}, power_eff: {2}'.format(
                cnum, perf_opt, power_eff))
        return (perf_opt, vdd_opt, cnum_opt, power_eff)

    # def _calc_dim_perf(self, thru_core_power=None, thru_core_area=None):
    #     # if thru_core_power:
    #     #     self.thru_core_power = thru_core_power
    #     # else:
    #     #     self.thru_core_power = self.sys_power

    #     ret = self._dim_perf_opt(power_budget=thru_core_power, area_budget=thru_core_area)

    #     self.dim_perf = ret['perf']
    #     self.opt_cnum = ret['cnum']
    #     self.opt_vdd = ret['vdd']

    #     """Get the performance of the system, on an :class:`~lumos.model.AppDAG`
    #     application, all kernels are processed in serial.

    #     Parameters
    #     ----------
    #     appdag : :class:`~lumos.model.AppDAG`
    #       The target application

    #     Returns
    #     -------
    #     float
    #       speedup relative to running all kernels at the baseline performance.

    #     """
    #     ker_lengths = appdag.get_all_kernel_lengths()
    #     baseline = sum(ker_lengths)

    #     depth_sorted = appdag.kernels_depth_sort()
    #     finish = 0
    #     for l, node_list in enumerate(depth_sorted):
    #         ker_objs = [appdag.get_kernel(idx_) for idx_ in node_list]
    #         ker_lengths = [appdag.get_kernel_length(idx_) for idx_ in node_list]
    #         length_sum = sum(ker_lengths)
    #         power_budget_percentages = [self.sys_power * l_ / length_sum
    #                                     for l_ in ker_lengths]
    #         runtime = []
    #         for ker_obj, k_idx, pb in zip(
    #                 ker_objs, node_list, power_budget_percentages):
    #             kl = appdag.get_kernel_length(k_idx)
    #             if self.has_asacc(ker_obj.name):
    #                 acc = self.get_asacc(ker_obj.name)
    #                 runtime.append(kl/acc.perf(power=pb))
    #             else:
    #                 ret = self._dim_perf_opt(power_budget=pb)
    #                 if not ret:
    #                     _logger.info("accelerator for {0} has a too constrained"
    #                                  " power budget".format(ker_obj.name))
    #                 self.thru_core.vdd = ret['vdd']
    #                 serial_su = self.thru_core.perf / PERF_BASE
    #                 thru_su = ret['perf']
    #                 runtime.append(kl*(1-ker_obj.pf)/serial_su+kl*ker_obj.pf/thru_su)
    #         _logger.debug('run time: {0}'.format(runtime))
    #         finish += max(runtime)
    #     return baseline / finish

    def get_speedup_appdag_parallel_greedy(self, appdag):
        """Get the performance of the system, on an
        :class:`~lumos.model.AppDAG` application, all kernels are
        processed in parallel, power budget is allocated to accelerators
        in a greedy way.

        The system power budget will be allocated to the kernel that has
        the longest execution time, the power of the accelerator working
        at nominal supply will be deducted from the system budget. Then
        the system will try to allocate the remaining power budget to
        the accelerator targeting the next longest running kernel. Until
        there is no more accelerators can be activate.

        This will assume that all parallel kernels are supported by accelerators.

        Parameters
        ----------
        appdag : :class:`~lumos.model.AppDAG`
          The target application

        Returns
        -------
        float
          speedup relative to running all kernels at the baseline performance.

        """
        ker_lengths = appdag.get_all_kernel_lengths()
        baseline = sum(ker_lengths)

        depth_sorted = appdag.kernels_depth_sort()
        finish = 0
        for l, node_list in enumerate(depth_sorted):
            ker_lengths = [appdag.get_kernel_length(idx_) for idx_ in node_list]
            ker_len_sorted = sorted(zip(ker_lengths, node_list), reverse=True)

            power_budget = self.sys_power
            runtime = []
            for kl, idx_ in ker_len_sorted:
                ko = appdag.get_kernel(idx_)
                _logger.debug('----------{0}----------'.format(ko.name))
                if self.has_asacc(ko.name):
                    asacc = self.get_asacc(ko.name)
                    asacc_su = asacc.perf(power=power_budget) / PERF_BASE
                    power_budget -= asacc.power_eff
                    rt = kl / asacc_su
                    runtime.append(rt)
                    _logger.debug('ASACC runtime: {0}'.format(rt))
                else:
                    perf_, vdd_, cnum_, power_eff = self._dim_perf_opt(power_budget=power_budget)
                    if power_eff == 0:
                        # remaining power budget is too small
                        power_budget = 0
                    else:
                        thru_su = perf_ / PERF_BASE
                        serial_su = self.thru_core.perf_by_vdd(vdd_) / PERF_BASE
                        power_budget -= power_eff
                        rt = kl * (1-ko.pf)/serial_su + kl * ko.pf / thru_su
                        runtime.append(rt)
                        _logger.debug('runtime: {0}'.format(rt))

                if power_budget <= 0.1:
                    finish += max(runtime)
                    _logger.debug('=====warp finish=====')
                    _logger.debug('run time of this warp: {0}'.format(max(runtime)))
                    runtime = []
                    power_budget = self.sys_power

            if runtime:
                finish += max(runtime)
                _logger.debug('=====warp finish=====')
                _logger.debug('run time of this warp: {0}'.format(max(runtime)))

        _logger.debug('baseline: {0}, bench: {1}'.format(baseline, finish))
        return baseline / finish

    def get_speedup_appdag_serial(self, appdag):
        """Get the performance of the system, on an :class:`~lumos.model.AppDAG`
        application, all kernels are processed in serial.

        Parameters
        ----------
        appdag : :class:`~lumos.model.AppDAG`
          The target application

        Returns
        -------
        float
          speedup relative to running all kernels at the baseline performance.

        """
        dim_perf, opt_vdd, opt_cnum, power_eff = self._dim_perf_opt(power_budget=self.sys_power)

        thru_core = self.thru_core
        thrucore_serial_su = thru_core.perf_by_vdd(opt_vdd) / PERF_BASE

        thrucore_thru_su = dim_perf / PERF_BASE
        _logger.debug('thrucore serial su: {0}, thrucore parallel su: {1}'.format(
            thrucore_serial_su, thrucore_thru_su))

        serial_su = thru_core.perf_by_vdd(thru_core.vnom) / PERF_BASE
        _logger.debug('serial su: {0}'.format(serial_su))

        ker_lengths = appdag.get_all_kernel_lengths()
        ker_objs = appdag.get_all_kernels(mode='object')

        _logger.debug('dim_perf: {0} cnum: {1}, vdd: {2}'.format(
            dim_perf, opt_cnum, opt_vdd))
        baseline = sum(ker_lengths)
        perf = 0
        for kl, ko in zip(ker_lengths, ker_objs):
            _logger.debug('-------{0}---------'.format(ko.name))
            if self.has_asacc(ko.name):
                acc = self.get_asacc(ko.name)
                rt = kl / acc.perf()
                _logger.debug('Accelerator speedup: {0}'.format(acc.perf()))
            else:
                if ko.pf == 0:
                    # this is a serial application
                    rt = kl / serial_su
                else:
                    # this is a parallel application
                    rt = kl * (1-ko.pf)/thrucore_serial_su + kl * ko.pf/thrucore_thru_su

            perf += rt
            _logger.debug('runtime: {0}, accu runtime: {1}'.format(rt, perf))

        _logger.debug('baseline: {0}, bench: {1}'.format(baseline, perf))

        return baseline / perf

    def get_asacc(self, kernel_name):
        """right now, it will only return the first ASAcc"""
        try:
            asics_ = self.asic_dict[kernel_name]
        except KeyError:
            return None

        for acc_obj in asics_.values():
            return acc_obj

    def has_asacc(self, kernel_name):
        if kernel_name in self.asic_dict:
            return True
        else:
            return False

    # def get_perf(self, app):
    #     """Get the optimal performance of the system.

    #     It uses accelerators to execute kernels if available. Otherwise,
    #     kernels are executed and accelerated by throughput cores. The
    #     system will try to find the optimal number of throughput cores
    #     to be active to achieve the best overall throughput.

    #     Parameters
    #     ----------
    #     app : :class:`~lumos.model.Application`
    #       The targeted application.

    #     Returns
    #     -------
    #     (perf, cnum, vdd)
    #       a tuple of the following three properties:

    #       perf : float
    #         Relative performance, also should be the optimal with the given
    #         system configuration.
    #       cnum : int
    #         The number of active cores for the optimal configuration.
    #       vdd : float
    #         The supply voltage of throughput cores when executing parallel part
    #         of the application.

    #     """
    #     if self.serial_core:
    #         serial_core = self.serial_core
    #     else:
    #         serial_core = self.thru_core

    #     serial_core.vdd = serial_core.vmax
    #     serial_perf = serial_core.perf / PERF_BASE

    #     if not self.dim_perf:
    #         # need to update dim_perf
    #         # self.thru_core_power = self.sys_power
    #         ret = self._dim_perf_opt()
    #         self.dim_perf = ret['perf']
    #         self.opt_cnum = ret['cnum']
    #         self.opt_vdd = ret['vdd']

    #     dim_perf = self.dim_perf
    #     perf = (1 - app.f) / serial_perf + app.f_noacc / dim_perf

    #     for kid, ker_obj in app.kernels.items():
    #         if self.use_gpacc:
    #             gp_acc = self.gp_acc
    #             if kid in self.kernel_asic_table:
    #                 acc_id_list = self.kernel_asic_table[kid]
    #                 if len(acc_id_list) > 1:
    #                     _logger.warning(
    #                         'More than 1 ASIC is available for a single kernel, '
    #                         'will default to use the first one in the list, '
    #                         'order not guaranteed')
    #                 acc_id = acc_id_list[0]
    #                 acc = self.asic_dict[acc_id]
    #             else:
    #                 acc = None

    #             if acc and acc.area > 0:
    #                 perf = perf + app.kernels_covreage[kid] / \
    #                     (acc.perf(power=self.sys_power, bandwidth=self.sys_bandwidth) / PERF_BASE)
    #             else:
    #                 gp_acc_perf = gp_acc.perf(
    #                     ker_obj, power=self.sys_power, bandwidth=self.sys_bandwidth)
    #                 perf = perf + app.kernels[kid] / (gp_acc_perf / PERF_BASE)
    #         else:
    #             if kid in self.kernel_asic_table:
    #                 acc_id_list = self.kernel_asic_table[kid]
    #                 if len(acc_id_list) > 1:
    #                     _logger.warning(
    #                         'More than 1 ASIC is available for a single kernel, '
    #                         'will default to use the first one in the list, '
    #                         'order not guaranteed')
    #                 acc_id = acc_id_list[0]
    #                 acc = self.asic_dict[acc_id]
    #             else:
    #                 acc = None

    #             if acc and acc.area > 0:
    #                 acc_perf = acc.perf(power=self.sys_power, bandwidth=self.sys_bandwidth)
    #                 perf = perf + app.kernels_coverage[kid] / (acc_perf / PERF_BASE)
    #             else:
    #                 perf = perf + app.kernels_coverage[kid] / dim_perf

    #     return (1 / perf, self.opt_cnum, self.opt_vdd)

    def change_serial_core_vdd(self, vdd_mv):
        if self.serial_core:
            self.serial_core.vdd = vdd_mv

    def change_tput_core_vdd(self, vdd_mv):
        self.tput_core.vdd = vdd_mv

    def change_asic_vdd(self, acc_id, vdd_mv):
        """change supply voltage of an ASIC accelerator"""
        if acc_id not in self.asic_dict:
            raise MPSoCError('ASIC accelerator {0} does not exist in MPSoC')

        self.asic_dict[acc_id].vdd = vdd_mv
