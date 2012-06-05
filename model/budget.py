#!/usr/bin/env python
# encoding: utf-8

class SysLarge:
    area = 200
    power = 120
    bw = {45: 180, 32: 198,
          22: 234, 16: 252}

class SysMedium:
    area = 130
    power = 65
    bw = {45: 117, 32: 129,
          22: 152, 16: 164}

class SysSmall:
    area = 107
    power = 33
    bw = {45: 96, 32: 106,
          22: 125, 16: 135}

class LargeWithIdealBW:
    area = 200
    power = 120
    bw = {45: 1000, 32: 1000,
          22: 1000, 16: 1000}
