#!/usr/bin/env python

from .cmos import CMOSTechModel
from .tfet import TFETTechModel
from .finfet import FinFETTechModel
from .base import TechModelError


def get_model(name, variant):
    if name == 'cmos':
        return CMOSTechModel(variant)
    elif name == 'tfet':
        return TFETTechModel(variant)
    elif name == 'finfet':
        return FinFETTechModel(variant)
    else:
        raise TechModelError("Unknown model name: {0}".format(name))
