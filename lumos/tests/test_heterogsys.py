#!/usr/bin/env python

import os
import lumos
from lumos.model.workload import load_kernels_and_apps
from lumos.model.system.hetero import HeterogSysDetailed, SysConfigDetailed
import unittest


class TestHomogSys(unittest.TestCase):
    def setUp(self):
        pass

    def test_heterogsys_detailed(self):
        workload_xmlfile = os.path.join(
            os.path.dirname(os.path.dirname(lumos.__file__)), 'workloads', 'sirius.xml')
        _ks, _as = load_kernels_and_apps(workload_xmlfile)
        app = _as['synapp_0']
        sysconfig = SysConfigDetailed()
        sys = HeterogSysDetailed(sysconfig, _ks)
        self.assertAlmostEqual(sys.perf(650, app), 94.0191182)
