#!/usr/bin/env python
"""
Models hardware accelerators, parameters extracted from Chung's paper:

    *Sing-Chip Heterogenerous Computing: Does the Future Include Custom Logic,
    FPGAs, and GPGPUs?*, Eric S. Chung, et al., MICRO'10

"""

import sys
import abc
from lumos import settings
from .tech import TechModelError

import logging
_logger = logging.getLogger('Accelerator')
if settings.DEBUG:
    _logger.setLevel(logging.DEBUG)
else:
    _logger.setLevel(logging.INFO)

try:
    MAXINT = sys.maxint
except AttributeError:
    MAXINT = sys.maxsize


BCE_PARAMS_DICT = {
    # CMOS-HP
    'hp': {
        # area of core i7-960, core only
        'area': 24.125,
        # SPECfp2006 of Core i7-960
        'perf': 43.5,
        # extracted from Core i7-960's TDP, 130W/4=32.5,
        # then subtract un-core components, e.g. LLC, MCs
        'dp': 20,
        'sp': 0,
        # technology nodes for BCE characteristics
        'tech': 45,
        # FIXME: adjust to more realistic values, currently not used
        'bw': 1,
        },
    # TFET-homo60nm
    'homoTFET60nm': {
        'area': 24.125/4,
        'perf': 43.5*1.21/1.65,
        'dp': 20*0.206/2.965,
        'sp': 0,
        'tech': 22,
        'bw': 1,
        },
    # TFET-homo30nm
    'homoTFET30nm': {
        'area': 24.125/4,
        'perf': 43.5*1.21/1.65,
        'dp': 20*0.206/2.965,
        'sp': 0,
        'tech': 22,
        'bw': 1,
        },
    }


class AcceleratorError(Exception):
    pass


class Accelerator(object):
    """Model an application-specific hardware accelerator, or ASIC accelerator.

    An accelerator has the following properties:

    acc_id
      Accelerator identifier, this is in line with the acc_id in kernel
      description. This property is used to model alternate
      accelerators for the same computing kernel

    ker_obj
      The kernel object, for which the accelerator is designed.

    area
      The area of the accelerator, a metric of allocated resources.

    tech
      The technology nodes, e.g. 22(nm).

    tech_model
      The technology model, it could be CMOSTechModel or
      TFETTechModel.

    vdd
      The working supply voltage, it is initialized to the nominal
      supply of the associated technology node.
    """
    def __init__(self, acc_id, ker_obj, area, tech, tech_model):
        self._acc_id = acc_id
        self._ker_obj = ker_obj
        self._area = area
        self._tech = tech

        self._tech_model = tech_model
        self._vdd_mv = tech_model.vnom_dict[tech]

        try:
            bce_params = BCE_PARAMS_DICT[tech_model.name]
        except KeyError:
            raise AcceleratorError(
                'No BCE_PARAMS for technology model {0}'.format(tech_model.name))
        tech_base = bce_params['tech']
        area_base = bce_params['area']
        perf_base = bce_params['perf']
        dp_base = bce_params['dp']
        sp_base = bce_params['sp']
        bw_base = bce_params['bw']
        if tech == tech_base:
            self._a0, self._perf0, self._bw0 = area_base, perf_base, bw_base
            self._dp0, self._sp0 = dp_base, sp_base
        else:
            self._a0 = area_base * tech_model.area_scale[tech] / \
                tech_model.area_scale[tech_base]
            self._perf0 = perf_base * tech_model.perf_scale[tech] / \
                tech_model.perf_scale[tech_base]
            self._dp0 = dp_base * tech_model.dynamic_power_scale[tech] / \
                tech_model.dynamic_power_scale[tech_base]
            self._sp0 = sp_base * tech_model.static_power_scale[tech] / \
                tech_model.static_power_scale[tech_base]
            self._bw0 = bw_base * tech_model.fnom_scale[tech] / \
                tech_model.fnom_scale[tech_base]
        self._v0 = tech_model.vnom(tech)

    def __update_config(self):
        """Internal function to update value of ctype/tech specific parameters
        :returns: @todo

        """
        raise AcceleratorError('__update_config should not be called')
        area = self._area
        tech = self._tech
        vnom = int(self._tech_model.vnom(tech)*1000)
        bce_vnom = int(self._tech_model.vnom(BCE_TECH)*1000)

        self._a0 = BCE_AREA * self._tech_model.area_scale[tech] / \
            self._tech_model.area_scale[BCE_TECH]

        self._perf0 = BCE_PERF * self._tech_model.fnom_scale[tech] / \
            self._tech_model.fnom_scale[BCE_TECH]

        self._p0 = BCE_POWER * self._tech_model.dynamic_power_scale[tech] / \
            self._tech_model.dynamic_power_scale[BCE_TECH]

        self._bw0 = BCE_BW * self._tech_model.fnom_scale[tech] / \
            self._tech_model.fnom_scale[BCE_TECH]

    def perf(self, power=None, bandwidth=None):
        kernel = self._ker_obj
        uparam = kernel.get_acc(self._acc_id)

        if power:
            area_p = (power / self.power) * self._a0
        else:
            area_p = MAXINT

        if bandwidth:
            area_b = (bandwidth / self._bw0 / uparam.bw) * self._a0
        else:
            area_b = MAXINT

        area_eff = min(area_p, area_b, self._area)

        return self._perf0 * (area_eff / self._a0) * uparam.miu * \
            self._tech_model.freq(self._tech, self._vdd_mv)


    def bandwidth(self, app):
        """Calculate the bandwith consumed by the accelerator

        :app: @todo
        :returns: @todo

        """
        raise NotImplementedError('Accelerator\'s bandwidth method is not implemented yet')
        return self._bw0 * (self._area/self._a0) * app[self._acc_id].bw

    def config(self, tech=None, area=None, vdd_mv=None):
        """Configurate accelerator characteristics

        :tech: @todo
        :area: @todo
        :returns: @todo

        """
        raise AcceleratorError(
            'config should not be called, do not change "tech",'
            ' area/vdd are changed using other methods')
        update = True

        if not tech:
            self._tech = tech
        elif not self._tech:
            update = False

        if not area:
            self._area = area
        elif not self._area:
            update = False

        if not vdd:
            self._vdd_mv = vdd_mv
        elif not self._vdd_mv:
            update = False

        if update:
            self.__update_config()

    @property
    def power(self):
        """Calculate the power of a accelerator with certain application
        """
        return self.dp + self.sp

    @property
    def dp(self):
        kernel = self._ker_obj
        uparam = kernel.get_acc(self._acc_id)
        return self._dp0 * (self._area/self._a0) * uparam.phi * \
            self._tech_model.dynamic_power(self._tech, self._vdd_mv)

    @property
    def sp(self):
        return self._sp0 * self._tech_model.static_power(self._tech, self._vdd_mv)

    @property
    def vdd(self):
        """ Get the supply voltage (vdd) of the accelerator"""
        return self._vdd_mv
    @vdd.setter
    def vdd(self, vdd_mv):
        self._vdd_mv = vdd_mv

    @property
    def area(self):
        """ Get the area of the core """
        return self._area
    @area.setter
    def area(self, new_area):
        self._area = new_area

    @property
    def tech(self):
        """ Get the technology node, in nm """
        return self._tech

    @property
    def tech_model(self):
        return self._tech_model

    @property
    def kid(self):
        """ The kernel id (str) that this accelerator targets at. This is a read-only property
        """
        return self._ker_obj.kid
