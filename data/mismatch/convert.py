import csv
import numpy
import os

def readMCData(ckt, ttype, tech, ccase='TT'):
    """
    ckt: 'inv', 'adder'
    ttype: 'HKMGS', 'LP'
    tech: 45, 32, 22, 16
    """
    lfname = '%s_%s_%d.mcdata' % (ckt, ttype, tech)
    lfullname = os.path.join('data','raw', 'mismatch', lfname)
    file = open(lfullname, 'rb')

    freader = csv.reader(file, delimiter='\t')


    vdd_r = []
    tp_array = []
    sp_array = []

    for row in freader:
        if (freader.line_num % 100 == 1):
            tp_list = []
            sp_list = []

        tp_list.append(float(row[1]))
        sp_list.append(float(row[3]))

        if (freader.line_num % 100 == 0):
            vdd_r.append(float(row[0]))
            tp_array.append(numpy.array(tp_list))
            sp_array.append(numpy.array(sp_list))

    file.close()

    vdd = numpy.array(vdd_r)

    delay_miu = numpy.array([numpy.mean(tp_list) for tp_list in tp_array ]) 
    delay_sigma = numpy.array([numpy.std(tp_list) for tp_list in tp_array ])

    delay_max = numpy.array([max(tp_list) for tp_list in tp_array ])
    delay_mean = numpy.array([numpy.mean(tp_list) for tp_list in tp_array ])

    delay_3sigma = delay_miu + 3*delay_sigma
    delay_2sigma = delay_miu + 2*delay_sigma
    delay_sigma = delay_miu + delay_sigma


    freq_3sigma = numpy.reciprocal(delay_3sigma)
    freq_2sigma = numpy.reciprocal(delay_2sigma)
    freq_sigma = numpy.reciprocal(delay_sigma)
    freq_min = numpy.reciprocal(delay_max)
    freq_mean = numpy.reciprocal(delay_mean)

    sp_mean = numpy.array([numpy.mean(sp_list) for sp_list in sp_array ])

    ols = []
    for (v, f_3sigma, fmin, fmean, f_2sigma, f_sigma) in zip(vdd, freq_3sigma, freq_min, freq_mean, freq_2sigma, freq_sigma):
        ol = '%.2f\t%e\t%e\t%e\t%e\t%e\n' % (v, f_3sigma, fmin, fmean, f_2sigma, f_sigma)
        ols.append(ol)
    with open('outputs/%s_%s_%d.mcdata' % (ckt, ttype, tech), 'wb') as f:
        f.writelines(ols)

    return {'vdd':vdd, 'freq_3sigma': freq_3sigma,
            'freq_2sigma': freq_2sigma,
            'freq_sigma': freq_sigma,
            'freq_mean': numpy.reciprocal(delay_mean),
            'freq_min': numpy.reciprocal(delay_max),
            'freq_miu': numpy.reciprocal(delay_miu),
            'freq_std': numpy.reciprocal(delay_sigma),
            'sp_mean': sp_mean}


for ckt in ('inv', 'adder'):
    for ttype in ('HKMGS', 'LP'):
        for tech in (45, 32, 22, 16):
            readMCData(ckt, ttype, tech)
