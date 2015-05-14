#!/usr/bin/env python3

import unittest
from lumos.model.misc import load_kernels_and_apps

import os
curdir = os.path.dirname(__file__)


class TestAppDAG(unittest.TestCase):
    def setUp(self):
        self._ks, self._as = load_kernels_and_apps(os.path.join(curdir, 'appdag.xml'))
        self._app = self._as['app_dag0']

    def test_get_predecent_kernel(self):
        self.assertEqual(self._app.get_precedent_kernel(5), [1, 2, 3, 4])

    def test_kernels_depth_sort(self):
        self.assertEqual(self._app.kernels_depth_sort(), [[0], [1, 2, 3, 4], [5]])

    def test_serialize_kernels(self):
        self.assertEqual(self._app.kernels_topo_sort(), [0, 1, 2, 3, 4, 5])

    def test_speedup(self):
        speedup_dict = {0: 1.2, 1: 1.3, 5: 1.5, 4: 2}
        self.assertAlmostEqual(self._app.get_speedup(speedup_dict), 1.2)
