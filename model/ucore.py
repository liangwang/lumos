#!/usr/bin/env python
'''
File: ucore.py
Author: Liang Wang <lw2aw@virginia.edu>
Description: Models unconventional cores, parameters extracted from Chung's paper:
    Sing-Chip Heterogenerous Computing: Does the Future Include Custom Logic,
    FPGAs, and GPGPUs?, Eric S. Chung, et al., MICRO'10

'''

import sys
import math
import logging
from tech import Base as techbase, Scale as techscl
from tech import ProjScale as projscl
from tech import LPBase as lpbase, PTMScale as ptmscl
import kernel


# area of core i7-960, core only
BCE_AREA = 24.125
# SPECfp2006 of Core i7-960
BCE_PERF = 43.5
# extracted from Core i7-960's TDP, 130W / 4 = 32.5, then exclude uncomputing components, e.g. LLC, MCs
BCE_POWER = 20

class UCore(object):
    def __init__(self, area=0, ctype=None, mech=None, tech=None):
        update = True

        self.ctype = ctype

        if mech is None:
            update = False
        self._mech = mech

        if tech is None:
            update = False
        self._tech = tech

        self._area = area

        if update:
            self.__update_config()

    def __update_config(self):
        """Internal function to update value of mech/ctype/tech specific parameters
        :returns: @todo

        """

        area = self._area
        tech = self._tech
        mech = self._mech

        self._a0 = BCE_AREA * techscl.area[tech]

        if mech == 'ITRS' or mech == 'CONS':
            self._perf0 = BCE_PERF * projscl.freq[mech][tech]
            self._p0 = BCE_POWER * projscl.dp[mech][tech]
            self._bw0 = projscl.freq[mech][tech]
        elif mech == 'HKMGS':
            self._perf0 = BCE_PERF * ptmscl.freq[mech][tech]
            self._p0 = BCE_POWER * ptmscl.dp[mech][tech]
            self._bw0 = ptmscl.freq[mech][tech]
        elif mech == 'LP':
            logging.error('U-core does not support LP processes')
            self._perf0 = 0
            self._p0 = 0
            self._bw0 = 0

    def perf(self, app, power=None, bandwidth=None):
        """Calculate the performance score of a u-core

        :app: @todo
        :returns: @todo

        """
        if power:
            area_p = (power / self._p0 / app[self.ctype].phi) * self._a0
        else:
            area_p = sys.maxint

        if bandwidth:
            area_b = (bandwidth / self._bw0 / app[self.ctype].bw) * self._a0
        else:
            area_b = sys.maxint

        area_eff = min(area_p, area_b, self._area)

        return self._perf0 * (area_eff / self._a0) * app[self.ctype].miu

    def power(self, app):
        """Calculate the power of a u-core with certain application

        :app: @todo
        :returns: @todo

        """
        return self._p0 * (self._area/self._a0) * app[self.ctype].phi

    def bandwidth(self, app):
        """Calculate the bandwith consumed by the ucore

        :app: @todo
        :returns: @todo

        """
        return self._bw0 * (self._area/self._a0) * app[self.ctype].bw

    def config(self, mech=None, ctype=None, tech=None, area=None):
        """Configurate ucore characteristics

        :mech: @todo
        :ctype: @todo
        :tech: @todo
        :area: @todo
        :returns: @todo

        """
        update = True

        if mech is not None:
            self._mech = mech
            #logging.debug('mech is %s' % mech)
        elif self._mech is None:
            update = False
            #logging.debug('mech is not set, no internal update')

        if ctype is not None:
            self.ctype = ctype
            #logging.debug('ctype is %s' % ctype)
        elif self.ctype is None:
            update = False
            #logging.debug('ctype is not set, no internal update')

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

    @property
    def mech(self):
        """ Get the scaling mechanism, either ITRS or CON(servative) """
        return self._mech


class ASIC(UCore):
    """ASIC accelerator"""

    def __init__(self, kid, area=0, mech=None, tech=None):
        """initilize ASIC

        :area: @todo
        :mech: @todo
        :tech: @todo

        """
        UCore.__init__(self,area, 'ASIC', mech, tech)

        self.kid = kid

    def perf(self, power=None, bandwidth=None):
        """performance under constraints

        :power: @todo
        :bandwidth: @todo
        :returns: @todo

        """
        ker = kernel.get_kernel(self.kid)
        if power:
            area_p = (power / self._p0 / ker['ASIC'].phi) * self._a0
        else:
            area_p = sys.maxint

        if bandwidth:
            area_b = (bandwidth / self._bw0 / ker['ASIC'].bw) * self._a0
        else:
            area_b = sys.maxint

        area_eff = min(area_p, area_b, self._area)

        return self._perf0 * (area_eff / self._a0) * ker['ASIC'].miu

    def config(self, mech=None, tech=None, area=None):
        UCore.config(self, mech, 'ASIC', tech, area)

    def power(self, app):
        logging.error("not implemented")

    def bandwidth(self, app):
        logging.error("not implemented")

class FPGA(UCore):
    """FPGA accelerator"""

    def __init__(self, area=0, mech=None, tech=None):
        """Initialize FPGA

        :area: @todo
        :mech: @todo
        :tech: @todo

        """
        UCore.__init__(self, area, 'FPGA', mech, tech)

    def perf(self, kid, power=None, bandwidth=None):
        ker = kernel.get_kernel(kid)
        if power:
            area_p = (power / self._p0 / ker['FPGA'].phi) * self._a0
        else:
            area_p = sys.maxint

        if bandwidth:
            area_b = (bandwidth / self._bw0 / ker['FPGA'].bw) * self._a0
        else:
            area_b = sys.maxint

        area_eff = min(area_p, area_b, self._area)

        return self._perf0 * (area_eff / self._a0) * ker['FPGA'].miu

    def config(self, mech=None, tech=None, area=None):
        UCore.config(self, mech, 'FPGA', tech, area)

    def power(self, app):
        logging.error("not implemented")

    def bandwidth(self, app):
        logging.error("not implemented")
