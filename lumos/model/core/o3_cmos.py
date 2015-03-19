#!/usr/bin/env python
"""
This module models conventional cores. Two variants are derived from
an abstract base class AbstractCore, as IOCore and O3Core for an
in-order core and an out-of-order core respectively.
"""

import logging
from . import BaseCore
from ..tech import CMOSTechModel
import lumos.settings as settings

# from: http://www.spec.org/cpu2006/results/res2010q1/cpu2006-20100215-09685.html
# SPECfp2006 * (3.7/3.3) (freq scaling factor)
PERF_BASE = 28.48
DYNAMIC_POWER_BASE = 19.83 #Watts
STATIC_POWER_BASE = 5.34 #Watts
AREA_BASE = 26.48 #mm^2
FREQ_BASE = 3.7 #GHz
TECH_BASE = 45 #nm


class O3Core(BaseCore):
    def __init__(self, tech, model_name='hp'):
        tech_model = CMOSTechModel(model_name)
        super(O3Core, self).__init__(tech, tech_model, 'O3Core_CMOS')

    def init(self):
        tech = self._tech
        tech_model = self._tech_model

        if tech == TECH_BASE:
            self._area = AREA_BASE
            self._perf0 = PERF_BASE
            self._v0 = tech_model.vnom(tech)
            self._dp0 = DYNAMIC_POWER_BASE
            self._sp0 = STATIC_POWER_BASE
            self._f0 = FREQ_BASE
        else:
            self._area = AREA_BASE * tech_model.area_scale[tech] / tech_model.area_scale[TECH_BASE]
            self._perf0 = PERF_BASE * tech_model.perf_scale[tech] / tech_model.perf_scale[TECH_BASE]
            self._f0 = FREQ_BASE * tech_model.fnom_scale[tech] / tech_model.fnom_scale[TECH_BASE]
            self._dp0 = DYNAMIC_POWER_BASE * tech_model.dynamic_power_scale[tech] / tech_model.dynamic_power_scale[TECH_BASE]
            self._sp0 = STATIC_POWER_BASE * tech_model.static_power_scale[tech] / tech_model.static_power_scale[TECH_BASE]
            self._f0 = FREQ_BASE * tech_model.fnom_scale[tech] / tech_model.fnom_scale[TECH_BASE]
