#!/usr/bin/env python
"""
This module models conventional cores. Two variants are derived from
an abstract base class AbstractCore, as IOCore and O3Core for an
in-order core and an out-of-order core respectively.
"""

from .base import BaseCore
from ..tech import get_model

# SPECfp2006 score for Intel Atom C2750, 8 cores, TDP=20W
# from: https://www.spec.org/cpu2006/results/res2015q2/cpu2006-20150324-35588.html
PERF_BASE = 23.3

# per-core power -> 2.5W, assume 20% static power and 80% for dynamic power
# total power from io-cmos, which is 1.4W, then apply 20/80 distribution
# to static/dynamic power
DYNAMIC_POWER_BASE = 1.12    # Watts
STATIC_POWER_BASE = 0.28   # Watts
# DYNAMIC_POWER_BASE = 2    # Watts
# STATIC_POWER_BASE = 0.5   # Watts

# Die area size is not available as of <2015-05-09 Sat>
# sacled from io-cmos
# AREA_BASE = 1.9125          # mm^2
AREA_BASE = 6.392          # mm^2
FREQ_BASE = 2.4             # GHz
TECH_BASE = 20              # nm


class SmallCore(BaseCore):
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

        super(SmallCore, self).__init__(tech_node, tech_model, 'SmallCore_FinFET')
