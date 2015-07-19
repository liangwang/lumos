#!/usr/bin/env python
"""
This module models conventional cores. Two variants are derived from
an abstract base class AbstractCore, as IOCore and O3Core for an
in-order core and an out-of-order core respectively.
"""

import abc
from lumos import settings
from lumos.model.misc import approx_equal
from ..tech import TechModelError
import numpy as np
import math

import logging
_logger = logging.getLogger('BaseCore')
_logger.setLevel(logging.INFO)
if settings.LUMOS_DEBUG and (
        'all' in settings.LUMOS_DEBUG or 'core' in settings.LUMOS_DEBUG):
    _logger.setLevel(logging.DEBUG)


class BaseCoreError(Exception):
    pass


class BaseCore(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, tech, tech_model, core_type):
        self._tech = tech
        self._tech_model = tech_model
        self._core_type = core_type

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
        if vdd < self.vmin or vdd > self.vmax:
            raise BaseCoreError('Vdd {0} not in the range supported by'
                                ' technology model ({1}mv - {2}mv)'.format(
                                    vdd, self.vmin, self.vmax))
        list_idx = vdd - self.vmin
        return self._dp_list[list_idx]

    def sp(self, vdd):
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
    def vnom(self):
        try:
            return self._tech_model.vnom(self._tech)
        except TypeError:
            raise BaseCoreError('no technology model loaded')
        except TechModelError:
            raise BaseCoreError(
                'no nominal supply for {0}nm'.format(self._tech))

    @property
    def vmax(self):
        try:
            return self._tech_model.vmax(self._tech)
        except TypeError:
            raise BaseCoreError('No technology model loaded')
        except TechModelError:
            raise BaseCoreError('No information for {0}nm'.format(self._tech))

    @property
    def vmin(self):
        try:
            return self._tech_model.vmin(self._tech)
        except TypeError:
            raise BaseCoreError('No technology model loaded')
        except TechModelError:
            raise BaseCoreError('No information for {0}nm'.format(self._tech))

    @property
    def area(self):
        return self._area

    @property
    def ctype(self):
        return self._core_type
