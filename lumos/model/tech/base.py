#!/usr/bin/env python

import abc


class TechModelError(Exception):
    pass


class BaseTechModel(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, name, variant):
        self._name = name
        self._variant = variant

    @property
    def variant(self):
        return self._variant

    @property
    def mnemonic(self):
        return '{0}-{1}'.format(self._name, self._variant)
