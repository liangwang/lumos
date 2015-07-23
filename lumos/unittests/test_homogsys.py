#!/usr/bin/env python

from lumos.model.system.homo import HomogSys
from lumos.model.application import SimpleApplication
from lumos.model.core import BaseCore
import unittest


class TestHomogSys(unittest.TestCase):
    def setUp(self):
        self.sys = HomogSys(area=600, power=120)
        self.sys.set_sys_prop(core=BaseCore(22, 'tfet', 'homo30nm', 'io'))
        self.app = SimpleApplication(f=1)

    def test_perf_by_cnum(self):
        cnum = 64
        r = self.sys.perf_by_cnum(cnum, self.app)
        self.assertAlmostEqual(r['perf'],  65.84793879)
        self.assertAlmostEqual(r['freq'], 3.57129833)
