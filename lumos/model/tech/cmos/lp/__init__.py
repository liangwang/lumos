#!/usr/bin/env python

from lumos import settings
from .. import TechModelError

import logging
import os
from scipy.interpolate import interp1d as scipy_interp
import numpy as np
import pandas as pd
import glob
import re
try:
    import cPickle as pickle
except ImportError:
    import pickle

_logger = logging.getLogger('CMOS_LP')
_logger.setLevel(logging.INFO)
if settings.LUMOS_DEBUG and (
        'all' in settings.LUMOS_DEBUG or 'cmos-lp' in settings.LUMOS_DEBUG):
    _logger.setLevel(logging.DEBUG)

_MODEL_DIR = os.path.dirname(__file__)


vnom_dict = {45: 1100, 32: 1000, 22: 950, 16: 900}
area_scale = {45: 1, 32: 0.5, 22: 0.25, 16: 0.125, 10: 0.0875}
perf_scale = {45: 1, 32: 1.1, 22: 1.21, 16: 1.331}
fnom_scale = {45: 1, 32: 0.974, 22: 0.749, 16: 0.648}
dp_scale = {45: 1, 32: 0.5265, 22: 0.2285, 16: 0.1216}
sp_scale = {45: 1, 32: 1.544, 22: 3.4, 16: 7.646}

_tech_node_re = re.compile('[a-zA-Z0-9]+_[a-zA-Z0-9]+_(\d+).data')


def _get_tech_node(model_file):
    fname = os.path.basename(model_file)
    mo = _tech_node_re.search(fname)
    if mo:
        return int(mo.group(1))
    else:
        raise TechModelError('no technology node from the name of {0}'.format(model_file))

model_name = 'lp'
freq_dict = dict()
dynamic_power_dict = dict()
static_power_dict = dict()

model_files = glob.glob(os.path.join(
    _MODEL_DIR, '{0}_{1}_*.data'.format(
        settings.CMOS_SIM_CIRCUIT, model_name)))

for model_file in model_files:
    _logger.debug('found model {0}'.format(model_file))
    model_file_mtime = os.path.getmtime(model_file)

    tech = _get_tech_node(model_file)
    pickle_file = os.path.join(
        _MODEL_DIR, '{0}_{1}_{2}.p'.format(
            settings.CMOS_SIM_CIRCUIT, model_name, tech))
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
        try:
            df = pd.read_csv(model_file, index_col='vdd')
        except OSError:
            raise TechModelError('Model file {0} not found under {1}'.format(model_file, _MODEL_DIR))
        except ValueError:
            raise TechModelError('Wrong format, missing "vdd" column in {0}'.format(model_file))
        df.sort(inplace=True)

        vdd_to_interp = df.index.values
        dp_to_interp = df['dp'].values
        sp_to_interp = df['sp'].values
        freq_to_interp = (1/df['delay']).values

        vmin = int(min(df.index) * 1000)
        vmax = int(max(df.index) * 1000)
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
