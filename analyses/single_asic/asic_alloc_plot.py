#!/usr/bin/env python

import os
import pandas as pd
import sys
sys.path.append(os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import lumos.analysis.plot as plt
df_cmos = pd.read_csv('results.cmos.large.csv')
df_cmos = df_cmos.query('f_parallel==100 & asic_perf==5')[['asic_alloc','sys_perf','asic_cov']]
# plt.line_plot(df_cmos, 'asic_alloc', 'sys_perf', 'asic_cov', xlabel='Total ASIC Allocation', lncols=3, figsize=(6,4.5), ms_list=(8,),
#               ylabel='Speedup', llabel='Kernel Coverage', ofn='asic_alloc_cmos_200_120.pdf',
#               figdir=os.path.abspath(os.path.dirname(__file__)))

df_tfet = pd.read_csv('results.tfet.large.csv')
df_tfet = df_tfet.query('f_parallel==100 & asic_perf==5')[['asic_alloc','sys_perf','asic_cov']]
# plt.line_plot(df_tfet, 'asic_alloc', 'sys_perf', 'asic_cov',ylim=(60,200), xlabel='Total ASIC Allocation', lncols=3, figsize=(6,4.5), ms_list=(8,),
#               ylabel='Speedup', llabel='Kernel Coverage', ofn='asic_alloc_tfet_200_120.pdf',
#               figdir=os.path.abspath(os.path.dirname(__file__)))

df_cmos['asic_cov'] = df_cmos['asic_cov'].apply(lambda x: '{0}-cmos'.format(x))
df_tfet['asic_cov'] = df_tfet['asic_cov'].apply(lambda x: '{0}-tfet'.format(x))

df = pd.concat([df_cmos, df_tfet])
df = df.query('asic_cov == "10-cmos" | asic_cov == "30-cmos" | asic_cov == "50-cmos" | asic_cov == "10-tfet" | asic_cov == "30-tfet" | asic_cov == "50-tfet"')
plt.line_plot(df, 'asic_alloc', 'sys_perf', 'asic_cov',ylim=(0,200), xlabel='Total ASIC Allocation', lncols=3, figsize=(7,5), ms_list=(8,),
              ylabel='Speedup', llabel='Kernel Coverage', ofn='asic_alloc_combined_200_120.pdf',
              figdir=os.path.abspath(os.path.dirname(__file__)))

#df_tfet.rename(columns=lambda x: 'tfet_{0}'.format(x), inplace=True)


df_cmos = pd.read_csv('results.cmos.pconstrained.csv')
df_cmos = df_cmos.query('f_parallel==100 & asic_perf==5')[['asic_alloc','sys_perf','asic_cov']]
# plt.line_plot(df_cmos, 'asic_alloc', 'sys_perf', 'asic_cov', ylim=(40,140), xlabel='Total ASIC Allocation', lncols=3, figsize=(6,4.5), ms_list=(8,),
#               ylabel='Speedup', llabel='Kernel Coverage', ofn='asic_alloc_cmos_200_60.pdf',
#               figdir=os.path.abspath(os.path.dirname(__file__)))

df_tfet = pd.read_csv('results.tfet.pconstrained.csv')
df_tfet = df_tfet.query('f_parallel==100 & asic_perf==5')[['asic_alloc','sys_perf','asic_cov']]
# plt.line_plot(df_tfet, 'asic_alloc', 'sys_perf', 'asic_cov', ylim=(40,140), xlabel='Total ASIC Allocation', lncols=3, figsize=(6,4.5), ms_list=(8,),
#               ylabel='Speedup', llabel='Kernel Coverage', ofn='asic_alloc_tfet_200_60.pdf',
#               figdir=os.path.abspath(os.path.dirname(__file__)))

df_cmos['asic_cov'] = df_cmos['asic_cov'].apply(lambda x: '{0}-cmos'.format(x))
df_tfet['asic_cov'] = df_tfet['asic_cov'].apply(lambda x: '{0}-tfet'.format(x))

df = pd.concat([df_cmos, df_tfet])
df = df.query('asic_cov == "10-cmos" | asic_cov == "30-cmos" | asic_cov == "50-cmos" | asic_cov == "10-tfet" | asic_cov == "30-tfet" | asic_cov == "50-tfet"')
plt.line_plot(df, 'asic_alloc', 'sys_perf', 'asic_cov',ylim=(40,140), xlabel='Total ASIC Allocation', lncols=3, figsize=(7,5), ms_list=(8,),
              ylabel='Speedup', llabel='Kernel Coverage', ofn='asic_alloc_combined_200_60.pdf',
              figdir=os.path.abspath(os.path.dirname(__file__)))

