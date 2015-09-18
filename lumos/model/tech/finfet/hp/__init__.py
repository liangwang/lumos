#!/usr/bin/env python

from lumos import settings
from .. import TechModelError

import logging
from lumos.settings import LUMOS_DEBUG
from lumos import BraceMessage as _bm_
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


__logger = None

if LUMOS_DEBUG and ('all' in LUMOS_DEBUG or 'finfet-hp' in LUMOS_DEBUG):
    _debug_enabled = True
else:
    _debug_enabled = False

def _debug(brace_msg):
    global __logger
    if not _debug_enabled:
        return

    if not __logger:
        __logger = logging.getLogger('finfet-hp')
        __logger.setLevel(logging.DEBUG)

    __logger.debug(brace_msg)

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
    _debug(_bm_('found model {0}', model_file))
    model_file_mtime = os.path.getmtime(model_file)

    tech = _get_tech_node(model_file)
    pickle_file = os.path.join(
        _MODEL_DIR, '{0}_{1}_{2}.p'.format(
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
