#!/usr/bin/env python

'''
Normal simulation with vdd sweeping
'''

import csv
import numpy
import os
import paramiko

DATAF_PREFIX='outputPTMBengroup'
REMOTE_WDIR='/var/home/lw2aw/simulation/ece6332'
LOCAL_WDIR='/home/lw2aw/projects/qual/model-new/data'
HOST='ivycreek.ece.virginia.edu'
PRIV_KEY_FILE=os.path.expanduser(os.path.join(
    '~', '.ssh', 'id_rsa'))
HOST_KEY=os.path.expanduser(os.path.join(
    '~', '.ssh', 'known_hosts'))
import conf.misc
USE_REMOTE=conf.misc.use_remote

def readNormData(ckt, ttype, tech, ccase='TT', use_remote=USE_REMOTE):
    """
    ckt: 'inv', 'adder'
    ttype: 'HKMGS', 'LP'
    tech: 45, 32, 22, 16
    """
    if use_remote:
        ssh = paramiko.SSHClient()
        ssh.load_host_keys(HOST_KEY)
        ssh.connect(HOST, key_filename=PRIV_KEY_FILE)
        sftp = ssh.open_sftp()

        dataf = '%s%dnm%s%s.txt' % (DATAF_PREFIX, tech, ttype, ccase)
        data_dir = '%s_%s' % (ckt, tech)

        remote_dfname = os.path.join(REMOTE_WDIR, data_dir, dataf)
        remote_df = sftp.file(remote_dfname, "rb")
        remote_df.set_pipelined(True)

        freader = csv.reader(remote_df, delimiter='\t')
    else:
        lfname = '%s_%s_%d.data' % (ckt, ttype, tech)
        lfullname = os.path.join(LOCAL_WDIR, lfname)
        file = open(lfullname, 'rb')

        freader = csv.reader(file, delimiter='\t')


    vdd_raw = []
    tp_raw = []
    dp_raw = []
    sp_raw = []
    for row in freader:
        vdd_raw.append(float(row[0]))
        tp_raw.append(float(row[1]))
        dp_raw.append(float(row[2]))
        sp_raw.append(float(row[3]))


    if use_remote:
        sftp.close()
        ssh.close()
    else:
        file.close()

    vdd = numpy.array(vdd_raw)

    dp = numpy.array(dp_raw)

    sp = numpy.array(sp_raw)

    delay = numpy.array(tp_raw)
    freq = numpy.reciprocal(delay)

    return {'vdd':vdd,'freq':freq,'dp':dp,'sp':sp}

def readMCData(ckt, ttype, tech, ccase='TT', use_remote=USE_REMOTE):
    """
    ckt: 'inv50', 'adder'
    ttype: 'HKMGS', 'LP'
    tech: 45, 32, 22, 16
    """
    if use_remote:
        ssh = paramiko.SSHClient()
        ssh.load_host_keys(HOST_KEY)
        ssh.connect(HOST, key_filename=PRIV_KEY_FILE)
        sftp = ssh.open_sftp()

        dataf = '%s%dnm%s%s.txt' % (DATAF_PREFIX, tech, ttype, ccase)
        data_dir = '%s_mc_%s' % (ckt, tech)

        remote_dfname = os.path.join(REMOTE_WDIR, data_dir, dataf)
        remote_df = sftp.file(remote_dfname, "rb")
        remote_df.set_pipelined(True)

        freader = csv.reader(remote_df, delimiter='\t')
    else:
        lfname = '%s_%s_%d.mcdata' % (ckt, ttype, tech)
        lfullname = os.path.join(LOCAL_WDIR, lfname)
        file = open(lfullname, 'rb')

        freader = csv.reader(file, delimiter='\t')


    vdd = []
    freqs_3sigma = []
    freqs_2sigma = []
    freqs_sigma = []
    freqs_min = []
    freqs_mean = []

    for row in freader:
        vdd.append(float(row[0]))
        freqs_3sigma.append(float(row[1]))
        freqs_min.append(float(row[2]))
        freqs_mean.append(float(row[3]))
        freqs_2sigma.append(float(row[4]))
        freqs_sigma.append(float(row[5]))

    file.close()

    return {'vdd':numpy.array(vdd), 
            'freq_3sigma': numpy.array(freqs_3sigma),
            'freq_2sigma': numpy.array(freqs_2sigma),
            'freq_sigma': numpy.array(freqs_sigma),
            'freqs_mean': numpy.array(freqs_mean),
            'freqs_min': numpy.array(freqs_min),}

