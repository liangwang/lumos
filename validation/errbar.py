#!/usr/bin/env python

'''
Normal simulation with vdd sweeping
'''

import csv
import numpy
import matplotlib.pyplot as plt
import os
import paramiko
from data import reader

DATAF_PREFIX='outputPTMBengroup'
REMOTE_WDIR='/var/home/lw2aw/simulation/ece6332'
HOST='ivycreek.ece.virginia.edu'
PRIV_KEY_FILE=os.path.expanduser(os.path.join(
    '~', '.ssh', 'id_rsa.ivycreek'))
HOST_KEY=os.path.expanduser(os.path.join(
    '~', '.ssh', 'known_hosts'))

def readNormData(ckt, ttype, tech, ccase='TT'):
    """
    ckt: 'inv', 'adder'
    ttype: 'HKMGS', 'LP'
    tech: 45, 32, 22, 16
    """
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

    vdd_raw = []
    tp_raw = []
    dp_raw = []
    sp_raw = []
    for row in freader:
        vdd_raw.append(float(row[0]))
        tp_raw.append(float(row[1]))
        dp_raw.append(float(row[2]))
        sp_raw.append(float(row[3]))


    sftp.close()
    ssh.close()

    vdd = numpy.array(vdd_raw)

    dp = numpy.array(dp_raw)

    sp = numpy.array(sp_raw)

    delay = numpy.array(tp_raw)
    freq = numpy.reciprocal(delay)

    return {'vdd':vdd,'freq':freq,'dp':dp,'sp':sp}

def readMCData(ckt, ttype, tech, ccase='TT'):
    """
    ckt: 'inv', 'adder'
    ttype: 'HKMGS', 'LP'
    tech: 45, 32, 22, 16
    """
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

    vdd_r = []
    tp_max_r = []
    tp_min_r = []
    dp_max_r = []
    dp_min_r = []
    sp_max_r = []
    sp_min_r = []

    for row in freader:
        if (freader.line_num % 100 == 1):
            tp_max_v = 0
            tp_min_v = 100
            dp_max_v = 0
            dp_min_v = 100
            sp_max_v = 0
            sp_min_v = 100

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

        sp_v = float(row[3])
        if (sp_v > sp_max_v):
            sp_max_v = sp_v
        if (sp_v < sp_min_v):
            sp_min_v = sp_v

        if (freader.line_num % 100 == 0):
            vdd_r.append(float(row[0]))
            tp_max_r.append(tp_max_v)
            tp_min_r.append(tp_min_v)
            dp_max_r.append(dp_max_v)
            dp_min_r.append(dp_min_v)
            sp_max_r.append(sp_max_v)
            sp_min_r.append(sp_min_v)

    sftp.close()
    ssh.close()

    vdd = numpy.array(vdd_r)

    dp_max = numpy.array(dp_max_r)
    dp_min = numpy.array(dp_min_r)

    sp_max = numpy.array(sp_max_r)
    sp_min = numpy.array(sp_min_r)

    delay_max = numpy.array(tp_max_r)
    delay_min = numpy.array(tp_min_r)

    freq_max = numpy.reciprocal(delay_max)
    freq_min = numpy.reciprocal(delay_min)

    return {'vdd':vdd, 
            'freq_min':freq_min, 'freq_max':freq_max,
            'dp_min':dp_min, 'dp_max':dp_max,
            'sp_min':sp_min, 'sp_max':sp_max}

