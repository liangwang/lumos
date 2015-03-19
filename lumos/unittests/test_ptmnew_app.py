#!/usr/bin/env python

import sys
from lumos.model import App
import unittest


class TestApp(unittest.TestCase):
    def setUp(self):
        self.app = App(1)
        self.app.reg_kernel('MMM', 0.1)
        self.app.reg_kernel('BS', 0.2)

    def test_tag(self):
        self.assertEqual(self.app.tag, '30-BS-20-MMM-10')
