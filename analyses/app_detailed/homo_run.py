#!/usr/bin/env python3

import sys
import os
LUMOS_HOME=os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
sys.path.append(LUMOS_HOME)

from lumos.model.system.homo import HomoSysDetailed,SysConfigDetailed
from lumos.model.system.budget import Budget
from collections import defaultdict
import itertools

results = defaultdict(list)

l1_miss_list = ('0.005', '0.01', '0.05', '0.1')
l2_miss_list = ('0.01', '0.05', '0.1', '0.2', '0.5', '0.6')
rm_list = ('0.18', '0.2', '0.22', '0.24', '0.26', '0.28', '0.3', '0.32')
alpha_list = ('0.5', '1.0', '1.5', '2.0')
cpi_list = ('0.5', '0.6', '0.7', '0.8', '0.9', '1.0', '1.1') 
vdd_list = (500, 550, 600, 650, 700, 750, 800)
area_list = (200, 150, 100)
power_list = (120, 90, 60) 
from lumos.model.workload import load_kernels_and_apps
kernels, apps = load_kernels_and_apps('detailed_workload_syn.xml')
for area, power in itertools.product(area_list, power_list):
    sysconfig = SysConfigDetailed()
    sysconfig.budget = Budget(area=area, power=power)
    sys = HomoSysDetailed(sysconfig)
    for vdd, l1m, l2m, rm, alpha, cpi in itertools.product(vdd_list, l1_miss_list, l2_miss_list, rm_list, alpha_list, cpi_list):
        appname = 'l1m{0}_l2m{1}_rm{2}_alpha{3}_cpi{4}'.format(l1m, l2m, rm, alpha, cpi) 
        results['area'].append(area)
        results['power'].append(power)
        results['vdd'].append(vdd)
        results['l1m'].append(l1m)
        results['l2m'].append(l2m)
        results['rm'].append(rm)
        results['alpha'].append(alpha)
        results['cpi'].append(cpi)
        results['speedup'].append(sys.perf(vdd, apps[appname])/sys.core.perfnom)

import pandas as pd
df = pd.DataFrame(results)
df.to_csv('syn.csv')
