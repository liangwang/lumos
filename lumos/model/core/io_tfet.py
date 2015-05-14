#!/usr/bin/env python
"""
This module models conventional cores. Two variants are derived from
an abstract base class AbstractCore, as IOCore and O3Core for an
in-order core and an out-of-order core respectively.
"""

from ..tech import get_model
from .base import BaseCore

# from: http://www.spec.org/cpu2006/results/res2009q3/cpu2006-20090721-08251.html
# SPECfp_rate2006 / 8(cores) / 2 (threads) * (4.2/1.58) (freq scaling factor) * 1.4 ( 1/0.7, tech scaling factor)
# PERF_BASE = 15.92
# adjust to federation
PERF_BASE = 12.92*1.21/1.65 # scale CMOS core performance to 22nm, then apply 1.65x downgrade factor from CMOS to TFET
DYNAMIC_POWER_BASE = 0.5  # extracted from ISCA'14 paper, which is about 1/2.965 of the total power of IO_CMOS at 22nm. Therefore, O3Core_TFET will use the same scaling factor (2.965) for power.
STATIC_POWER_BASE = 0     # assume static power to be negligible
AREA_BASE = 7.65/4        # scaled area to 22nm
FREQ_BASE = 4.2/1.65      # GHz
TECH_BASE = 22


class IOCore(BaseCore):

    def __init__(self, tech_node, tech_variant='homo30nm'):
        tech_model = get_model('tfet', tech_variant)

        if tech_node == TECH_BASE:
            self._area = AREA_BASE
            self._perf0 = PERF_BASE
            self._v0 = tech_model.vnom(tech_node)
            self._dp0 = DYNAMIC_POWER_BASE
            self._sp0 = STATIC_POWER_BASE
            self._f0 = FREQ_BASE
        else:
            self._area = (AREA_BASE * tech_model.area_scale[tech_node] /
                          tech_model.area_scale[TECH_BASE])
            self._perf0 = (PERF_BASE * tech_model.perf_scale[tech_node] /
                           tech_model.perf_scale[TECH_BASE])
            self._f0 = (FREQ_BASE * tech_model.fnom_scale[tech_node] /
                        tech_model.fnom_scale[TECH_BASE])
            self._dp0 = (DYNAMIC_POWER_BASE * tech_model.dynamic_power_scale[tech_node] /
                         tech_model.dynamic_power_scale[TECH_BASE])
            self._sp0 = (STATIC_POWER_BASE * tech_model.static_power_scale[tech_node] /
                         tech_model.static_power_scale[TECH_BASE])
            self._f0 = (FREQ_BASE * tech_model.fnom_scale[tech_node] /
                        tech_model.fnom_scale[TECH_BASE])

        super(IOCore, self).__init__(tech_node, tech_model, 'IOCore_TFET')
