#!/usr/bin/env python
"""
This module models conventional cores. Two variants are derived from
an abstract base class AbstractCore, as IOCore and O3Core for an
in-order core and an out-of-order core respectively.
"""

import abc
from lumos import settings
from lumos.model.misc import approx_equal
from ..tech import get_model as get_tech_model, TechModelError
import numpy as np
import math

import logging
_logger = logging.getLogger('BaseCore')
_logger.setLevel(logging.INFO)
if settings.LUMOS_DEBUG and (
        'all' in settings.LUMOS_DEBUG or 'core' in settings.LUMOS_DEBUG):
    _logger.setLevel(logging.DEBUG)


CORE_PARAMS = {
    'io-cmos-hp': {
        # from: http://www.spec.org/cpu2006/results/res2009q3/cpu2006-20090721-08251.html
        # SPECfp_rate2006 / 8(cores) / 2 (threads) *
        # (4.2/1.58) (freq scaling factor) * 1.4 ( 1/0.7, tech_node scaling factor)
        # PERF_BASE = 15.92
        # adjust to federation
        'PERF_BASE': 12.92,         # SPECmark score
        'DYNAMIC_POWER_BASE': 6.14, # Watts
        'STATIC_POWER_BASE': 1.058, # Watts
        'AREA_BASE': 7.65,          # mm^2
        'FREQ_BASE': 4.2,           # GHz
        'TECH_BASE': 45,            # nm
    },
    'io-cmos-lp': {
        # @TODO: it is assumed to be the same as io-cmos-hp, may need fix
        'PERF_BASE': 12.92,         # SPECmark score
        'DYNAMIC_POWER_BASE': 6.14, # Watts
        'STATIC_POWER_BASE': 1.058, # Watts
        'AREA_BASE': 7.65,          # mm^2
        'FREQ_BASE': 4.2,           # GHz
        'TECH_BASE': 45,            # nm
    },
    'o3-cmos-hp': {
        # Core 2 Duo E8600
        # from: http://www.spec.org/cpu2006/results/res2010q1/cpu2006-20100215-09685.html
        # SPECfp2006 * (3.7/3.3) (freq scaling factor)
        'PERF_BASE': 28.48,
        'DYNAMIC_POWER_BASE': 19.83,  # Watts
        'STATIC_POWER_BASE': 5.34,    # Watts
        'AREA_BASE': 26.48,           # mm^2
        'FREQ_BASE': 3.7,             # GHz
        'TECH_BASE': 45,              # nm
    },
    'o3-cmos-lp': {
        # @TODO: it is assumed to be the same as o3-cmos-hp, may need fix
        'PERF_BASE': 28.48,
        'DYNAMIC_POWER_BASE': 19.83,  # Watts
        'STATIC_POWER_BASE': 5.34,    # Watts
        'AREA_BASE': 26.48,           # mm^2
        'FREQ_BASE': 3.7,             # GHz
        'TECH_BASE': 45,              # nm
    },
    'io-tfet-homo30nm': {
        # from: http://www.spec.org/cpu2006/results/res2009q3/cpu2006-20090721-08251.html
        # SPECfp_rate2006 / 8(cores) / 2 (threads) * (4.2/1.58) (freq scaling factor) * 1.4 ( 1/0.7, tech scaling factor)
        # PERF_BASE = 15.92
        # adjust to federation
        'PERF_BASE': 12.92*1.21/1.65, # scale CMOS core performance to 22nm, then apply 1.65x downgrade factor from CMOS to TFET
        'DYNAMIC_POWER_BASE': 0.5,  # extracted from ISCA'14 paper, which is about 1/2.965 of the total power of IO_CMOS at 22nm. Therefore, O3Core_TFET will use the same scaling factor (2.965) for power.
        'STATIC_POWER_BASE': 0,     # assume static power to be negligible
        'AREA_BASE': 7.65/4,        # scaled area to 22nm
        'FREQ_BASE': 4.2/1.65,      # GHz
        'TECH_BASE': 22,
    },
    'io-tfet-homo60nm': {
        # @TODO: the same as io-tfet-homo30nm
        'PERF_BASE': 12.92*1.21/1.65,
        'DYNAMIC_POWER_BASE': 0.5,
        'STATIC_POWER_BASE': 0,
        'AREA_BASE': 7.65/4,
        'FREQ_BASE': 4.2/1.65,
        'TECH_BASE': 22,
    },
    'o3-tfet-homo30nm': {
        # from: http://www.spec.org/cpu2006/results/res2009q3/cpu2006-20090721-08251.html
        # SPECfp_rate2006 / 8(cores) / 2 (threads) * (4.2/1.58) (freq scaling factor) * 1.4 ( 1/0.7, tech_node scaling factor)
        'PERF_BASE': 28.48*1.21/1.65,
        'DYNAMIC_POWER_BASE': (19.83+5.34)*0.206/2.965,
        'STATIC_POWER_BASE': 0,
        'AREA_BASE': 26.48/4,
        'FREQ_BASE': 3.7/1.65,
        'TECH_BASE': 22,
    },
    'o3-tfet-homo60nm': {
        # @TODO: the same as o3-tfet-homo30nm
        'PERF_BASE': 28.48*1.21/1.65,
        'DYNAMIC_POWER_BASE': (19.83+5.34)*0.206/2.965,
        'STATIC_POWER_BASE': 0,
        'AREA_BASE': 26.48/4,
        'FREQ_BASE': 3.7/1.65,
        'TECH_BASE': 22,
    },
    'bigcore-finfet-hp': {
        # SPECfp2006 score for Intel Xeon E5-2630 v3, 2.4GHz. 8 cores, TDP=85W
        # from: https://www.spec.org/cpu2006/results/res2015q2/cpu2006-20150324-35588.html
        'PERF_BASE': 105,

        # per-core power -> 10.625W, assume 20% static power and 80% for dynamic power
        'DYNAMIC_POWER_BASE': 8.5,    # Watts
        'STATIC_POWER_BASE': 2.125,   # Watts
        # Die area size from:
        # http://www.pcper.com/reviews/Processors/Intel-Xeon-E5-2600-v3-Processor-Overview-Haswell-EP-18-Cores
        # High Core Count
        #   5.56 Billion transistors
        #   661 mm2 die size
        # Medium Core Count
        #   3.83 Billion transistors
        #   483 mm2 die
        # Low Core Count
        #   2.6 Billion transistors
        #   354 mm2 die
        # Use low core count for total area. per-core area is 354 / 8 = 44.25.
        # Assum 50% for core-only component, so that AREA_BASE = 44.25/2 = 22.125
        'AREA_BASE': 22.125,          # mm^2
        'FREQ_BASE': 2.4,             # GHz
        'TECH_BASE': 20,              # nm
    },
    'bigcore-finfet-lp': {
        # @TODO: the same as bigcore-finfet-hp
        'PERF_BASE': 105,
        'DYNAMIC_POWER_BASE': 8.5,    # Watts
        'STATIC_POWER_BASE': 2.125,   # Watts
        'AREA_BASE': 22.125,          # mm^2
        'FREQ_BASE': 2.4,             # GHz
        'TECH_BASE': 20,              # nm
    },
    'bigcore-tfet-homo30nm': {
        # scaled from bigcore-finfet-hp
        'PERF_BASE': 105/1.65,
        'DYNAMIC_POWER_BASE': 10.625/2.965,
        'STATIC_POWER_BASE': 0,
        'AREA_BASE': 22.125,
        'FREQ_BASE': 2.4/1.65,
        'TECH_BASE': 22,
    },
    'bigcore-tfet-homo60nm': {
        # scaled from bigcore-finfet-hp
        'PERF_BASE': 105/1.65,
        'DYNAMIC_POWER_BASE': 10.625/2.965,
        'STATIC_POWER_BASE': 0,
        'AREA_BASE': 22.125,
        'FREQ_BASE': 2.4/1.65,
        'TECH_BASE': 22,
    },
    'smallcore-finfet-hp': {
        # SPECfp2006 score for Intel Atom C2750, 8 cores, TDP=20W
        # from: https://www.spec.org/cpu2006/results/res2015q2/cpu2006-20150324-35588.html
        'PERF_BASE': 23.3,

        # per-core power -> 2.5W, assume 20% static power and 80% for dynamic power
        # total power from io-cmos, which is 1.4W, then apply 20/80 distribution
        # to static/dynamic power
        'DYNAMIC_POWER_BASE': 1.12,    # Watts
        'STATIC_POWER_BASE': 0.28,   # Watts
        # DYNAMIC_POWER_BASE = 2    # Watts
        # STATIC_POWER_BASE = 0.5   # Watts

        # Die area size is not available as of <2015-05-09 Sat>
        # sacled from io-cmos
        # AREA_BASE = 1.9125          # mm^2
        'AREA_BASE': 6.392,          # mm^2
        'FREQ_BASE': 2.4,             # GHz
        'TECH_BASE': 20,              # nm
    },
    'smallcore-finfet-lp': {
        # @TODO: the same as smallcore-finfet-lp
        'PERF_BASE': 23.3,
        'DYNAMIC_POWER_BASE': 1.12,    # Watts
        'STATIC_POWER_BASE': 0.28,   # Watts
        'AREA_BASE': 6.392,          # mm^2
        'FREQ_BASE': 2.4,             # GHz
        'TECH_BASE': 20,              # nm
    },
    'smallcore-tfet-homo30nm': {
# scaled from smallcore-finfet-hp
        'PERF_BASE': 23.3/1.65,           # scale CMOS core performance to 22nm, then apply 1.65x downgrade factor from CMOS to TFET
        'DYNAMIC_POWER_BASE': 2.5/2.965,  # extracted from ISCA'14 paper, which is about 1/2.965 of the total power of IO_CMOS at 22nm. Therefore, O3Core_TFET will use the same scaling factor (2.965) for power.
        'STATIC_POWER_BASE': 0,           # assume static power to be negligible
        'AREA_BASE': 6.392,               # scaled area to 22nm
        'FREQ_BASE': 2.4/1.65,            # GHz
        'TECH_BASE': 22,
    },
    'smallcore-tfet-homo60nm': {
# scaled from smallcore-finfet-hp
        'PERF_BASE': 23.3/1.65,           # scale CMOS core performance to 22nm, then apply 1.65x downgrade factor from CMOS to TFET
        'DYNAMIC_POWER_BASE': 2.5/2.965,  # extracted from ISCA'14 paper, which is about 1/2.965 of the total power of IO_CMOS at 22nm. Therefore, O3Core_TFET will use the same scaling factor (2.965) for power.
        'STATIC_POWER_BASE': 0,           # assume static power to be negligible
        'AREA_BASE': 6.392,               # scaled area to 22nm
        'FREQ_BASE': 2.4/1.65,            # GHz
        'TECH_BASE': 22,
    },
}

