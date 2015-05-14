#!/usr/bin/env python

from lumos.model.system.homo import HomogSys
from lumos.model.application import SimpleApplication
from lumos.model.core import get_coreclass
import unittest


class TestHomogSys(unittest.TestCase):
    def setUp(self):
        self.sys = HomogSys(area=600, power=120)
        CoreClass = get_coreclass('io-tfet')
        self.sys.set_sys_prop(core=CoreClass(tech_node=22, tech_variant="homo30nm"))
        self.app = SimpleApplication(f=1)

    def test_perf_by_cnum(self):
        cnum = 64
        r = self.sys.perf_by_cnum(cnum, self.app)
        self.assertAlmostEqual(r['perf'],  65.84793879)
        self.assertAlmostEqual(r['freq'], 3.57129833)
