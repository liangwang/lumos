#!/usr/bin/env python
"""
Models unconventional cores, parameters extracted from Chung's paper:

    *Sing-Chip Heterogenerous Computing: Does the Future Include Custom Logic,
    FPGAs, and GPGPUs?*, Eric S. Chung, et al., MICRO'10

"""

import sys
import math
import logging
from .tech import CMOSTechModel



# area of core i7-960, core only
BCE_AREA = 24.125
# SPECfp2006 of Core i7-960
BCE_PERF = 43.5
# extracted from Core i7-960's TDP, 130W / 4 = 32.5, then exclude uncomputing components, e.g. LLC, MCs
BCE_POWER = 20
# Technology nodes for BCE characteristics
BCE_TECH = 45

BCE_BW = 1     # FIXME: change to more realistic values

class UCoreError(Exception):
    pass

class UCore(object):
    def __init__(self, uid, area=0, ctype=None, tech=None, model_name='hp'):
        update = True

        self._ctype = ctype

        self._tech_model = CMOSTechModel(model_name)

        if tech is None:
            update = False
        self._tech = tech

        self._area = area

        self._uid = uid

        if update:
            self.__update_config()

    @property
    def ctype(self):
        raise DeprecationWarning('ctype is not used for UCore')


    def __update_config(self):
        """Internal function to update value of ctype/tech specific parameters
        :returns: @todo

        """

        area = self._area
        tech = self._tech
        vnom = int(self._tech_model.vnom(tech)*1000)
        bce_vnom = int(self._tech_model.vnom(BCE_TECH)*1000)

        self._a0 = BCE_AREA * self._tech_model.area_scale[tech] / self._tech_model.area_scale[BCE_TECH]

        self._perf0 = BCE_PERF * self._tech_model.fnom_scale[tech] / self._tech_model.fnom_scale[BCE_TECH]

        self._p0 = BCE_POWER * self._tech_model.dynamic_power_scale[tech] / self._tech_model.dynamic_power_scale[BCE_TECH]

        self._bw0 = BCE_BW * self._tech_model.fnom_scale[tech] / self._tech_model.fnom_scale[BCE_TECH]

    def perf(self, kernel, power=None, bandwidth=None):
        uparam = kernel.get_acc(self._uid)

        if power:
            area_p = (power / self._p0 / uparam.phi) * self._a0
        else:
            area_p = sys.maxint

        if bandwidth:
            area_b = (bandwidth / self._bw0 / uparam.bw) * self._a0
        else:
            area_b = sys.maxint

        area_eff = min(area_p, area_b, self._area)

        return self._perf0 * (area_eff / self._a0) * uparam.miu


    def power(self, app):
        """Calculate the power of a u-core with certain application

        :app: @todo
        :returns: @todo

        """
        return self._p0 * (self._area/self._a0) * app[self._uid].phi

    def bandwidth(self, app):
        """Calculate the bandwith consumed by the ucore

        :app: @todo
        :returns: @todo

        """
        return self._bw0 * (self._area/self._a0) * app[self._uid].bw

    def config(self, tech=None, area=None):
        """Configurate ucore characteristics

        :tech: @todo
        :area: @todo
        :returns: @todo

        """
        update = True

        if tech is not None:
            self._tech = tech
            #logging.debug('tech is %d' % tech)
        elif self._tech is None:
            update = False
            #logging.debug('tech is not set, no internal update')

        if area is not None:
            self._area = area
            #logging.debug('area is %f' % area)
        elif self._area is None:
            update = False
            #logging.debug('area is not set, no internal update')

        if update:
            self.__update_config()

    @property
    def area(self):
        """ Get the area of the core """
        return self._area

    @property
    def tech(self):
        """ Get the technology node, in nm """
        return self._tech


class AppAccelerator(UCore):
    def __init__(self, uid, ker_obj, area=0, tech=None, model_name='hp'):
        super(AppAccelerator, self).__init__(uid,
            area=area, tech=tech, model_name=model_name)

        self._ker_obj = ker_obj

    @property
    def kid(self):
        """ The kernel id (str) that this accelerator targets at. This is a read-only property
        """
        return self._ker_obj.kid

    def perf(self, power=None, bandwidth=None):
        return super(AppAccelerator, self).perf(self._ker_obj, power, bandwidth)


class GPAccelerator(UCore):
    def __init__(self, uid, area=0, tech=None, model_name='hp'):
        super(GPAccelerator, self).__init__(uid,
            area=area, tech=tech, model_name=model_name)
