#!/usr/bin/env python

import os
import lumos
from lumos.model.workload import load_kernels_and_apps
from lumos.model.system.hetero import HeterogSysDetailed, SysConfigDetailed
import unittest


class TestHeterogSys(unittest.TestCase):
    def setUp(self):
        pass

    def test_heterogsys_detailed(self):
        workload_xmlfile = os.path.join(
            os.path.dirname(lumos.model.workload.__file__), 'sirius.xml')
        _ks, _as = load_kernels_and_apps(workload_xmlfile)
        app = _as['synapp_0']
        sysconfig = SysConfigDetailed()
        sys = HeterogSysDetailed(sysconfig, _ks)
        self.assertAlmostEqual(sys.perf(650, app), 124.692, places=2)

    def test_reconfig_overhead(self):
        workload_xmlfile = os.path.join(
            os.path.dirname(lumos.model.workload.__file__), 'sirius.xml')
        _ks, _as = load_kernels_and_apps(workload_xmlfile)
        app = _as['synapp_reconfig_overhead_0']
        sysconfig = SysConfigDetailed()
        sysconfig.rlacc_area_ratio = 0.2
        sys = HeterogSysDetailed(sysconfig, _ks)
        self.assertAlmostEqual(sys.perf(750, app), 1083.076, places=2)
        app = _as['synapp_reconfig_overhead_1']
        self.assertAlmostEqual(sys.perf(750, app), 766.22, places=2)
        app = _as['synapp_reconfig_overhead_2']
        self.assertAlmostEqual(sys.perf(750, app), 686.615, places=2)
        app = _as['synapp_reconfig_overhead_3']
        self.assertAlmostEqual(sys.perf(750, app), 686.615, places=2)
