import os
import lumos
from lumos.model.workload import load_kernels_and_apps
from lumos.model.system.hetero import HeterogSysDetailed as HetSys
from lumos.model.system.hetero import SysConfigDetailed as HetSysConfig
from lumos.model.system.homo import HomogSysDetailed as HomSys
from lumos.model.system.homo import SysConfigDetailed as HomSysConfig
from lumos.model.system.budget import Budget
import unittest


class TestDetailedApp(unittest.TestCase):
    def test_homog_vs_heterog_detailed(self):
        workload_xmlfile = os.path.join(
            os.path.dirname(lumos.model.workload.__file__), 'sirius.xml')
        _ks, _as = load_kernels_and_apps(workload_xmlfile)
        app = _as['synapp_0']

        hetsys = HetSys(HetSysConfig(), _ks)
        homsys = HomSys(HomSysConfig())
        self.assertAlmostEqual(hetsys.perf(650, app),
                               homsys.perf(650, app),
                               places=2)

    def test_homog_vs_heterog_detailed2(self):
        workload_xmlfile = os.path.join(
            os.path.dirname(lumos.model.workload.__file__), 'sirius.xml')
        _ks, _as = load_kernels_and_apps(workload_xmlfile)
        app = _as['synapp_0']

        config = HetSysConfig()
        config.rlacc_area_ratio = 0.2
        hetsys = HetSys(config, _ks)

        config2 = HomSysConfig()
        config2.budget = Budget(power=config.budget.power,
                                area=config.budget.area * 0.8)
        homsys = HomSys(config2)
        self.assertAlmostEqual(hetsys.perf(650,
                                           app,
                                           disable_rlacc=True),
                               homsys.perf(650, app),
                               places=2)
