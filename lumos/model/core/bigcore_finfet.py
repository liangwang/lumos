#!/usr/bin/env python
"""
This module models conventional cores. Two variants are derived from
an abstract base class AbstractCore, as IOCore and O3Core for an
in-order core and an out-of-order core respectively.
"""

from .base import BaseCore
from ..tech import get_model

# SPECfp2006 score for Intel Xeon E5-2630 v3, 2.4GHz. 8 cores, TDP=85W
# from: https://www.spec.org/cpu2006/results/res2015q2/cpu2006-20150324-35588.html
PERF_BASE = 105

# per-core power -> 10.625W, assume 20% static power and 80% for dynamic power
DYNAMIC_POWER_BASE = 8.5    # Watts
STATIC_POWER_BASE = 2.125   # Watts
# Die area size from: http://www.pcper.com/reviews/Processors/Intel-Xeon-E5-2600-v3-Processor-Overview-Haswell-EP-18-Cores
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
AREA_BASE = 22.125          # mm^2
FREQ_BASE = 2.4             # GHz
TECH_BASE = 20              # nm


class BigCore(BaseCore):
    def __init__(self, tech_node, tech_variant='hp'):
        tech_model = get_model('finfet', tech_variant)
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

        super(BigCore, self).__init__(tech_node, tech_model, 'BigCore_FinFET')
