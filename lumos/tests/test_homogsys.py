#!/usr/bin/env python

import os
from lumos.model.system.homo import HomogSys
from lumos.model.workload import SimpleApp
from lumos.model.core import BaseCore
from lumos.model.workload import load_kernels_and_apps
from lumos.model.system.homo import HomogSysDetailed, SysConfigDetailed
import unittest


class TestHomogSys(unittest.TestCase):
    def setUp(self):
        self.sys = HomogSys(area=600, power=120)
        self.sys.set_sys_prop(core=BaseCore(22, 'tfet', 'homo30nm', 'io'))
        self.app = SimpleApp(f=1)

    def test_perf_by_cnum(self):
        cnum = 64
        r = self.sys.perf_by_cnum(cnum, self.app)
        self.assertAlmostEqual(r['perf'],  65.84793879)
        self.assertAlmostEqual(r['freq'], 3.57129833)

    def test_homogsys_detailed(self):
        _ks, _as = load_kernels_and_apps(
            os.path.join(os.path.dirname(__file__), 'detailed_workload.xml'))
        app = _as['l1m0.005_l2m0.01_rm0.18_alpha0.5_cpi0.5']
        sysconfig = SysConfigDetailed()
        sys = HomogSysDetailed(sysconfig)

        # test perf score
        self.assertAlmostEqual(sys.perf(650, app), 1422.7337681)
