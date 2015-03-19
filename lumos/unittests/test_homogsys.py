#!/usr/bin/env python

from lumos.model.system import HomogSys
from lumos.model.application import App
from lumos.model import IOCore_TFET
import unittest


class TestHomogSys(unittest.TestCase):
    def setUp(self):
        self.sys = HomogSys(area=600, power=120)
        self.sys.set_sys_prop(core=IOCore_TFET(tech=22))
        self.app = App(f=1)

    def test_perf_by_cnum(self):
        cnum = 64
        r = self.sys.perf_by_cnum(cnum, self.app)
        self.assertAlmostEqual(r['perf'],  65.84793879)
        self.assertAlmostEqual(r['freq'], 3.57129833)
