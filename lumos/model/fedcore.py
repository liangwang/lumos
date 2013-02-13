#!/usr/bin/env python
# encoding: utf-8

"""
Models federated core, which federates two in-order cores into a beefy out-of-order core as needed.

"""

import logging
from core import IOCore

class FedCore(object):
    """
    Federated Core, composed by two in-order cores
    """

    def __init__(self, tech=None, mech=None):
        """
        @todo: to be defined

        :tech: @todo
        :mech: @todo

        """
        self.tech = tech
        self.mech = mech

        self.iocore = IOCore(tech=tech, mech=mech)

        # federated core will have 3.7% area overhead
        # according to federation's DAC'08 paper
        self._area = self.iocore.area * 1.037 * 2

        self._perf = self.iocore.perf * 2

    def config(self, tech=None, mech=None):
        """
        @todo: Docstring for config

        :tech: @todo
        :mech: @todo
        :returns: @todo

        """
        self.iocore.config(tech=tech,mech=mech)

    @property
    def area(self):
        return self.iocore.area * 1.037 * 2

    @property
    def perf(self):
        return self.iocore.perf * 2