def readMCDataold2(ckt, ttype, tech, ccase='TT', use_remote=USE_REMOTE):
    """
    ckt: 'inv', 'adder'
    ttype: 'HKMGS', 'LP'
    tech: 45, 32, 22, 16
    """
    if use_remote:
        ssh = paramiko.SSHClient()
        ssh.load_host_keys(HOST_KEY)
        ssh.connect(HOST, key_filename=PRIV_KEY_FILE)
        sftp = ssh.open_sftp()

        dataf = '%s%dnm%s%s.txt' % (DATAF_PREFIX, tech, ttype, ccase)
        data_dir = '%s_mc_%s' % (ckt, tech)

        remote_dfname = os.path.join(REMOTE_WDIR, data_dir, dataf)
        remote_df = sftp.file(remote_dfname, "rb")
        remote_df.set_pipelined(True)

        freader = csv.reader(remote_df, delimiter='\t')
    else:
        lfname = '%s_%s_%d.mcdata' % (ckt, ttype, tech)
        lfullname = os.path.join(LOCAL_WDIR, lfname)
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

    if use_remote:
        sftp.close()
        ssh.close()
    else:
        file.close()

    vdd = numpy.array(vdd_r)

    delay_miu = numpy.array([numpy.mean(tp_list) for tp_list in tp_array ]) 
    delay_sigma = numpy.array([numpy.std(tp_list) for tp_list in tp_array ])

    delay_max = numpy.array([max(tp_list) for tp_list in tp_array ])
    delay_mean = numpy.array([numpy.mean(tp_list) for tp_list in tp_array ])

    delay_3sigma = delay_miu + 3*delay_sigma


    freq_3sigma = numpy.reciprocal(delay_3sigma)

    sp_mean = numpy.array([numpy.mean(sp_list) for sp_list in sp_array ])

    return {'vdd':vdd, 'freq_3sigma': freq_3sigma,
            'freq_mean': numpy.reciprocal(delay_mean),
            'freq_min': numpy.reciprocal(delay_max),
            'freq_miu': numpy.reciprocal(delay_miu),
            'freq_std': numpy.reciprocal(delay_sigma),
            'sp_mean': sp_mean}

