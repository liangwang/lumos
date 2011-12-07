#!/usr/bin/env python

import csv
import numpy
import matplotlib.pyplot as plt
import os
import paramiko

ssh = paramiko.SSHClient()
ssh.load_host_keys(os.path.expanduser(os.path.join("~", ".ssh", "known_hosts")))
ssh.connect('ivycreek.ece.virginia.edu', 
            username='lw2aw', password='wl,128620')
sftp = ssh.open_sftp()
remote_dir = '/var/home/lw2aw/ECE6332/project/inv_mc'

data_prefix="outputPTMBengroup"
for (ttype,ccase) in (("LP","TT"),("HKMGS", "TT"),):
#for ttype in ("LPTT",):
    for (tech,color) in ((45,'red'),(32, 'red'), (22, 'red'), (16, 'red'),):
    #for (tech,color) in ((16,'blue'), ):
        fig = plt.figure(figsize=(14,6))
        fig.suptitle('Tech Node: %dnm, Technology Type: %s, Corner Case: %s' % (tech, ttype,ccase), size='large')
        axes_freq = fig.add_subplot(121)
        axes_power = fig.add_subplot(122)
        legends=[]
        plines = []

        dataf = '%s%dnm%s%s.txt' % (data_prefix, tech, ttype, ccase)
        remote_fname = os.path.join(remote_dir, dataf)
        remote_file = sftp.file(remote_fname, "rb")
        remote_file.set_pipelined(True)
        #reader = csv.reader(open(dataf,'rb'), delimiter='\t')
        reader = csv.reader(remote_file, delimiter='\t')
#myReader = csv.reader(open('outputPTMBengroup16nmLPTT.txt', 'rb'), delimiter='\t')

        vdd_raw = []
        tp_raw = []
        dp_raw = []
        sp_raw = []
        for row in reader:
            vdd_raw.append(float(row[0]))
            tp_raw.append(float(row[1]))
            dp_raw.append(float(row[2]))
            sp_raw.append(float(row[3]))


        vdd = numpy.array(vdd_raw)
        #tplh = numpy.array(tplh_raw)
        #tphl = numpy.array(tphl_raw)
        #tp = numpy.array(tp_raw)
        dp = numpy.array(dp_raw)
        sp = numpy.array(sp_raw)
        #energy = numpy.array(energy_raw)
        #ileak = numpy.array(ileak_raw)
        #delay = numpy.maximum(tplh, tphl)
        delay = numpy.array(tp_raw)
        freq = numpy.reciprocal(delay)
        freq_ghz = freq/1000000000
        #dp = energy*freq
        #eleak = ileak * vdd * delay * (-1)
        #sp = eleak * freq

        axes_freq.plot(vdd, freq_ghz, 'o')
        axes_power.plot(vdd, dp, 'o', vdd, sp, 'o')
        #axes_power.plot(vdd, sp)
        legends.append('%dnm' % tech)

        axes_freq.set_yscale('log')
        axes_freq.set_title('Frequency Scaling')
        axes_freq.set_xlabel('Supply Voltage (V)')
        axes_freq.set_ylabel('Frequency (GHz)')
        axes_freq.set_xlim(0.2, 1.3)
        #axes_freq.legend(axes_freq.lines, legends, 'upper left')        
        axes_freq.grid(True)

        axes_power.set_yscale('log')
        axes_power.set_title('Power Scaling')
        axes_power.set_xlabel('Supply Voltage (V)')
        axes_power.set_ylabel('Power (W)')
        axes_power.set_xlim(0.2, 1.3)
        #axes_power.legend(axes_power.lines, ['Dynamic Power', 'Leakage Power'], 'upper left')        
        axes_power.grid(True)
        fig.savefig('inv_mc_%dnm%s%s.pdf'% (tech, ttype,ccase))

sftp.close()
ssh.close()


