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

_logger = logging.getLogger('FINFET_HP')
_logger.setLevel(logging.INFO)
if settings.LUMOS_DEBUG and (
        'all' in settings.LUMOS_DEBUG or 'finfet-hp' in settings.LUMOS_DEBUG):
    _logger.setLevel(logging.DEBUG)

_MODEL_DIR = os.path.dirname(__file__)


# Adopted from PTM-MG model file
vnom_dict = {20: 900, 16: 850, 14: 800, 10: 750, 7: 700}
# Caculated as (tech_length/20nm)^2
area_scale = {20: 1, 16: 0.53, 14: 0.4, 10: 0.25, 7: 0.1225}
# Calculated using RCA32 results at nominal supply
fnom_scale = {20: 1, 16: 1.5493, 14: 2.2967, 10: 2.6215, 7: 3.0719}
dp_scale = {20: 1, 16: 0.9606, 14: 0.9164, 10: 0.7731, 7: 0.6086}
sp_scale = {20: 1, 16: 0.8515, 14: 0.7015, 10: 0.6023, 7: 0.4719}
# The same as fnom_scale
perf_scale = {20: 1, 16: 1.5493, 14: 2.2967, 10: 2.6215, 7: 3.0719}

_tech_node_re = re.compile('[a-zA-Z0-9]+_[a-zA-Z0-9]+_(\d+).data')


def _get_tech_node(model_file):
    fname = os.path.basename(model_file)
    mo = _tech_node_re.search(fname)
    if mo:
        return int(mo.group(1))
    else:
        raise TechModelError('no technology node from the name of {0}'.format(model_file))

model_name = 'hp'
freq_dict = dict()
dynamic_power_dict = dict()
static_power_dict = dict()

model_files = glob.glob(os.path.join(
    _MODEL_DIR, '{0}_{1}_*.data'.format(
        settings.FINFET_SIM_CIRCUIT, model_name)))

for model_file in model_files:
    _logger.debug('found model {0}'.format(model_file))
    model_file_mtime = os.path.getmtime(model_file)

    tech = _get_tech_node(model_file)
    pickle_file = os.path.join(
        _MODEL_DIR, '{0}_{1}_{2}.pypkl'.format(
            settings.FINFET_SIM_CIRCUIT, model_name, tech))
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
        vdd_np = np.array([(float(v)/1000) for v in vdd_mv_np])

        model = scipy_interp(vdd_to_interp, freq_to_interp, kind=6)
        freq_np = model(vdd_np)
        freq_dict[tech] = dict((v, f) for (v, f) in zip(vdd_mv_np, freq_np))

        model = scipy_interp(vdd_to_interp, dp_to_interp, kind=6)
        dp_np = model(vdd_np)
        dynamic_power_dict[tech] = dict((v, dp) for (v, dp) in zip(vdd_mv_np, dp_np))

        model = scipy_interp(vdd_to_interp, sp_to_interp, kind='linear')
        sp_np = model(vdd_np)
        static_power_dict[tech] = dict((v, sp) for (v, sp) in zip(vdd_mv_np, sp_np))

        with open(pickle_file, 'wb') as f:
            pickle.dump(freq_dict[tech], f)
            pickle.dump(dynamic_power_dict[tech], f)
            pickle.dump(static_power_dict[tech], f)
