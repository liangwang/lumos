#!/usr/bin/env python
# encoding: utf-8

from os.path import join as joinpath
import conf.misc
import numpy
import csv
import scipy.interpolate
import math
import cPickle as pickle



SIM_RESULT_DIR=joinpath(conf.misc.homedir, 'data')

def gen_interp(ckt, ttype, tech):
    fname = joinpath(SIM_RESULT_DIR, '%s_%s_%d.data' % (ckt, ttype, tech))

    with open(fname, 'rb') as f:
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

    vdd = numpy.array(vdd_list)

    dp = numpy.array(dp_list)

    sp = numpy.array(sp_list)

    delay = numpy.array(tp_list)
    freq = numpy.reciprocal(delay)

    vdd_to_interp = vdd[::-1]
    freq_to_interp = freq[::-1]
    model = scipy.interpolate.interp1d(vdd_to_interp, freq_to_interp, kind='cubic')
    vmin = int(min(vdd_list) * 1000)
    vmax = int(max(vdd_list) * 1000)
    samples = vmax-vmin + 1
    vdd_mv_np = numpy.linspace(vmin, vmax, num=samples)
    vdd_np = numpy.array([ (float(v)/1000) for v in vdd_mv_np])
    freq_np = model(vdd_np)
    freq_dict = dict( (v, f) for (v,f) in zip(vdd_mv_np, freq_np) )
    sp_slopes = ((math.log10(sp_list[-1])-math.log10(sp_list[0])) / (vdd_list[-1]-vdd_list[0]))

    #print freq_dict
    #print sp_slopes
    ofn = joinpath(SIM_RESULT_DIR, '%s_%s_%d.pypkl' % (ckt, ttype, tech))
    with open(ofn, 'wb') as f:
        pickle.dump(freq_dict, f)
        pickle.dump(sp_slopes, f)

if __name__ == '__main__':
    for ckt in ('adder', 'inv'):
        for ttype in ('HKMGS', 'LP'):
            for tech in (45, 32, 22, 16):
                gen_interp(ckt, ttype, tech)


