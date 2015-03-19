#!/usr/bin/env python

import sys
import os
from lumos.model.system import MPSoC
from lumos.model.application import Application
from lumos.model.kernel import Kernel, UCoreParam
from lumos.model.tech import CMOSTechModel
from lumos.model import Sys_L
from lumos.model import IOCore_CMOS as IOCore
import unittest
from lxml import etree


def load_kernel(fname='norm.xml'):
    """
    Load kernels from an XML file.

    Args:
       fname (str):
          The file to be loaded

    Returns:
       kernels (list):
          A sorted (by name) list of kernels that have been loaded.
    """
    tree = etree.parse(fname)
    kernels = dict()
    for k_root in tree.iter('kernel'):
        k_name = k_root.get('name')
        k = Kernel(k_name)

        accelerator_root = k_root.find('accelerator')
        for ele in accelerator_root.getchildren():
            acc_id = ele.tag
            ucore_param = UCoreParam()
            for attr, val in ele.items():
                try:
                    setattr(ucore_param, attr, float(val))
                except ValueError:
                    print('(attr, val): {0}, {1}, val is not a float'.format(attr, val))
                except TypeError as te:
                    print(te)

            k.add_acc(acc_id, ucore_param)

        kernels[k_name] = k
    return kernels


def load_workload(kernels, fname='workload.xml'):
    """
    Load a workload from an XML file

    Args:
       fname (str):
          The XML file to be loaded

    Returns:
       workload (dict):
          A dict of applications this workload contains, indexed by application name
    """
    workload = dict()
    tree = etree.parse(fname)
    for app_root in tree.iter('app'):
        app_name = app_root.get('name')

        ele = app_root.find('f_parallel')
        f_parallel = float(ele.text)
        app = Application(f=f_parallel, name=app_name)

        kcfg_root = app_root.find('kernel_config')
        for k_ele in kcfg_root.iter('kernel'):
            kid = k_ele.get('name')
            kernel = kernels[kid]
            cov = float(k_ele.get('cov'))
            app.add_kernel(kernel, cov)

        workload[app_name] = app

    return workload


class TestMPSoC(unittest.TestCase):
    def setUp(self):
        budget = Sys_L
        tech = 22
        tput_core = IOCore(tech=22)
        self.sys = MPSoC(budget, tech, tput_core=tput_core)
        self.kernels = load_kernel(
            os.path.join(os.path.abspath(os.path.dirname(__file__)), 'kernels.xml'))
        self.workload = load_workload(self.kernels,
            os.path.join(os.path.abspath(os.path.dirname(__file__)), 'apps.xml'))

    def test_acc(self):
        app = self.workload['app_f100_c10']
        ker_obj = self.kernels['ker']
        self.sys.set_asic(ker_obj, 'asic_5x', 0.1, CMOSTechModel('hp'))
        self.assertAlmostEqual(self.sys.get_perf(app)['perf'], 117.84259499)
