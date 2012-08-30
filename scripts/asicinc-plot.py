#!/usr/bin/env python
# encoding: utf-8

import os

series = ('01_fpga40x_varcov', '02_fpga40x_cov30', '03_fpga40x_cov50', '04_fpga40x_cov70',
'05_fpga80x_varcov', '06_fpga80x_cov30', '07_fpga80x_cov50', '08_fpga80x_cov70')

kernels = ('kernels_asic_inc.xml','kernels_asic_inc.xml','kernels_asic_inc.xml','kernels_asic_inc.xml',
'kernels_asic_inc_fpga80x.xml','kernels_asic_inc_fpga80x.xml','kernels_asic_inc_fpga80x.xml','kernels_asic_inc_fpga80x.xml')

workloads = ('workload_asic_inc.xml','workload_fpga40x_cov30.xml','workload_fpga40x_cov50.xml','workload_fpga40x_cov70.xml',
        'workload_fpga80x_varcov.xml','workload_fpga80x_cov30.xml','workload_fpga80x_cov50.xml','workload_fpga80x_cov70.xml')

ratio=range(10,90,5)

for s,k,w in zip(series, kernels, workloads):
    for r in ratio:
        cmd = 'python analyses/asicinc/asicinc.py --asic-ratio=%d --kernels=config/%s --workload=config/%s --series=%s' % (r, k, w, s)
        os.system(cmd)
