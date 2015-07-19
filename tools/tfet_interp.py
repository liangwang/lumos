#!/usr/bin/env python

from lumos.model.tech import get_model
import os
from os.path import join as joinpath
import numpy as np
import csv
from scipy.interpolate import InterpolatedUnivariateSpline as IUSpline
import scipy.interpolate
import pickle
import matplotlib.pyplot as plt


ckt = 'rca32'
ttype = 'homoTFET30nm'
tech = 22
SIM_RESULT_DIR = os.path.join(os.path.dirname(__file__), ttype)

ifn = joinpath(SIM_RESULT_DIR, '%s_%s_%d.data' % (ckt, ttype, tech))

with open(ifn, 'r') as f:
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

fig = plt.figure()
axes = fig.add_subplot(111)
model = scipy.interpolate.interp1d(vdd_to_interp, freq_to_interp, kind=6)
vdd_mv_np = np.arange(vmin, vmax+1)
vdd_np = np.array([ (float(v)/1000) for v in vdd_mv_np])
freq_np = model(vdd_np)
axes.plot(vdd_np, freq_np, 'r-')
axes.plot(vdd_to_interp, freq_to_interp, 'bo')
fig.savefig('freq_interp.pdf')

fig = plt.figure()
axes = fig.add_subplot(111)
model = scipy.interpolate.interp1d(vdd_to_interp, dp_to_interp, kind=6)
vdd_mv_np = np.arange(vmin, vmax+1)
vdd_np = np.array([ (float(v)/1000) for v in vdd_mv_np])
dp_np = model(vdd_np)
axes.plot(vdd_np, dp_np, 'r-')
axes.plot(vdd_to_interp, dp_to_interp, 'bo')
fig.savefig('dp_interp.pdf')

fig = plt.figure()
axes = fig.add_subplot(111)
model = scipy.interpolate.interp1d(vdd_to_interp, sp_to_interp, kind='linear')
vdd_mv_np = np.arange(vmin, vmax+1)
vdd_np = np.array([ (float(v)/1000) for v in vdd_mv_np])
sp_np = model(vdd_np)
axes.plot(vdd_np, sp_np, 'r-')
axes.plot(vdd_to_interp, sp_to_interp, 'bo')
fig.savefig('sp_interp.pdf')
