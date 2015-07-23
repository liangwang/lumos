from lumos.model.mem.cache import *

import unittest

class TestMem(unittest.TestCase):
    def setUp(self):
        pass

    def test_cacti(self):
        c = CacheTraits(cache_sz_nom('128M'), tech_node=22)
        self.assertAlmostEqual(c.area, 115.9857141)

        c = CacheTraits(cache_sz_nom('64K'), tech_node=22)
        self.assertAlmostEqual(c.area, 0.0693157)
        self.assertAlmostEqual(c.power, 0.1212363)

        c = CacheTraits(cache_sz_nom('128K'), tech_node=22)
        self.assertAlmostEqual(c.area, 0.1792535)
        self.assertAlmostEqual(c.power, 0.1461256)
