#!/usr/bin/env python

from lumos import settings
from .. import TechModelError

import logging
import os
from scipy.interpolate import interp1d as scipy_interp
import numpy as np
import csv
import glob
import re
try:
    import cPickle as pickle
except ImportError:
    import pickle

_logger = logging.getLogger('homoTFET_30nm')
_logger.setLevel(logging.INFO)
if settings.LUMOS_DEBUG and (
        'all' in settings.LUMOS_DEBUG or 'homotfet30nm' in settings.LUMOS_DEBUG):
    _logger.setLevel(logging.DEBUG)

_MODEL_DIR = os.path.dirname(__file__)


# @TODO: change scaling factors for TFET
vnom_dict = {45: 1000, 32: 900, 22: 400, 16: 350, 10: 300}
area_scale = {45: 1, 32: 0.5, 22: 0.25, 16: 0.125, 10: 0.0875}
perf_scale = {45: 1, 32: 1.1, 22: 1.21, 16: 1.331}   # FIXME: needs change
fnom_scale = {45: 1, 32: 0.95, 22: 0.7945, 16: 0.664}
dp_scale = {45: 1, 32: 0.492, 22: 0.206, 16: 0.092}
sp_scale = {45: 1, 32: 0.306, 22: 0.122, 16: 0.131}


_tech_node_re = re.compile('[a-zA-Z0-9]+_[a-zA-Z0-9]+_(\d+).data')


def _get_tech_node(model_file):
    fname = os.path.basename(model_file)
    mo = _tech_node_re.search(fname)
    if mo:
        return int(mo.group(1))
    else:
        raise TechModelError('no technology node from the name of {0}'.format(model_file))

model_name = 'homoTFET30nm'
freq_dict = dict()
dynamic_power_dict = dict()
static_power_dict = dict()

model_files = glob.glob(os.path.join(
    _MODEL_DIR, '{0}_{1}_*.data'.format(
        settings.TFET_SIM_CIRCUIT, model_name)))

for model_file in model_files:
    _logger.debug('found model {0}'.format(model_file))
    model_file_mtime = os.path.getmtime(model_file)

    tech = _get_tech_node(model_file)
    pickle_file = os.path.join(
        _MODEL_DIR, '{0}_{1}_{2}.pypkl'.format(
            settings.TFET_SIM_CIRCUIT, model_name, tech))
    try:
        pickle_file_mtime = os.path.getmtime(pickle_file)
    except OSError:
        pickle_file_mtime = 0

    if pickle_file_mtime > model_file_mtime:
        with open(pickle_file, 'rb') as f:
            freq_dict[tech] = pickle.load(f)
            dynamic_power_dict[tech] = pickle.load(f)
            static_power_dict[tech] = pickle.load(f)
    else:
        with open(model_file, 'r') as f:
            freader = csv.reader(f, delimiter='\t')

            vdd_list = []
            tp_list = []
            dp_list = []
            sp_list = []
            for row in freader:
                vdd_list.append(float(row[0]))
                tp_list.append(float(row[1]))
                dp_list.append(float(row[2]))
                sp_list.append(float(row[3]))

        vdd = np.array(vdd_list)
        vdd_to_interp = vdd[::-1]

        dp = np.array(dp_list)
        dp_to_interp = dp[::-1]

        sp = np.array(sp_list)
        sp_to_interp = sp[::-1]

        delay = np.array(tp_list)
        freq = np.reciprocal(delay)
        freq_to_interp = freq[::-1]

        vmin = int(min(vdd_list) * 1000)
        vmax = int(max(vdd_list) * 1000)
        vdd_mv_np = np.arange(vmin, vmax+1)
        vdd_np = np.array([ (float(v)/1000) for v in vdd_mv_np])

        model = scipy_interp(vdd_to_interp, freq_to_interp, kind=6)
        freq_np = model(vdd_np)
        freq_dict[tech] = dict( (v, f) for (v,f) in zip(vdd_mv_np, freq_np) )

        model = scipy_interp(vdd_to_interp, dp_to_interp, kind=6)
        dp_np = model(vdd_np)
        dynamic_power_dict[tech] = dict( (v, dp) for (v, dp) in zip(vdd_mv_np, dp_np))

        model = scipy_interp(vdd_to_interp, sp_to_interp, kind='linear')
        sp_np = model(vdd_np)
        static_power_dict[tech] = dict( (v, sp) for (v, sp) in zip(vdd_mv_np, sp_np))

        with open(pickle_file, 'wb') as f:
            pickle.dump(freq_dict[tech], f)
            pickle.dump(dynamic_power_dict[tech], f)
            pickle.dump(static_power_dict[tech], f)