def readMCDataold(ckt, ttype, tech, ccase='TT', use_remote=USE_REMOTE):
    """
    ckt: 'inv', 'adder'
    ttype: 'HKMGS', 'LP'
    tech: 45, 32, 22, 16
    """
    if use_remote:
        ssh = paramiko.SSHClient()
        ssh.load_host_keys(HOST_KEY)
        ssh.connect(HOST, key_filename=PRIV_KEY_FILE)
        sftp = ssh.open_sftp()

        dataf = '%s%dnm%s%s.txt' % (DATAF_PREFIX, tech, ttype, ccase)
        data_dir = '%s_mc_%s' % (ckt, tech)

        remote_dfname = os.path.join(REMOTE_WDIR, data_dir, dataf)
        remote_df = sftp.file(remote_dfname, "rb")
        remote_df.set_pipelined(True)

        freader = csv.reader(remote_df, delimiter='\t')
    else:
        lfname = '%s_%s_%d.mcdata' % (ckt, ttype, tech)
        lfullname = os.path.join(LOCAL_WDIR, lfname)
        file = open(lfullname, 'rb')

        freader = csv.reader(file, delimiter='\t')


    vdd_r = []
    tp_max_r = []
    tp_min_r = []
    dp_max_r = []
    dp_min_r = []
    sp_max_r = []
    sp_min_r = []
    sp_mean_r = []
    dp_mean_r = []

    for row in freader:
        if (freader.line_num % 100 == 1):
            tp_max_v = 0
            tp_min_v = 100
            dp_max_v = 0
            dp_min_v = 100
            sp_max_v = 0
            sp_min_v = 100
            sp_sum = 0
            dp_sum = 0

        tp_v = float(row[1])
        if (tp_v > tp_max_v):
            tp_max_v = tp_v
        if (tp_v < tp_min_v):
            tp_min_v = tp_v

        dp_v = float(row[2])
        if (dp_v > dp_max_v):
            dp_max_v = dp_v
        if (dp_v < dp_min_v):
            dp_min_v = dp_v
        dp_sum = dp_sum + dp_v

        sp_v = float(row[3])
        if (sp_v > sp_max_v):
            sp_max_v = sp_v
        if (sp_v < sp_min_v):
            sp_min_v = sp_v
        sp_sum = sp_sum + sp_v

        if (freader.line_num % 100 == 0):
            vdd_r.append(float(row[0]))
            tp_max_r.append(tp_max_v)
            tp_min_r.append(tp_min_v)
            dp_max_r.append(dp_max_v)
            dp_min_r.append(dp_min_v)
            sp_max_r.append(sp_max_v)
            sp_min_r.append(sp_min_v)
            sp_mean_r.append(sp_sum/100)
            dp_mean_r.append(dp_sum/100)

    if use_remote:
        sftp.close()
        ssh.close()
    else:
        file.close()

    vdd = numpy.array(vdd_r)

    dp_max = numpy.array(dp_max_r)
    dp_min = numpy.array(dp_min_r)
    dp_mean = numpy.array(dp_mean_r)

    sp_max = numpy.array(sp_max_r)
    sp_min = numpy.array(sp_min_r)
    sp_mean = numpy.array(sp_mean_r)

    delay_max = numpy.array(tp_max_r)
    delay_min = numpy.array(tp_min_r)

    freq_max = numpy.reciprocal(delay_min)
    freq_min = numpy.reciprocal(delay_max)

    return {'vdd':vdd, 
            'freq_min':freq_min, 'freq_max':freq_max,
            'dp_min':dp_min, 'dp_max':dp_max, 'dp_mean':dp_mean,
            'sp_min':sp_min, 'sp_max':sp_max, 'sp_mean':sp_mean}

import xlrd
import tempfile
DEFAULT_XLS_FILE='/home/lw2aw/projects/model/data/inv_45.xls'
ROW_TITLE = 0 # row number for titles
COL_KEY = 1   # column number for master key, currently it is 1 as Vdd

def readXLS(xlsfile=DEFAULT_XLS_FILE, sheetname=u'Sheet1'):
    wbk = xlrd.open_workbook(xlsfile, logfile=tempfile.TemporaryFile())
    sht = wbk.sheet_by_name(sheetname)
    
    titles = []
    values = dict()
    for row in xrange(sht.nrows):
        if row == ROW_TITLE:
            for col in xrange(sht.ncols):
                titles.append(sht.cell_value(row, col))
            continue
        
        row_temp = []
        for col in xrange(sht.ncols):
            if col == COL_KEY:
                key = sht.cell_value(row, col)
            row_temp.append(sht.cell_value(row, col))
        values[key] = row_temp

    vdd = (v for v in sorted(values.iterkeys()))
    for title in titles:
        if 'Max Freq' in title:
            idx_freq = titles.index(title)
            break
    freq = (values[v][idx_freq] for v in values.keys())

    idx_dp = titles.index('Dynamic Power')
    dp = (values[v][idx_dp] for v in values.keys())

    idx_sp = titles.index('Leakage Power')
    sp = (values[v][idx_sp] for v in values.keys())

    return {'vdd' : vdd,
            'freq': freq,
            'dp'  : dp,
            'sp'  : sp}

if __name__ == '__main__':
    #ana = Analyzer()
    #ana.plotSingle(cktList=('adder',), ttypeList=('LP',), techList=(45,))
    #ana.plotSingle(cktList=('adder',), ttypeList=('HKMGS',), techList=(45,32))
    #ana.plotSingle(cktList=('inv','adder'), ttypeList=('HKMGS','LP'), techList=(45,32,22,16))
    mech = 'LP'
    ckt = 'adder'
    for tech in (16,):
        mcdata=readMCData(ckt,mech,tech)
        data = readNormData(ckt, mech, tech)
        #print mcdata['vdd']
        print mcdata['freq_3sigma']
        #print mcdata['freq_mean']
        print mcdata['freq_min']
        print mcdata['freq_miu']
        #print mcdata['freq_std']
        #print data['freq']
