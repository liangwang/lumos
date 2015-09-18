#!/usr/bin/env python

from lumos.model.acc import ASAcc as Accelerator
from lumos.model.workload import Kernel, KernelParam
from lumos.model.tech import get_model
import unittest


class TestAccelerator(unittest.TestCase):
    def setUp(self):
        ker_obj = Kernel('test_ker')
        ker_obj._add_kernel_param('fpga', KernelParam(perf=10))
        ker_obj._add_kernel_param('asic_5x', KernelParam(perf=50))
        ker_obj._add_kernel_param('asic_10x', KernelParam(perf=100))
        ker_obj._add_kernel_param('asic_50x', KernelParam(perf=500))
        tfet_tech_model = get_model('tfet', 'homo30nm')
        cmos_tech_model = get_model('cmos', 'hp')
        self.acc_cmos = Accelerator('asic_5x', ker_obj, 10, 22, cmos_tech_model)
        self.acc_tfet = Accelerator('asic_5x', ker_obj, 10, 22, tfet_tech_model)

    def test_acc_vdd_scale(self):
        self.acc_cmos.vdd = 300
        self.assertAlmostEqual(self.acc_cmos.perf(), 9.826, places=2)

        self.acc_tfet.vdd = 300
        self.assertAlmostEqual(self.acc_tfet.perf(), 1256.462, places=2)

        self.acc_cmos.vdd = 400
        self.assertAlmostEqual(self.acc_cmos.perf(), 79.345, places=2)

        self.acc_tfet.vdd = 400
        self.assertAlmostEqual(self.acc_tfet.perf(), 2053.795, places=2)

        self.acc_cmos.vdd = 500
        self.assertAlmostEqual(self.acc_cmos.perf(), 432.16, places=2)

        self.acc_tfet.vdd = 500
        self.assertAlmostEqual(self.acc_tfet.perf(), 2881.495, places=2)

        self.acc_cmos.vdd = self.acc_cmos.tech_vnom
        self.assertAlmostEqual(self.acc_cmos.perf(), 3388.761, places=2)

        self.acc_tfet.vdd = self.acc_tfet.tech_vnom
        self.assertAlmostEqual(self.acc_tfet.perf(), 2053.795, places=2)