class BaseCoreError(Exception):
    pass


class BaseCore(object):
    def __init__(self, tech, tech_model_name, tech_model_variant, core_type):
        self._tech = tech
        self._tech_model = get_tech_model(tech_model_name, tech_model_variant)
        self._core_type = core_type

        tech_model = self._tech_model
        cparam_key = '{0}-{1}'.format(core_type, tech_model.mnemonic)
        try:
            core_params = CORE_PARAMS[cparam_key]
        except KeyError:
            raise BaseCoreError('No entry found in CORE_PARAMS for {0}'.format(cparam_key))

        TECH_BASE = core_params['TECH_BASE']
        PERF_BASE = core_params['PERF_BASE']
        DYNAMIC_POWER_BASE = core_params['DYNAMIC_POWER_BASE']
        STATIC_POWER_BASE = core_params['STATIC_POWER_BASE']
        FREQ_BASE = core_params['FREQ_BASE']
        AREA_BASE = core_params['AREA_BASE']
        if tech == TECH_BASE:
            self._area = AREA_BASE
            self._perf0 = PERF_BASE
            self._v0 = tech_model.vnom(tech)
            self._dp0 = DYNAMIC_POWER_BASE
            self._sp0 = STATIC_POWER_BASE
            self._f0 = FREQ_BASE
        else:
            self._area = (AREA_BASE * tech_model.area_scale[tech] /
                          tech_model.area_scale[TECH_BASE])
            self._perf0 = (PERF_BASE * tech_model.perf_scale[tech] /
                           tech_model.perf_scale[TECH_BASE])
            self._f0 = (FREQ_BASE * tech_model.fnom_scale[tech] /
                        tech_model.fnom_scale[TECH_BASE])
            self._dp0 = (DYNAMIC_POWER_BASE * tech_model.dynamic_power_scale[tech] /
                         tech_model.dynamic_power_scale[TECH_BASE])
            self._sp0 = (STATIC_POWER_BASE * tech_model.static_power_scale[tech] /
                         tech_model.static_power_scale[TECH_BASE])
            self._f0 = (FREQ_BASE * tech_model.fnom_scale[tech] /
                        tech_model.fnom_scale[TECH_BASE])

        self._vdd_list = np.arange(self.vmin, self.vmax+1)
        self._sp_list = np.array([self._tech_model.static_power(self._tech, v_)
                                  for v_ in self._vdd_list]) * self._sp0
        self._dp_list = np.array([self._tech_model.dynamic_power(self._tech, v_)
                                  for v_ in self._vdd_list]) * self._dp0
        self._freq_list = np.array([self._tech_model.freq(self._tech, v_)
                                    for v_ in self._vdd_list]) * self._f0

        _logger.debug('a0: {0}, dp0: {1}, sp0: {2}, perf0: {3}'.format(
            self._area, self._dp0, self._sp0, self._perf0))

    def freq(self, vdd):
        if vdd < self.vmin or vdd > self.vmax:
            raise BaseCoreError('Vdd {0} not in the range supported by'
                                ' technology model ({1}mv - {2}mv)'.format(
                                    vdd, self.vmin, self.vmax))
        list_idx = vdd - self.vmin
        return self._freq_list[list_idx]

    def perf_by_vdd(self, vdd):
        """Get performance when the core is operated at the given supply (vdd)

        Parameters
        ----------
        vdd : int
          Supply voltage in milli-volts (mV)

        Returns
        -------
        float
          The achieved performance.
        """
        return self._perf0 * self.freq(vdd) / self.freq(self.vnom)

    def perf_constrainted_by_power(self, power_budget):
        """Get performance constrained by specified power budget

        Use binary search to find the optimal supply voltage which yields the
        highest performance under the specified power constraint.

        Parameters
        ----------
        power_budget : float
          The power constraint.

        Returns
        -------
        perf : float
          The achieved optimal performance. If 0 is returned, that means the
          power_budget is too constrained to met even when the core is operated
          at the lowest supply (tech_model.vmin).
        vdd : int
          The supply voltage when achieving the optimal performance.
        """
        vmin = self.vmin
        if self.power(vmin) > power_budget:
            return (0, 0)

        vmax = self.vmax
        if self.power(vmax) < power_budget:
            perf_opt = self._perf0 * self.freq(vmax) / self.freq(self.vnom)
            return (perf_opt, vmax)

        perf_opt = 0
        vdd_opt = 0
        while vmax > vmin:
            vmid = math.ceil((vmin+vmax) / 2)
            power_vmid = self.power(vmid)
            if approx_equal(power_vmid, power_budget):
                perf_opt = self._perf0 * self.freq(vmid) / self.freq(self.vnom)
                vdd_opt = vmid
                break
            elif power_vmid > power_budget:
                vmax = vmid - 1
                vdd_opt = vmax
            else:
                vmin = vmid
                vdd_opt = vmin

        perf_opt = self._perf0 * self.freq(vdd_opt) / self.freq(self.vnom)
        return (perf_opt, vdd_opt)

    def perf(self):
        """Return the performance at nominal operating point.

        'Nominal opearting point' means nominal supply without power constraint.

        Returns
        -------
        flaot:
          The performance when working at nominal supply
        """
        return self.perf_by_vdd(self.vnom)

    def power(self, vdd):
        return self.dp(vdd) + self.sp(vdd)

    def dp(self, vdd):
        """Dynamic power consumption when operating at the given supply

        Parameters
        ----------
        vdd: int
          Supply voltage in mV

        Returns
        -------
        float
          Dynamic power in Watts
        """
        if vdd < self.vmin or vdd > self.vmax:
            raise BaseCoreError('Vdd {0} not in the range supported by'
                                ' technology model ({1}mv - {2}mv)'.format(
                                    vdd, self.vmin, self.vmax))
        list_idx = vdd - self.vmin
        return self._dp_list[list_idx]

    def sp(self, vdd):
        """Static power consumption when operating at the given supply

        Parameters
        ----------
        vdd: int
          Supply voltage in mV

        Returns
        -------
        float
          Static power in Watts
        """
        if vdd < self.vmin or vdd > self.vmax:
            raise BaseCoreError('Vdd {0} not in the range supported by'
                                ' technology model ({1}mv - {2}mv)'.format(
                                    vdd, self.vmin, self.vmax))
        list_idx = vdd - self.vmin
        return self._sp_list[list_idx]

    @property
    def tech(self):
        if not self._tech:
            raise BaseCoreError('No technology node specified')
        return self._tech

    @property
    def perfnom(self):
        return self._perf0

    @property
    def fnom(self):
        return self._f0

    @property
    def vnom(self):
        return self._tech_model.vnom(self._tech)

    @property
    def vmax(self):
        return self._tech_model.vmax(self._tech)

    @property
    def vmin(self):
        return self._tech_model.vmin(self._tech)

    @property
    def area(self):
        return self._area

    @property
    def ctype(self):
        return self._core_type
