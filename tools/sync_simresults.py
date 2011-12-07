#!/usr/bin/env python
'''
Synchronize simulation results files from remote server
'''

import os
from os.path import join as joinpath
import paramiko
import sys

PREFIX = 'outputPTMBengroup'
R_DIR = '/var/home/lw2aw/simulation/ece6332'
L_DIR = '/home/lw2aw/projects/qual/model/data'
HOST = 'ivycreek.ece.virginia.edu'
PRIV_KEY_FILE=os.path.expanduser(joinpath(
    '~', '.ssh', 'id_rsa'))
HOST_KEY=os.path.expanduser(joinpath(
    '~', '.ssh', 'known_hosts'))

cktList = ('inv', 'adder', 'adder16', 'adder8', 'adder4')
techList = (45, 32, 22, 16)
ttypeList = ('HKMGS', 'LP')

ssh = paramiko.SSHClient()
ssh.load_host_keys(HOST_KEY)
try:
    ssh.connect(HOST, key_filename=PRIV_KEY_FILE)
except paramiko.BadHostKeyException:
    print "Server's host key could not be verified"
    sys.exit(1)
except paramiko.AuthenticationException:
    print "Authentication failed"
    sys.exit(1)
except paramiko.SSHException:
    print "SSH connection error"
    sys.exit(1)
except :
    raise

sftp = ssh.open_sftp()

def sync(rfname, lfname):
    if os.path.exists(lfname):
        # check to update
        l_attr = os.stat(lfname)
        r_attr = sftp.stat(rfname)
        
        if l_attr.st_mtime < r_attr.st_mtime:
            print 'File updated'
            sftp.get(rfname, lfname)
    else:
        # copy
        sftp.get(rfname, lfname)

for ttype in ttypeList:
    for ckt in cktList:
        for tech in techList:
            rfname = '%s%dnm%sTT.txt' % (PREFIX, tech, ttype)
            last_dir = '%s_%s' % (ckt, tech)

            lfname = '%s_%s_%d.data' % (ckt, ttype, tech) 

            r_fullname = joinpath(R_DIR, last_dir, rfname)
            l_fullname = joinpath(L_DIR, lfname)
            sync(r_fullname, l_fullname)

            rfname = '%s%dnm%sTT.txt' % (PREFIX, tech, ttype)
            last_dir = '%s_mc_%s' % (ckt, tech)

            lfname = '%s_%s_%d.mcdata' % (ckt, ttype, tech) 

            r_fullname = joinpath(R_DIR, last_dir, rfname)
            l_fullname = joinpath(L_DIR, lfname)
            sync(r_fullname, l_fullname)

    
