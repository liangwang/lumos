import os
import lumos
from lumos.model.workload import load_kernels_and_apps
from lumos.model.system.hetero import HeterogSysDetailed as HetSys, SysConfigDetailed as HetSysConfig
from lumos.model.system.homo import HomogSysDetailed as HomSys, SysConfigDetailed as HomSysConfig
import unittest

class TestDetailedApp(unittest.TestCase):
    def test_homog_vs_heterog_detailed(self):
        workload_xmlfile = os.path.join(
            os.path.dirname(os.path.dirname(lumos.__file__)), 'workloads', 'sirius.xml')
        _ks, _as = load_kernels_and_apps(workload_xmlfile)
        app = _as['synapp_0']

        hetsys = HetSys(HetSysConfig(), _ks)
        homsys = HomSys(HomSysConfig())
        self.assertAlmostEqual(hetsys.perf(650, app),
                               homsys.perf(650, app))
