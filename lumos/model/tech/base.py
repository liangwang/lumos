#!/usr/bin/env python

import abc


class TechModelError(Exception):
    pass


class BaseTechModel(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, name, variant, _tech_model):
        self._name = name
        self._variant = variant

        self._freq_dict = _tech_model.freq_dict
        self._dynamic_power_dict = _tech_model.dynamic_power_dict
        self._static_power_dict = _tech_model.static_power_dict
        self.vnom_dict = _tech_model.vnom_dict
        self.area_scale = _tech_model.area_scale
        self.dynamic_power_scale = _tech_model.dp_scale
        self.static_power_scale = _tech_model.sp_scale
        self.fnom_scale = _tech_model.fnom_scale
        self.perf_scale = _tech_model.perf_scale

    @property
    def variant(self):
        return self._variant

    @property
    def mnemonic(self):
        return '{0}-{1}'.format(self._name, self._variant)

    def dynamic_power(self, tech, vdd_mv, **kwargs):
        try:
            vdd_scale = self._dynamic_power_dict[tech][vdd_mv] / \
                self._dynamic_power_dict[tech][self.vnom(tech)]
        except KeyError:
            raise TechModelError('No dynamic power for Vdd: {0}mV at {1}nm'.format(vdd_mv, tech))

        return vdd_scale

    def static_power(self, tech, vdd_mv, **kwargs):
        try:
            vdd_scale = self._static_power_dict[tech][vdd_mv] / \
                self._static_power_dict[tech][self.vnom(tech)]
        except KeyError:
            raise TechModelError('No static power for Vdd: {0}mV at {1}nm'.format(vdd_mv, tech))

        return vdd_scale

    def power(self, tech, vdd_mv, **kwargs):
        raise NotImplementedError()

    def freq(self, tech, vdd_mv, **kwargs):
        try:
            vdd_scale = self._freq_dict[tech][vdd_mv] / \
                self._freq_dict[tech][self.vnom(tech)]
        except KeyError:
            raise TechModelError('No freq for Vdd: {0}mV at {1}nm'.format(vdd_mv, tech))

        return vdd_scale

    def vnom(self, tech, **kwargs):
        return self.vnom_dict[tech]

    def vmin(self, tech, **kwargs):
        try:
            return self._vmin
        except AttributeError:
            try:
                self._vmin = min(self._freq_dict[tech].keys())
            except KeyError:
                raise TechModelError('No freq for tech node at {0}nm'.format(tech))
            return self._vmin

    def vmax(self, tech, **kwargs):
        try:
            return self._vmax
        except AttributeError:
            try:
                self._vmax = max(self._freq_dict[tech].keys())
            except KeyError:
                raise TechModelError('No freq for tech node at {0}nm'.format(tech))
            return self._vmax
