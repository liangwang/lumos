#!/usr/bin/python

import csv
import paramiko
from optparse import OptionParser
import os


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

parser = OptionParser()
parser.add_option('-f', '--file', dest='file', default='LP_nom2.txt')
parser.add_option('-d', '--dir', dest='dir', default='inv')
parser.add_option('--tech', action='store_true', default=False)
parser.add_option('--h2l', action='store_true', default=False)
parser.add_option('--ckt', default='inv')
parser.add_option('--type', default='nom')
(options, args) = parser.parse_args()

def printSingle():
    ssh = paramiko.SSHClient()
    ssh.load_host_keys(HOST_KEY)
    ssh.connect(HOST, key_filename=PRIV_KEY_FILE)
    sftp = ssh.open_sftp()

    remote_dfname = os.path.join(REMOTE_WDIR, options.dir, options.file)
    print remote_dfname
    remote_df = sftp.file(remote_dfname, "rb")
    remote_df.set_pipelined(True)

    freader = csv.reader(remote_df, delimiter='\t')

    print ''.join([''.ljust(6),'freq'.ljust(10), 'dp'.ljust(10), 'sp'.ljust(10)])
    row45 = freader.next()
    techList = (32, 22, 16)
    i=0
    for row in freader:
        techLabel='%dnm' % techList[i]
        freqLabel='%g' % (float(row45[1])/float(row[1]))
        dpLabel='%g' % (float(row[2])/float(row45[2]))
        spLabel='%g' % (float(row[3])/float(row45[3]))
        print ''.join([techLabel.ljust(6),
                       freqLabel.ljust(10),
                       dpLabel.ljust(10),
                       spLabel.ljust(10)])
        i = i + 1

def printHP2LP():
    ssh = paramiko.SSHClient()
    ssh.load_host_keys(HOST_KEY)
    ssh.connect(HOST, key_filename=PRIV_KEY_FILE)
    sftp = ssh.open_sftp()

    lpfname='LP_%s_%s.txt' % (options.ckt, options.type)
    hpfname='HP_%s_%s.txt' % (options.ckt, options.type)
    remote_dfname = os.path.join(REMOTE_WDIR, options.dir, lpfname)
    lpf = sftp.file(remote_dfname, "rb")
    lpf.set_pipelined(True)
    remote_dfname = os.path.join(REMOTE_WDIR, options.dir, hpfname)
    hpf = sftp.file(remote_dfname, "rb")
    hpf.set_pipelined(True)

    techList = (45,32, 22, 16)
    lpfreader = csv.reader(lpf, delimiter='\t')
    lpdata = {'freq': {},
              'dp': {},
              'sp': {}}
    i=0
    for row in lpfreader:
        lpdata['freq'][techList[i]] = 1/float(row[1])
        lpdata['dp'][techList[i]] = float(row[2])
        lpdata['sp'][techList[i]] = float(row[3])
        i = i + 1

    hpfreader = csv.reader(hpf, delimiter='\t')
    hpdata = {'freq': {},
              'dp': {},
              'sp': {}}
    i=0
    for row in hpfreader:
        hpdata['freq'][techList[i]] = 1/float(row[1])
        hpdata['dp'][techList[i]] = float(row[2])
        hpdata['sp'][techList[i]] = float(row[3])
        i = i + 1

    print 'Freq'
    for tech in techList:
        print '%d: %g' % (tech, 
                          lpdata['freq'][tech]/hpdata['freq'][tech])
    print 'dp'
    for tech in techList:
        print '%d: %g' % (tech, 
                          lpdata['dp'][tech]/hpdata['dp'][tech])
    print 'sp'
    for tech in techList:
        print '%d: %g' % (tech, 
                          lpdata['sp'][tech]/hpdata['sp'][tech])

if options.tech:
    printSingle()
elif options.h2l:
    printHP2LP()
