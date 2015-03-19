#!/usr/bin/env python
"""
This module models conventional cores. Two variants are derived from
an abstract base class AbstractCore, as IOCore and O3Core for an
in-order core and an out-of-order core respectively.
"""

import logging
from ..tech import TFETTechModel
from . import BaseCore
import lumos.settings as settings

# from: http://www.spec.org/cpu2006/results/res2009q3/cpu2006-20090721-08251.html
# SPECfp_rate2006 / 8(cores) / 2 (threads) * (4.2/1.58) (freq scaling factor) * 1.4 ( 1/0.7, tech scaling factor)
#PERF_BASE = 15.92
# adjust to federation
PERF_BASE = 28.48*1.21/1.65
DYNAMIC_POWER_BASE = (19.83+5.34)*0.206/2.965
STATIC_POWER_BASE = 0
AREA_BASE = 26.48/4
FREQ_BASE = 3.7/1.65
TECH_BASE = 22


class O3Core(BaseCore):

    def __init__(self, tech, model_name='homoTFET30nm'):
        tech_model = TFETTechModel(model_name)
        super(IOCore, self).__init__(tech, tech_model, 'O3Core_TFET')

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
