#!/usr/bin/env python

from lumos.model.accelerator import Accelerator
from lumos.model.kernel import Kernel, UCoreParam
from lumos.model.tech import TFETTechModel, CMOSTechModel
import unittest


class TestAccelerator(unittest.TestCase):
    def setUp(self):
        ker_obj = Kernel('test_ker')
        ker_obj.add_acc('fpga', UCoreParam(miu=10))
        ker_obj.add_acc('asic_5x', UCoreParam(miu=50))
        ker_obj.add_acc('asic_10x', UCoreParam(miu=100))
        ker_obj.add_acc('asic_50x', UCoreParam(miu=500))
        tfet_tech_model = TFETTechModel('homoTFET30nm')
        cmos_tech_model = CMOSTechModel('hp')
        self.acc_cmos = Accelerator('asic_5x', ker_obj, 10, 22, cmos_tech_model)
        self.acc_tfet = Accelerator('asic_5x', ker_obj, 10, 22, tfet_tech_model)

    def test_acc_vdd_scale(self):
        self.acc_cmos.vdd = 300
        self.assertAlmostEqual(self.acc_cmos.perf(), 18.37063799)

        self.acc_tfet.vdd = 300
        self.assertAlmostEqual(self.acc_tfet.perf(), 1617.87771896)

        self.acc_cmos.vdd = 400
        self.assertAlmostEqual(self.acc_cmos.perf(), 148.34224234)
    
        self.acc_tfet.vdd = 400
        self.assertAlmostEqual(self.acc_tfet.perf(), 2644.55958549)
        
        self.acc_cmos.vdd = 500
        self.assertAlmostEqual(self.acc_cmos.perf(), 807.96122739)

        self.acc_tfet.vdd = 500
        self.assertAlmostEqual(self.acc_tfet.perf(), 3710.34370167)

        self.acc_cmos.vdd = self.acc_cmos.tech_model.vnom(22)
        self.assertAlmostEqual(self.acc_cmos.perf(), 4363.52331606)

        self.acc_tfet.vdd = self.acc_tfet.tech_model.vnom(22)
        self.assertAlmostEqual(self.acc_tfet.perf(), 2644.55958549)
