#!/usr/bin/env python

import os
from lumos.model.workload import load_kernels_and_apps
from lumos.model.system.mpsoc import MPSoC
from lumos.model.system.budget import Sys_L
from lumos.model.tech import get_model
from lumos.model.core import BaseCore
import unittest


class TestMPSoC(unittest.TestCase):
    def setUp(self):

        self.ks_, self.as_ = load_kernels_and_apps(
            os.path.join(os.path.dirname(__file__), 'appdag.xml'))

    def test_appdag_speedup_serial(self):
        budget = Sys_L
        tech = 22
        tput_core = BaseCore(22, 'cmos', 'hp', 'io')
        sys = MPSoC(budget, tech, tput_core=tput_core)
        app = self.as_['app_dag0']
        ker_obj = self.ks_['ker3']
        tech_model = get_model('cmos', 'hp')
        sys.add_asic(ker_obj, 'asic_5x', 0.1, tech_model)
        self.assertAlmostEqual(sys.get_speedup_appdag_serial(app), 3.561031891466)

    def test_appdag_speedup_parallel(self):
        budget = Sys_L
        tech = 22
        tput_core = BaseCore(22, 'cmos', 'hp', 'io')
        sys = MPSoC(budget, tech, tput_core=tput_core)
        app = self.as_['app_dag0']
        tech_model = get_model('cmos', 'hp')
        ker_obj = self.ks_['ker1']
        sys.add_asic(ker_obj, 'asic_5x', 0.1, tech_model)
        ker_obj = self.ks_['ker2']
        sys.add_asic(ker_obj, 'asic_5x', 0.1, tech_model)
        ker_obj = self.ks_['ker3']
        sys.add_asic(ker_obj, 'asic_5x', 0.1, tech_model)
        ker_obj = self.ks_['ker4']
        sys.add_asic(ker_obj, 'asic_5x', 0.1, tech_model)
        self.assertAlmostEqual(sys.get_speedup_appdag_parallel_greedy(app), 3.91827844296)
