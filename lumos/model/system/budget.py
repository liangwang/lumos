#!/usr/bin/env python


class Budget:
    """ Physical constraints for a system, including area, power, and memory bandwidth
    """
    def __init__(self, area=0, power=0, bw=None):
        self._area = area
        self._power = power
        self._bw = bw

    @property
    def area(self):
        """ Total area of a system, in mili-meters (mm^2)"""
        return self._area

    @property
    def power(self):
        """ Total TDP of a system, in watts (W)"""
        return self._power

    @property
    def bw(self):
        """ Total available memory bandwidth of a system, in GBytes/S.

        `bw` is in a form of python dict indexed by technology nodes, which looks like::

          {45: 180, 32: 198,
           22: 234, 16: 252}

        """
        return self._bw


# Predifined budgets

#: A predefined budget for large system, similar to SPARC T4
Sys_L = Budget(
    area=200, power=120, bw={
        45: 180, 32: 198, 22: 234, 16: 252, 20:234, 14: 271})

#: A predefined budget for medium system, similar to Xeon processor
Sys_M = Budget(
    area=130, power=65, bw={
        45: 117, 32: 129, 22: 152, 16: 164})

#: A predefined budget for small system, similar to Core2 processor
Sys_S = Budget(
    area=107, power=33, bw={
        45: 96, 32: 106, 22: 125, 16: 135})

LargeWithIdealBW = Budget(
    area=200, power=120, bw={
        45: 1000, 32: 1000, 22: 1000, 16: 1000})