class Analyzer(object):
    def __init__(self):
        pass

    def plot(self, cktList, ttypeList, techList):
        num_of_techs = len(techList)
        colorList = ('blue', 'magenta', 'red', 'green')
        for ckt in cktList:
            for ttype in ttypeList:
                plot_idx = 0
                fig = plt.figure(figsize=(16,6*num_of_techs))
                fig.suptitle('Technology Type: %s, Corner Case: %s' % (ttype, 'TT'))
                for (tech,color) in zip(techList, colorList):
                    #self.readData(ckt=ckt,ttype=ttype,tech=tech)
                    data_norm = reader.readNormData(ckt, ttype, tech)
                    plot_idx = plot_idx + 1
                    axes_freq = fig.add_subplot(num_of_techs,2,plot_idx)
                    
                    axes_freq.plot(data_norm['vdd'], data_norm['freq'], c=color) 
                    axes_freq.set_yscale('log')
                    axes_freq.set_title('Frequency Scaling, %snm' % (tech,))
                    axes_freq.set_xlabel('Supply Voltage (V)')
                    axes_freq.set_ylabel('Frequency (GHz)')
                    axes_freq.set_xlim(0.2, 1.2)
                    axes_freq.grid(True)
                    
                    plot_idx = plot_idx + 1
                    axes_power = fig.add_subplot(num_of_techs,2,plot_idx)

                    axes_power.plot(data_norm['vdd'], data_norm['dp'], ls='solid', marker='*', c=color) 
                    axes_power.plot(data_norm['vdd'], data_norm['sp'], ls='solid', marker='s', c=color) 

                    axes_power.set_yscale('log')
                    axes_power.set_title('Power Scaling, %snm' % (tech,))
                    axes_power.set_xlabel('Supply Voltage (V)')
                    axes_power.set_ylabel('Power (W)')
                    axes_power.set_xlim(0.2, 1.2)
                    axes_power.grid(True)

                fig.savefig('noebar_%s_%s%s.pdf' % (ckt, ttype, 'TT'))

    def plotWithErrbar(self, cktList, ttypeList, techList):
        num_of_techs = len(techList)
        colorList = ('blue', 'magenta', 'red', 'green')
        for ckt in cktList:
            for ttype in ttypeList:
                plot_idx = 0
                fig = plt.figure(figsize=(16,6*num_of_techs))
                fig.suptitle('Technology Type: %s, Corner Case: %s' % (ttype, 'TT'))
                for (tech,color) in zip(techList, colorList):
                    #self.readData(ckt=ckt,ttype=ttype,tech=tech)
                    data_norm = reader.readNormData(ckt, ttype, tech)
                    data_mc = reader.readMCData(ckt, ttype, tech)
                    plot_idx = plot_idx + 1
                    axes_freq = fig.add_subplot(num_of_techs,2,plot_idx)
                    
                    yerr_max = data_mc['freq_max']-data_norm['freq']
                    yerr_min = data_norm['freq'] - data_mc['freq_min']
                    axes_freq.errorbar(data_norm['vdd'], data_norm['freq'], yerr=[yerr_min, yerr_max]) 
                    axes_freq.set_yscale('log')
                    axes_freq.set_title('Frequency Scaling, %snm' % (tech,))
                    axes_freq.set_xlabel('Supply Voltage (V)')
                    axes_freq.set_ylabel('Frequency (GHz)')
                    axes_freq.set_xlim(0.2, 1.2)
                    axes_freq.grid(True)
                    
                    plot_idx = plot_idx + 1
                    axes_power = fig.add_subplot(num_of_techs,2,plot_idx)

                    yerr_max = data_mc['dp_max']-data_norm['dp']
                    yerr_min = data_norm['dp'] - data_mc['dp_min']
                    axes_power.errorbar(data_norm['vdd'], data_norm['dp'], yerr=[yerr_min, yerr_max]) 
                    yerr_max = data_mc['sp_max']-data_norm['sp']
                    yerr_min = data_norm['sp'] - data_mc['sp_min']
                    axes_power.errorbar(data_norm['vdd'], data_norm['sp'], yerr=[yerr_min, yerr_max]) 
                    axes_power.set_yscale('log')
                    axes_power.set_title('Power Scaling, %snm' % (tech,))
                    axes_power.set_xlabel('Supply Voltage (V)')
                    axes_power.set_ylabel('Power (W)')
                    axes_power.set_xlim(0.2, 1.2)
                    axes_power.grid(True)

                fig.savefig('errbar_%s_%s%s.png' % (ckt, ttype, 'TT'))

    #def plotAll(self):
        #cktList = ('inv',)
        #ttypeList = ('HKMGS', 'LP')
        #techList = (45, 32, 22,)
        #colorList = ('blue', 'magenta', 'red', 'green')
        #num_of_techs = len(techList)
        #for ckt in cktList:
            #for ttype in ttypeList:
                #plot_idx = 0
                #fig = plt.figure(figsize=(16,6*num_of_techs))
                #fig.suptitle('Technology Type: %s, Corner Case: %s' % (ttype, 'TT'))
                #for (tech,color) in zip(techList, colorList):
                    #self.readData(ckt=ckt,ttype=ttype,tech=tech)
                    #plot_idx = plot_idx + 1
                    #axes_freq = fig.add_subplot(num_of_techs,2,plot_idx)
                    
                    #yerr_max = self.freq_max-self.freq
                    #yerr_min = self.freq - self.freq_min
                    #axes_freq.errorbar(self.vdd, self.freq, yerr=[yerr_min, yerr_max]) 
                    #axes_freq.set_yscale('log')
                    #axes_freq.set_title('Frequency Scaling, %snm' % (tech,))
                    #axes_freq.set_xlabel('Supply Voltage (V)')
                    #axes_freq.set_ylabel('Frequency (GHz)')
                    #axes_freq.set_xlim(0.2, 1.2)
                    #axes_freq.grid(True)
                    
                    #plot_idx = plot_idx + 1
                    #axes_power = fig.add_subplot(num_of_techs,2,plot_idx)

                    #yerr_max = self.dp_max-self.dp
                    #yerr_min = self.dp - self.dp_min
                    #axes_power.errorbar(self.vdd, self.dp, yerr=[yerr_min, yerr_max], marker='*', c='blue', ecolor='blue')
                    #yerr_max = self.sp_max-self.sp
                    #yerr_min = self.sp - self.sp_min
                    #axes_power.errorbar(self.vdd, self.sp, yerr=[yerr_min, yerr_max], marker='s', c='magenta', ecolor='magenta')
                    #axes_power.set_yscale('log')
                    #axes_power.set_title('Power Scaling, %snm' % (tech,))
                    #axes_power.set_xlabel('Supply Voltage (V)')
                    #axes_power.set_ylabel('Power (W)')
                    #axes_power.set_xlim(0.2, 1.2)
                    #axes_power.grid(True)

                #fig.savefig('%s_%s%s.pdf' % (ckt, ttype, 'TT'))


    ###def plotErrorbar(self):

        ####for ckt in ('inv', 'adder'):
        ###for ckt in ('inv', ):
            ###for (ttype,ccase) in (("HKMGS","TT"), ("LP","TT")):
            ####for (ttype,ccase) in (("HKMGS","TT"),):
                ###plot_idx = 0
                ###fig_freq = plt.figure(figsize=(12,9))
                ###fig_freq.suptitle('Frequency\nTechnology Type: %s, Corner Case: %s' % (ttype,ccase))
                ###fig_power = plt.figure(figsize=(12,9))
                ###fig_power.suptitle('Power\nTechnology Type: %s, Corner Case: %s' % (ttype,ccase))
                ####for (tech,color) in ((16,'blue'), (22,'red'), (32,'magenta'), (45,'green')):
                ###for (tech,color) in ((22,'red'), (32,'magenta'), (45,'green')):
                    ###plot_idx = plot_idx + 1
                    ###axes_freq = fig_freq.add_subplot(2,2,plot_idx)
                    ###axes_power = fig_power.add_subplot(2,2,plot_idx)

                    ###axes_freq.errorbar(vdd, freq_ghz, yerr=[freq_ghz_min,freq_ghz_max], c=color)
                    ###axes_power.errorbar(vdd, dp, yerr=[dp-dp_min, dp_max-dp], c=color)
                    ###axes_power.errorbar(vdd, sp, yerr=[sp-sp_min, sp_max-sp], c=color)

                    ###axes_freq.set_yscale('log')
                    ###axes_freq.set_title('%s' % (tech,))
                    ###axes_freq.set_xlabel('Supply Voltage (V)')
                    ###axes_freq.set_ylabel('Frequency (GHz)')
                    ###axes_freq.set_xlim(0.2, 1.2)
                    ###axes_freq.grid(True)

                    ###axes_power.set_yscale('log')
                    ###axes_power.set_title('%s' % (tech,))
                    ###axes_power.set_xlabel('Supply Voltage (V)')
                    ###axes_power.set_ylabel('Power (W)')
                    ###axes_power.set_xlim(0.2, 1.2)
                    ###axes_power.grid(True)

                ###fig_freq.savefig('freq_%s_%s%s.pdf'% (ckt,ttype,ccase))
                ###fig_power.savefig('power_%s_%s%s.pdf'% (ckt,ttype,ccase))

if __name__ == '__main__':
    ana = Analyzer()
    #cktList=('inv','adder','adder16','adder8')
    cktList=('testckt',)
    ttypeList=('HKMGS',)
    techList=(45,32)
    #ana.plot(cktList, ttypeList, techList)
    ana.plotWithErrbar(cktList, ttypeList, techList)
    #ana.plotSingle(cktList=('adder',), ttypeList=('LP',), techList=(45,))
    #ana.plotSingle(cktList=('adder',), ttypeList=('HKMGS',), techList=(45,32))
    #ana.plotSingle(cktList=('inv','adder'), ttypeList=('HKMGS','LP'), techList=(45,32,22,16))
    #data=readMCData('inv','LP',45)
    #print data['vdd']
    #print data['freq_min']
    #print data['freq_max']
    #print data['dp_min']
    #print data['dp_max']
    #print data['sp_min']
    #print data['sp_max']
